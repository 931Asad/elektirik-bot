from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

import database as db
from config import ADMIN_IDS
from keyboards import obj_type_kb, confirm_media_kb, objects_list_kb

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


LOCATION_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def _parse_latlon(text: str):
    try:
        lat_str, lon_str = text.replace(" ", "").split(",")
        return float(lat_str), float(lon_str)
    except Exception:
        return None


# ---------------- ADD OBJECT (TP / GTP) ----------------

class AddObject(StatesGroup):
    type = State()
    number = State()
    address = State()
    location = State()
    media = State()


@router.message(Command("add"))
async def add_object_start(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    await state.set_state(AddObject.type)
    await message.answer("Turini tanlang:", reply_markup=obj_type_kb())


@router.callback_query(AddObject.type, F.data.startswith("type:"))
async def add_object_type(callback: CallbackQuery, state: FSMContext):
    obj_type = callback.data.split(":")[1]
    await state.update_data(obj_type=obj_type)
    await state.set_state(AddObject.number)
    await callback.answer()
    await callback.message.answer(f"Tanlandi: {obj_type}\n\nEndi raqamini yozing (masalan: 123):")


@router.message(AddObject.number)
async def add_object_number(message: Message, state: FSMContext):
    await state.update_data(number=message.text.strip())
    await state.set_state(AddObject.address)
    await message.answer("Manzilini yozing (masalan: Chilonzor tumani, 4-kvartal):")


@router.message(AddObject.address)
async def add_object_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await state.set_state(AddObject.location)
    await message.answer(
        "Endi joylashuvni yuboring — pastdagi tugmani bosing yoki\n"
        "koordinatani <code>41.123, 69.456</code> shaklida yozing:",
        reply_markup=LOCATION_KB,
    )


@router.message(AddObject.location, F.location)
async def add_object_location_gps(message: Message, state: FSMContext):
    await state.update_data(lat=message.location.latitude, lon=message.location.longitude)
    await state.set_state(AddObject.media)
    await message.answer(
        "Endi rasm yoki video yuboring (bir nechtasini yuborsangiz bo'ladi, "
        "dumaloq video ham qabul qilinadi).\nTugatgach, pastdagi tugmani bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("👇", reply_markup=confirm_media_kb())


@router.message(AddObject.location, F.text)
async def add_object_location_text(message: Message, state: FSMContext):
    coords = _parse_latlon(message.text)
    if not coords:
        await message.answer("Format noto'g'ri. Masalan: 41.123, 69.456 yoki tugmani bosing.")
        return
    await state.update_data(lat=coords[0], lon=coords[1])
    await state.set_state(AddObject.media)
    await message.answer(
        "Endi rasm yoki video yuboring (bir nechtasini yuborsangiz bo'ladi, "
        "dumaloq video ham qabul qilinadi).\nTugatgach, pastdagi tugmani bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("👇", reply_markup=confirm_media_kb())


@router.message(AddObject.media, F.photo)
async def add_object_media_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    media = data.get("media", [])
    media.append({"file_id": message.photo[-1].file_id, "type": "photo"})
    await state.update_data(media=media)
    await message.answer(f"Qabul qilindi ({len(media)} ta material). Yana yuboring yoki tugmani bosing.")


@router.message(AddObject.media, F.video)
async def add_object_media_video(message: Message, state: FSMContext):
    data = await state.get_data()
    media = data.get("media", [])
    media.append({"file_id": message.video.file_id, "type": "video"})
    await state.update_data(media=media)
    await message.answer(f"Qabul qilindi ({len(media)} ta material). Yana yuboring yoki tugmani bosing.")


@router.message(AddObject.media, F.video_note)
async def add_object_media_video_note(message: Message, state: FSMContext):
    data = await state.get_data()
    media = data.get("media", [])
    media.append({"file_id": message.video_note.file_id, "type": "video_note"})
    await state.update_data(media=media)
    await message.answer(f"Qabul qilindi ({len(media)} ta material). Yana yuboring yoki tugmani bosing.")


@router.callback_query(AddObject.media, F.data == "media_done")
async def add_object_finish(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    object_id = db.add_object(
        obj_type=data["obj_type"],
        number=data["number"],
        address=data["address"],
        lat=data["lat"],
        lon=data["lon"],
        created_by=callback.from_user.id,
    )
    for item in data.get("media", []):
        db.add_media(object_id, item["file_id"], item["type"])

    await state.clear()
    await callback.answer()
    await callback.message.answer(
        f"✅ Saqlandi: {data['obj_type']} {data['number']} "
        f"({len(data.get('media', []))} ta material bilan)."
    )


# ---------------- ADD MEDIA TO EXISTING OBJECT ----------------

class AddMedia(StatesGroup):
    find = State()
    pick = State()
    media = State()


@router.message(Command("addmedia"))
async def add_media_start(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    await state.set_state(AddMedia.find)
    await message.answer("Qaysi ТП/ГТП ga rasm yoki video qo'shmoqchisiz? Raqamini yozing:")


@router.message(AddMedia.find)
async def add_media_find(message: Message, state: FSMContext):
    objects = db.find_objects(message.text.strip())
    if not objects:
        await message.answer("Topilmadi. Qaytadan raqam yozing yoki /cancel.")
        return
    if len(objects) == 1:
        await state.update_data(object_id=objects[0]["id"], media=[])
        await state.set_state(AddMedia.media)
        await message.answer(
            f"{objects[0]['obj_type']} {objects[0]['number']} tanlandi.\n"
            "Endi rasm yoki video yuboring, tugatgach tugmani bosing.",
            reply_markup=confirm_media_kb(),
        )
        return
    await state.set_state(AddMedia.pick)
    await message.answer("Bir nechta topildi, birini tanlang:", reply_markup=objects_list_kb(objects))


@router.callback_query(AddMedia.pick, F.data.startswith("obj:"))
async def add_media_pick(callback: CallbackQuery, state: FSMContext):
    object_id = int(callback.data.split(":")[1])
    await state.update_data(object_id=object_id, media=[])
    await state.set_state(AddMedia.media)
    await callback.answer()
    await callback.message.answer(
        "Tanlandi. Endi rasm yoki video yuboring, tugatgach tugmani bosing.",
        reply_markup=confirm_media_kb(),
    )


@router.message(AddMedia.media, F.photo)
async def add_media_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    media = data.get("media", [])
    media.append({"file_id": message.photo[-1].file_id, "type": "photo"})
    await state.update_data(media=media)
    await message.answer(f"Qabul qilindi ({len(media)} ta). Yana yuboring yoki tugmani bosing.")


@router.message(AddMedia.media, F.video)
async def add_media_video(message: Message, state: FSMContext):
    data = await state.get_data()
    media = data.get("media", [])
    media.append({"file_id": message.video.file_id, "type": "video"})
    await state.update_data(media=media)
    await message.answer(f"Qabul qilindi ({len(media)} ta). Yana yuboring yoki tugmani bosing.")


@router.message(AddMedia.media, F.video_note)
async def add_media_video_note(message: Message, state: FSMContext):
    data = await state.get_data()
    media = data.get("media", [])
    media.append({"file_id": message.video_note.file_id, "type": "video_note"})
    await state.update_data(media=media)
    await message.answer(f"Qabul qilindi ({len(media)} ta). Yana yuboring yoki tugmani bosing.")


@router.callback_query(AddMedia.media, F.data == "media_done")
async def add_media_finish(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    for item in data.get("media", []):
        db.add_media(data["object_id"], item["file_id"], item["type"])
    count = len(data.get("media", []))
    await state.clear()
    await callback.answer()
    await callback.message.answer(f"✅ {count} ta material qo'shildi.")


# ---------------- ISH JURNALI (work log) ----------------

class AddLog(StatesGroup):
    find = State()
    pick = State()
    note = State()


@router.message(Command("addlog"))
async def add_log_start(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    await state.set_state(AddLog.find)
    await message.answer("Qaysi ТП/ГТП uchun yozuv qo'shmoqchisiz? Raqamini yozing:")


@router.message(AddLog.find)
async def add_log_find(message: Message, state: FSMContext):
    objects = db.find_objects(message.text.strip())
    if not objects:
        await message.answer("Topilmadi. Qaytadan raqam yozing yoki /cancel.")
        return
    if len(objects) == 1:
        await state.update_data(object_id=objects[0]["id"])
        await state.set_state(AddLog.note)
        await message.answer(
            f"{objects[0]['obj_type']} {objects[0]['number']} tanlandi.\n"
            "Endi nima qilinganini yoki nima kerakligini yozing:"
        )
        return
    await state.set_state(AddLog.pick)
    await message.answer("Bir nechta topildi, birini tanlang:", reply_markup=objects_list_kb(objects))


@router.callback_query(AddLog.pick, F.data.startswith("obj:"))
async def add_log_pick(callback: CallbackQuery, state: FSMContext):
    object_id = int(callback.data.split(":")[1])
    await state.update_data(object_id=object_id)
    await state.set_state(AddLog.note)
    await callback.answer()
    await callback.message.answer("Tanlandi. Endi nima qilinganini yoki nima kerakligini yozing:")


@router.message(AddLog.note)
async def add_log_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    db.add_log(
        object_id=data["object_id"],
        note=message.text.strip(),
        author_name=message.from_user.full_name,
        created_by=message.from_user.id,
    )
    await state.clear()
    await message.answer("✅ Yozuv saqlandi.")


# ---------------- ADD LINE ----------------

class AddLine(StatesGroup):
    name = State()
    start = State()
    end = State()
    description = State()


@router.message(Command("addline"))
async def add_line_start(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    await state.set_state(AddLine.name)
    await message.answer("Liniya nomini yozing (masalan: Л-12):")


@router.message(AddLine.name)
async def add_line_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddLine.start)
    await message.answer(
        "Boshlanish nuqtasini yuboring — tugma bilan yoki <code>41.123, 69.456</code> shaklida:",
        reply_markup=LOCATION_KB,
    )


@router.message(AddLine.start, F.location)
async def add_line_start_gps(message: Message, state: FSMContext):
    await state.update_data(start_lat=message.location.latitude, start_lon=message.location.longitude)
    await state.set_state(AddLine.end)
    await message.answer("Endi oxirgi nuqtasini yuboring:", reply_markup=LOCATION_KB)


@router.message(AddLine.start, F.text)
async def add_line_start_text(message: Message, state: FSMContext):
    coords = _parse_latlon(message.text)
    if not coords:
        await message.answer("Format noto'g'ri. Masalan: 41.123, 69.456")
        return
    await state.update_data(start_lat=coords[0], start_lon=coords[1])
    await state.set_state(AddLine.end)
    await message.answer("Endi oxirgi nuqtasini yuboring:", reply_markup=LOCATION_KB)


@router.message(AddLine.end, F.location)
async def add_line_end_gps(message: Message, state: FSMContext):
    await state.update_data(end_lat=message.location.latitude, end_lon=message.location.longitude)
    await state.set_state(AddLine.description)
    await message.answer("Izoh yozing (kesimi, uzunligi va h.k.), yoki \"-\" yuboring:", reply_markup=ReplyKeyboardRemove())


@router.message(AddLine.end, F.text)
async def add_line_end_text(message: Message, state: FSMContext):
    coords = _parse_latlon(message.text)
    if not coords:
        await message.answer("Format noto'g'ri. Masalan: 41.123, 69.456")
        return
    await state.update_data(end_lat=coords[0], end_lon=coords[1])
    await state.set_state(AddLine.description)
    await message.answer("Izoh yozing (kesimi, uzunligi va h.k.), yoki \"-\" yuboring:", reply_markup=ReplyKeyboardRemove())


@router.message(AddLine.description)
async def add_line_finish(message: Message, state: FSMContext):
    description = "" if message.text.strip() == "-" else message.text.strip()
    data = await state.get_data()
    db.add_line(
        name=data["name"],
        start_lat=data["start_lat"],
        start_lon=data["start_lon"],
        end_lat=data["end_lat"],
        end_lon=data["end_lon"],
        description=description,
        created_by=message.from_user.id,
    )
    await state.clear()
    await message.answer(f"✅ Liniya saqlandi: {data['name']}")


# ---------------- USER MANAGEMENT ----------------

@router.message(Command("adduser"))
async def add_user(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(
            "Foydalanish: <code>/adduser 123456789 Ism Familiya</code>\n"
            "ID'ni bilish uchun foydalanuvchi @userinfobot ga yozishi kerak."
        )
        return
    user_id = int(parts[1])
    full_name = parts[2] if len(parts) > 2 else ""
    db.add_allowed_user(user_id, full_name)
    await message.answer(f"✅ Qo'shildi: {user_id} {full_name}")


@router.message(Command("deluser"))
async def del_user(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: <code>/deluser 123456789</code>")
        return
    db.remove_allowed_user(int(parts[1]))
    await message.answer("✅ O'chirildi.")


@router.message(Command("users"))
async def list_users(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    users = db.list_allowed_users()
    if not users:
        await message.answer("Hozircha ruxsat etilgan foydalanuvchi yo'q (adminlardan tashqari).")
        return
    text = "\n".join(f"• {u['user_id']} — {u['full_name'] or '-'}" for u in users)
    await message.answer(text)


@router.message(Command("stats"))
async def stats(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    objs, lns, users = db.stats()
    await message.answer(f"📊 ТП/ГТП: {objs}\n🔌 Liniyalar: {lns}\n👥 Foydalanuvchilar: {users}")


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    if await state.get_state() is None:
        return
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=ReplyKeyboardRemove())

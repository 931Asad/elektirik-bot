from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

import database as db
from config import ADMIN_IDS
from keyboards import obj_type_kb, confirm_photos_kb

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
    photos = State()


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
    await state.set_state(AddObject.photos)
    await message.answer(
        "Endi rasmlarni yuboring (bir nechtasini yuborsangiz bo'ladi).\n"
        "Tugatgach, pastdagi tugmani bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("👇", reply_markup=confirm_photos_kb())


@router.message(AddObject.location, F.text)
async def add_object_location_text(message: Message, state: FSMContext):
    coords = _parse_latlon(message.text)
    if not coords:
        await message.answer("Format noto'g'ri. Masalan: 41.123, 69.456 yoki tugmani bosing.")
        return
    await state.update_data(lat=coords[0], lon=coords[1])
    await state.set_state(AddObject.photos)
    await message.answer(
        "Endi rasmlarni yuboring (bir nechtasini yuborsangiz bo'ladi).\n"
        "Tugatgach, pastdagi tugmani bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("👇", reply_markup=confirm_photos_kb())


@router.message(AddObject.photos, F.photo)
async def add_object_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"Qabul qilindi ({len(photos)} ta rasm). Yana yuboring yoki tugmani bosing.")


@router.callback_query(AddObject.photos, F.data == "photos_done")
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
    for file_id in data.get("photos", []):
        db.add_photo(object_id, file_id)

    await state.clear()
    await callback.answer()
    await callback.message.answer(
        f"✅ Saqlandi: {data['obj_type']} {data['number']} "
        f"({len(data.get('photos', []))} ta rasm bilan)."
    )


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

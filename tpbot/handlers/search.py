from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

import database as db
from config import ADMIN_IDS
from keyboards import objects_list_kb, lines_list_kb
from maputils import render_line_map

router = Router()


def _access_ok(user_id: int) -> bool:
    return db.is_allowed(user_id, ADMIN_IDS)


async def _send_object_card(message: Message, obj):
    text = f"⚡ <b>{obj['obj_type']} {obj['number']}</b>\n"
    if obj["address"]:
        text += f"📍 {obj['address']}\n"

    await message.answer(text)

    if obj["lat"] is not None and obj["lon"] is not None:
        await message.answer_location(latitude=obj["lat"], longitude=obj["lon"])

    photos = db.get_photos(obj["id"])
    if photos:
        if len(photos) == 1:
            await message.answer_photo(photos[0]["file_id"])
        else:
            media = [InputMediaPhoto(media=p["file_id"]) for p in photos[:10]]
            await message.answer_media_group(media)
    else:
        await message.answer("Rasm mavjud emas.")


async def _send_line_card(message: Message, ln):
    text = f"🔌 <b>Liniya {ln['name']}</b>\n"
    if ln["description"]:
        text += f"{ln['description']}\n"
    await message.answer(text)

    photo = render_line_map(ln["start_lat"], ln["start_lon"], ln["end_lat"], ln["end_lon"])
    await message.answer_photo(photo, caption="Yashil — boshlanishi, qizil — oxiri")

    await message.answer_location(latitude=ln["start_lat"], longitude=ln["start_lon"])
    await message.answer_location(latitude=ln["end_lat"], longitude=ln["end_lon"])


@router.message(Command("start"))
async def cmd_start(message: Message):
    if not _access_ok(message.from_user.id):
        await message.answer(
            "Kechirasiz, sizda botdan foydalanish huquqi yo'q.\n"
            "Admin bilan bog'lanib, Telegram ID'ingizni bering.\n"
            f"Sizning ID'ingiz: <code>{message.from_user.id}</code>"
        )
        return
    await message.answer(
        "Salom! Bu — ТП/ГТП va liniyalar spravochnigi.\n\n"
        "• ТП yoki ГТП raqamini yuboring (masalan: <b>123</b>) — joyi va rasmlari chiqadi.\n"
        "• Liniya nomini <b>Л</b> bilan yuboring (masalan: <b>Л12</b>) — xaritada chiziladi.\n"
    )


@router.message(F.text & ~F.text.startswith("/"))
async def search_text(message: Message):
    if not _access_ok(message.from_user.id):
        await message.answer("Sizda ruxsat yo'q. Admin bilan bog'laning.")
        return

    query = message.text.strip()

    # "Л12", "л-12", "L12" -> liniya deb hisoblaymiz
    if query.upper().lstrip().startswith(("Л", "L")):
        lines = db.find_lines(query)
        if not lines:
            await message.answer("Bunday liniya topilmadi.")
            return
        if len(lines) == 1:
            await _send_line_card(message, lines[0])
        else:
            await message.answer("Bir nechta mos liniya topildi:", reply_markup=lines_list_kb(lines))
        return

    objects = db.find_objects(query)
    if not objects:
        # ehtimol liniya qidirayotgandir
        lines = db.find_lines(query)
        if lines:
            if len(lines) == 1:
                await _send_line_card(message, lines[0])
            else:
                await message.answer("Bir nechta mos liniya topildi:", reply_markup=lines_list_kb(lines))
            return
        await message.answer("Hech narsa topilmadi. Raqamni tekshirib qayta yuboring.")
        return

    if len(objects) == 1:
        await _send_object_card(message, objects[0])
    else:
        await message.answer("Bir nechta mos obyekt topildi:", reply_markup=objects_list_kb(objects))


@router.callback_query(F.data.startswith("obj:"))
async def cb_object(callback: CallbackQuery):
    object_id = int(callback.data.split(":")[1])
    obj = db.get_object(object_id)
    if not obj:
        await callback.answer("Topilmadi", show_alert=True)
        return
    await callback.answer()
    await _send_object_card(callback.message, obj)


@router.callback_query(F.data.startswith("line:"))
async def cb_line(callback: CallbackQuery):
    line_id = int(callback.data.split(":")[1])
    ln = db.get_line(line_id)
    if not ln:
        await callback.answer("Topilmadi", show_alert=True)
        return
    await callback.answer()
    await _send_line_card(callback.message, ln)

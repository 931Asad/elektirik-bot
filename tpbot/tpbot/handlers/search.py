from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMediaVideo

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

    logs = db.get_logs(obj["id"], limit=5)
    if logs:
        text += "\n🛠 <b>So'nggi ishlar:</b>\n"
        for log in logs:
            date = (log["created_at"] or "")[:16].replace("T", " ")
            author = f" — {log['author_name']}" if log["author_name"] else ""
            text += f"• {date}{author}: {log['note']}\n"

    await message.answer(text)

    if obj["lat"] is not None and obj["lon"] is not None:
        await message.answer_location(latitude=obj["lat"], longitude=obj["lon"])

    media_rows = db.get_media(obj["id"])
    if not media_rows:
        await message.answer("Rasm yoki video mavjud emas.")
        return

    # Video-xabar (dumaloq video) media-guruhga qo'shilmaydi, alohida yuboriladi
    group_items = [m for m in media_rows if m["media_type"] in ("photo", "video")][:10]
    video_notes = [m for m in media_rows if m["media_type"] == "video_note"]

    if len(group_items) == 1:
        m = group_items[0]
        if m["media_type"] == "photo":
            await message.answer_photo(m["file_id"])
        else:
            await message.answer_video(m["file_id"])
    elif group_items:
        media = [
            InputMediaPhoto(media=m["file_id"]) if m["media_type"] == "photo"
            else InputMediaVideo(media=m["file_id"])
            for m in group_items
        ]
        await message.answer_media_group(media)

    for vn in video_notes:
        await message.answer_video_note(vn["file_id"])


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
        "• ТП yoki ГТП raqamini yuboring (masalan: <b>123</b>) — joyi, rasm/videolari va "
        "so'nggi ishlar tarixi chiqadi.\n"
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

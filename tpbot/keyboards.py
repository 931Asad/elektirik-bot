from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def objects_list_kb(objects):
    kb = InlineKeyboardBuilder()
    for obj in objects:
        label = f"{obj['obj_type']} {obj['number']}"
        if obj["address"]:
            label += f" — {obj['address'][:25]}"
        kb.row(InlineKeyboardButton(text=label, callback_data=f"obj:{obj['id']}"))
    return kb.as_markup()


def lines_list_kb(lines):
    kb = InlineKeyboardBuilder()
    for ln in lines:
        kb.row(InlineKeyboardButton(text=f"Liniya {ln['name']}", callback_data=f"line:{ln['id']}"))
    return kb.as_markup()


def obj_type_kb():
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="ТП", callback_data="type:TP"),
        InlineKeyboardButton(text="ГТП", callback_data="type:GTP"),
    )
    return kb.as_markup()


def skip_kb(callback_data: str):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="O'tkazib yuborish ➡️", callback_data=callback_data))
    return kb.as_markup()


def confirm_photos_kb():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✅ Rasmlar tugadi, saqlash", callback_data="photos_done"))
    return kb.as_markup()

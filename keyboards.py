from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Chiqim qo‘shish")],
            [KeyboardButton(text="📊 Hisobot")],
            [KeyboardButton(text="❌ Oxirgi chiqimni bekor qilish")],
            [KeyboardButton(text="🔔 Eslatma")]
        ],
        resize_keyboard=True
    )

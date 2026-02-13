from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Chiqim qo‘shish")],
        [KeyboardButton(text="📊 Hisobot")],
        [KeyboardButton(text="❌ Oxirgi chiqimni bekor qilish")],
        [KeyboardButton(text="🔔 Eslatma sozlash")]
    ],
    resize_keyboard=True
)

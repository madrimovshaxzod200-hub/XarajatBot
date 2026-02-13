import asyncio
import datetime
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================= CONFIG =================
TOKEN = "7915188460:AAGtbZw5EyEwjIeSJ1OUkvCq-hvK5s0FfJw"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB_NAME = "database.db"

# ================= DATABASE =================
async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            created_at TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            category TEXT,
            date TEXT,
            time TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            usage_count INTEGER DEFAULT 1
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS reminders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            time TEXT
        )
        """)

        await db.commit()


async def add_user(user_id, username):
    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,)
        )
        user = await cur.fetchone()

        if not user:
            await db.execute(
                "INSERT INTO users VALUES (?, ?, ?)",
                (
                    user_id,
                    username,
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                )
            )
            await db.commit()


async def add_expense(user_id, amount, category):
    async with aiosqlite.connect(DB_NAME) as db:

        now = datetime.datetime.now()

        await db.execute("""
        INSERT INTO expenses(user_id, amount, category, date, time)
        VALUES(?,?,?,?,?)
        """, (
            user_id,
            amount,
            category,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M")
        ))

        # category statistikasi
        cur = await db.execute("""
        SELECT id, usage_count FROM categories
        WHERE user_id = ? AND name = ?
        """, (user_id, category))

        cat = await cur.fetchone()

        if cat:
            await db.execute("""
            UPDATE categories
            SET usage_count = usage_count + 1
            WHERE id = ?
            """, (cat[0],))
        else:
            await db.execute("""
            INSERT INTO categories(user_id, name)
            VALUES(?,?)
            """, (user_id, category))

        await db.commit()

# ================= STATES =================
class ExpenseState(StatesGroup):
    waiting_amount = State()
    waiting_category = State()


# ================= KEYBOARDS =================
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Chiqim qo‘shish")],
            [KeyboardButton(text="📊 Hisobot")],
            [KeyboardButton(text="❌ Oxirgi chiqimni bekor qilish")],
            [KeyboardButton(text="🔔 Eslatma sozlash")]
        ],
        resize_keyboard=True
    )


async def category_keyboard(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("""
        SELECT name FROM categories
        WHERE user_id = ?
        ORDER BY usage_count DESC
        """, (user_id,))

        cats = await cur.fetchall()

    buttons = [[KeyboardButton(text=c[0])] for c in cats]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )


# ================= HISOBOT FUNKSIYALARI =================
async def today_report(user_id):
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT SUM(amount) FROM expenses
        WHERE user_id = ? AND date = ?
        """, (user_id, today))

        total = await cur.fetchone()
        total = total[0] if total[0] else 0

        cur = await db.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id = ? AND date = ?
        GROUP BY category
        """, (user_id, today))

        rows = await cur.fetchall()

    text = f"📅 Bugungi jami chiqim: {total} so‘m\n\n"

    for r in rows:
        text += f"{r[0]} — {r[1]} so‘m\n"

    return text


async def month_report(user_id):
    month = datetime.datetime.now().strftime("%Y-%m")

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT SUM(amount) FROM expenses
        WHERE user_id = ? AND date LIKE ?
        """, (user_id, f"{month}%"))

        total = await cur.fetchone()
        total = total[0] if total[0] else 0

        cur = await db.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id = ? AND date LIKE ?
        GROUP BY category
        """, (user_id, f"{month}%"))

        rows = await cur.fetchall()

    text = f"📆 Oylik jami chiqim: {total} so‘m\n\n"

    for r in rows:
        text += f"{r[0]} — {r[1]} so‘m\n"

    return text


# ================= OXIRGI CHIQIMNI O‘CHIRISH =================
async def delete_last_expense(user_id):
    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT id FROM expenses
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 1
        """, (user_id,))

        row = await cur.fetchone()

        if not row:
            return False

        await db.execute("DELETE FROM expenses WHERE id = ?", (row[0],))
        await db.commit()

        return True

# ================= START =================
@dp.message(F.text == "/start")
async def start_cmd(message: Message):

    await add_user(
        message.from_user.id,
        message.from_user.username or "NoUsername"
    )

    await message.answer(
        "Salom 👋\nXarajatBotga xush kelibsiz!",
        reply_markup=main_menu()
    )


# ================= CHIQIM BOSHLASH =================
@dp.message(F.text == "➕ Chiqim qo‘shish")
async def add_expense_start(message: Message, state: FSMContext):

    await message.answer("Bugun qancha pul sarfladingiz?")
    await state.set_state(ExpenseState.waiting_amount)


# ================= SUMMA QABUL QILISH =================
@dp.message(ExpenseState.waiting_amount)
async def get_amount(message: Message, state: FSMContext):

    if not message.text.isdigit():
        await message.answer("Iltimos faqat raqam kiriting.")
        return

    await state.update_data(amount=int(message.text))

    keyboard = await category_keyboard(message.from_user.id)

    if keyboard.keyboard:
        await message.answer(
            "Pul nimaga ishlatildi?",
            reply_markup=keyboard
        )
    else:
        await message.answer("Pul nimaga ishlatildi? (nom yozing)")

    await state.set_state(ExpenseState.waiting_category)

# ================= CATEGORY QABUL QILISH =================
@dp.message(ExpenseState.waiting_category)
async def get_category(message: Message, state: FSMContext):

    data = await state.get_data()
    amount = data["amount"]
    category = message.text

# ================= HISOBOT MENYU =================
@dp.message(F.text == "📊 Hisobot")
async def report_menu(message: Message):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Bugungi hisobot")],
            [KeyboardButton(text="📆 Oylik hisobot")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

    await message.answer("Hisobot turini tanlang:", reply_markup=kb)


# ================= BUGUNGI HISOBOT =================
@dp.message(F.text == "📅 Bugungi hisobot")
async def today_rep(message: Message):

    text = await today_report(message.from_user.id)

    await message.answer(text)


# ================= OYLIK HISOBOT =================
@dp.message(F.text == "📆 Oylik hisobot")
async def month_rep(message: Message):

    text = await month_report(message.from_user.id)

    await message.answer(text)


# ================= ORQAGA =================
@dp.message(F.text == "⬅️ Orqaga")
async def back_menu(message: Message):

    await message.answer(
        "Bosh menyu",
        reply_markup=main_menu()
    )


    await add_expense(
        message.from_user.id,
        amount,
        category
    )

    await message.answer(
        "✅ Chiqim saqlandi",
        reply_markup=main_menu()
    )

    await state.clear()

# ================= OXIRGI CHIQIMNI O‘CHIRISH =================
@dp.message(F.text == "❌ Oxirgi chiqimni bekor qilish")
async def cancel_last(message: Message):

    ok = await delete_last_expense(message.from_user.id)

    if ok:
        await message.answer("✅ Oxirgi chiqim o‘chirildi")
    else:
        await message.answer("❗ O‘chirish uchun chiqim topilmadi")


# ================= ESLATMA SOZLASH =================
@dp.message(F.text == "🔔 Eslatma sozlash")
async def reminder_menu(message: Message):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Vaqt qo‘shish")],
            [KeyboardButton(text="📋 Vaqtlar ro‘yxati")],
            [KeyboardButton(text="❌ Vaqtni o‘chirish")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

    await message.answer("Eslatma menyusi:", reply_markup=kb)


class ReminderState(StatesGroup):
    waiting_time = State()


# ================= ESLATMA QO‘SHISH =================
@dp.message(F.text == "➕ Vaqt qo‘shish")
async def add_reminder_start(message: Message, state: FSMContext):

    await message.answer("Vaqt kiriting (masalan: 21:00)")
    await state.set_state(ReminderState.waiting_time)


@dp.message(ReminderState.waiting_time)
async def save_reminder(message: Message, state: FSMContext):

    time_text = message.text

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO reminders(user_id, time)
        VALUES(?,?)
        """, (message.from_user.id, time_text))
        await db.commit()

    await message.answer("✅ Eslatma qo‘shildi", reply_markup=main_menu())
    await state.clear()


# ================= ESLATMA RO‘YXATI =================
@dp.message(F.text == "📋 Vaqtlar ro‘yxati")
async def reminder_list(message: Message):

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT time FROM reminders WHERE user_id = ?
        """, (message.from_user.id,))

        rows = await cur.fetchall()

    if not rows:
        await message.answer("Eslatma yo‘q")
        return

    text = "🔔 Eslatmalar:\n\n"
    for r in rows:
        text += f"{r[0]}\n"

    await message.answer(text)

# ================= ESLATMA YUBORISH =================
async def reminder_scheduler():
    while True:

        now = datetime.datetime.now().strftime("%H:%M")

        async with aiosqlite.connect(DB_NAME) as db:

            cur = await db.execute("""
            SELECT user_id FROM reminders WHERE time = ?
            """, (now,))

            users = await cur.fetchall()

        for u in users:
            try:
                await bot.send_message(
                    u[0],
                    "🔔 Xarajatlarni yozishni unutmang!"
                )
            except:
                pass

        await asyncio.sleep(60)


# ================= BOTNI ISHGA TUSHIRISH =================
async def main():

    await create_tables()

    asyncio.create_task(reminder_scheduler())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging
import datetime
import aiosqlite

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = "8501423191:AAGUTF5qC0_iNAZZwYyKTnHryNApX_e4sf0"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB_NAME = "xarajat.db"

logging.basicConfig(level=logging.INFO)

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

# ================= USER =================

async def add_user(user_id, username):
    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute(
            "SELECT user_id FROM users WHERE user_id=?",
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

# ================= MENU =================

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Chiqim qo‘shish")],
        [KeyboardButton(text="📊 Hisobot")],
        [KeyboardButton(text="❌ Oxirgi chiqimni bekor qilish")],
        [KeyboardButton(text="🔔 Eslatma sozlash")]
    ],
    resize_keyboard=True
)

# ================= STATES =================

class ExpenseState(StatesGroup):
    amount = State()
    category = State()

# ================= START =================

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await add_user(message.from_user.id, message.from_user.username)

    await message.answer(
        "Salom 🙂\nHisibkitob ga xush kelibsiz!",
        reply_markup=main_menu
    )

# ================= CHIQIM BOSHLASH =================

@dp.message(F.text == "➕ Chiqim qo‘shish")
async def expense_start(message: types.Message, state: FSMContext):
    await message.answer("Bugun qancha pul sarfladingiz?")
    await state.set_state(ExpenseState.amount)

# ================= SUMMA QABUL QILISH =================

@dp.message(ExpenseState.amount)
async def expense_amount(message: types.Message, state: FSMContext):

    if not message.text.isdigit():
        await message.answer("❗ Iltimos faqat son kiriting")
        return

    await state.update_data(amount=int(message.text))

    # Kategoriyalarni chiqaramiz
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("""
        SELECT name FROM categories
        WHERE user_id=?
        ORDER BY usage_count DESC
        """, (message.from_user.id,))
        cats = await cur.fetchall()

    keyboard = []

    for cat in cats:
        keyboard.append([KeyboardButton(text=cat[0])])

    markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ) if keyboard else None

    await message.answer(
        "Pul nimaga ishlatildi?",
        reply_markup=markup
    )

    await state.set_state(ExpenseState.category)

# ================= CHIQIMNI SAQLASH =================

@dp.message(ExpenseState.category)
async def expense_category(message: types.Message, state: FSMContext):

    data = await state.get_data()
    amount = data["amount"]
    category = message.text

    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M")

    async with aiosqlite.connect(DB_NAME) as db:

        # Expense saqlash
        await db.execute("""
        INSERT INTO expenses (user_id, amount, category, date, time)
        VALUES (?, ?, ?, ?, ?)
        """, (
            message.from_user.id,
            amount,
            category,
            date,
            time
        ))

        # Category mavjudligini tekshiramiz
        cur = await db.execute("""
        SELECT id, usage_count FROM categories
        WHERE user_id=? AND name=?
        """, (message.from_user.id, category))

        cat = await cur.fetchone()

        if cat:
            await db.execute("""
            UPDATE categories
            SET usage_count = usage_count + 1
            WHERE id=?
            """, (cat[0],))
        else:
            await db.execute("""
            INSERT INTO categories (user_id, name)
            VALUES (?, ?)
            """, (message.from_user.id, category))

        await db.commit()

        await message.answer(
        f"✅ Chiqim saqlandi\n💰 {amount:,} so‘m — {category}",
        reply_markup=main_menu
        )

        await state.clear()

# ================= OXIRGI CHIQIMNI O‘CHIRISH =================

@dp.message(F.text == "❌ Oxirgi chiqimni bekor qilish")
async def delete_last_expense(message: types.Message):

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT id FROM expenses
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
        """, (message.from_user.id,))

        expense = await cur.fetchone()

        if not expense:
            await message.answer(
                "⚠️ Sizda hali chiqimlar mavjud emas",
                reply_markup=main_menu
            )
            return

        await db.execute(
            "DELETE FROM expenses WHERE id=?",
            (expense[0],)
        )

        await db.commit()

        await message.answer(
        "✅ Oxirgi chiqim o‘chirildi",
        reply_markup=main_menu
    )

# ================= HISOBOT MENYUSI =================

report_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Kunlik hisobot")],
        [KeyboardButton(text="📆 Oylik hisobot")],
        [KeyboardButton(text="📊 Yillik hisobot")],
        [KeyboardButton(text="⬅️ Ortga")]
    ],
    resize_keyboard=True
)


@dp.message(F.text == "📊 Hisobot")
async def report_menu_open(message: types.Message):
    await message.answer("Hisobot turini tanlang:", reply_markup=report_menu)


@dp.message(F.text == "⬅️ Ortga")
async def back_main_menu(message: types.Message):
    await message.answer("Bosh menyu", reply_markup=main_menu)


# ================= KUNLIK HISOBOT =================

@dp.message(F.text == "📅 Kunlik hisobot")
async def daily_report(message: types.Message):

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=? AND date=?
        GROUP BY category
        """, (message.from_user.id, today))

        data = await cur.fetchall()

    if not data:
        await message.answer("Bugun chiqimlar mavjud emas.")
        return

    text = "📅 Bugungi hisobot:\n\n"
    total = 0

    for cat, amount in data:
        text += f"{cat} — {amount:,} so‘m\n"
        total += amount

    text += f"\n💰 Jami: {total:,} so‘m"

    await message.answer(text)


# ================= OYLIK HISOBOT (OY RO‘YXATI) =================

@dp.message(F.text == "📆 Oylik hisobot")
async def monthly_report_menu(message: types.Message):

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT DISTINCT substr(date,1,7) AS month
        FROM expenses
        WHERE user_id=?
        ORDER BY month ASC
        """, (message.from_user.id,))

        months = await cur.fetchall()

    if not months:
        await message.answer("Sizda hali oylik ma’lumotlar yo‘q.")
        return

    keyboard = []

    for m in months:
        keyboard.append([KeyboardButton(text=m[0])])

    markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

    await message.answer("Oyni tanlang:", reply_markup=markup)

# ================= TANLANGAN OY HISOBOTI =================

@dp.message()
async def monthly_detail(message: types.Message):

    # Oy format tekshiramiz (YYYY-MM)
    if len(message.text) == 7 and message.text[4] == "-":

        month = message.text

        async with aiosqlite.connect(DB_NAME) as db:

            # Statistika
            cur = await db.execute("""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE user_id=? AND substr(date,1,7)=?
            GROUP BY category
            """, (message.from_user.id, month))

            stats = await cur.fetchall()

            # Batafsil ro‘yxat
            cur2 = await db.execute("""
            SELECT date, category, amount
            FROM expenses
            WHERE user_id=? AND substr(date,1,7)=?
            ORDER BY date ASC
            """, (message.from_user.id, month))

            details = await cur2.fetchall()

        if not stats:
            return

        text = f"📆 {month} hisoboti\n\n"
        total = 0

        for cat, amount in stats:
            text += f"{cat} — {amount:,} so‘m\n"
            total += amount

        text += f"\n💰 Jami: {total:,} so‘m\n"
        text += "\n📋 Batafsil:\n"

        for d, cat, amount in details:
            day = d[8:]
            text += f"{day}.{month[5:]} — {cat} — {amount:,}\n"

        await message.answer(text, reply_markup=report_menu)


# ================= YILLIK HISOBOT =================

@dp.message(F.text == "📊 Yillik hisobot")
async def yearly_report(message: types.Message):

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT DISTINCT substr(date,1,4) AS year
        FROM expenses
        WHERE user_id=?
        ORDER BY year ASC
        """, (message.from_user.id,))

        years = await cur.fetchall()

    if not years:
        await message.answer("Yillik ma’lumot mavjud emas.")
        return

    text = "📊 Yillik hisobot\n\n"

    async with aiosqlite.connect(DB_NAME) as db:

        for y in years:
            year = y[0]

            cur = await db.execute("""
            SELECT substr(date,6,2) AS month, SUM(amount)
            FROM expenses
            WHERE user_id=? AND substr(date,1,4)=?
            GROUP BY month
            ORDER BY month ASC
            """, (message.from_user.id, year))

            months = await cur.fetchall()

            text += f"📅 {year}\n"

            for m, amount in months:
                text += f"{m}-{year} — {amount:,} so‘m\n"

            text += "\n"

            await message.answer(text)

# ================= ESLATMA MENYUSI =================

reminder_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Eslatma qo‘shish")],
        [KeyboardButton(text="📋 Eslatmalar ro‘yxati")],
        [KeyboardButton(text="🗑 Eslatmani o‘chirish")],
        [KeyboardButton(text="⬅️ Ortga")]
    ],
    resize_keyboard=True
)


@dp.message(F.text == "🔔 Eslatma sozlash")
async def reminder_menu_open(message: types.Message):
    await message.answer("Eslatma menyusi:", reply_markup=reminder_menu)


# ================= ESLATMA QO‘SHISH =================

class ReminderState(StatesGroup):
    time = State()

@dp.message(F.text == "➕ Eslatma qo‘shish")
async def reminder_add(message: types.Message, state: FSMContext):
    await message.answer("Vaqt kiriting (HH:MM) masalan 21:00")
    await state.set_state(ReminderState.time)


@dp.message(ReminderState.time)
async def reminder_save(message: types.Message, state: FSMContext):

    time = message.text

    if len(time) != 5 or time[2] != ":":
        await message.answer("❗ Format noto‘g‘ri. Masalan 21:00")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO reminders (user_id, time)
        VALUES (?, ?)
        """, (message.from_user.id, time))

        await db.commit()

    await message.answer("✅ Eslatma qo‘shildi", reply_markup=reminder_menu)
    await state.clear()


# ================= ESLATMA RO‘YXATI =================

@dp.message(F.text == "📋 Eslatmalar ro‘yxati")
async def reminder_list(message: types.Message):

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT time FROM reminders
        WHERE user_id=?
        """, (message.from_user.id,))

        times = await cur.fetchall()

    if not times:
        await message.answer("Eslatmalar mavjud emas.")
        return

    text = "🔔 Sizning eslatmalaringiz:\n\n"

    for t in times:
        text += f"⏰ {t[0]}\n"

    await message.answer(text)


# ================= ESLATMANI O‘CHIRISH =================

@dp.message(F.text == "🗑 Eslatmani o‘chirish")
async def reminder_delete(message: types.Message):

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT id, time FROM reminders
        WHERE user_id=?
        """, (message.from_user.id,))

        data = await cur.fetchall()

    if not data:
        await message.answer("Eslatmalar mavjud emas.")
        return

    keyboard = []

    for i in data:
        keyboard.append([KeyboardButton(text=f"O‘chirish {i[1]}")])

    markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    await message.answer("Qaysi eslatmani o‘chiramiz?", reply_markup=markup)


@dp.message(F.text.startswith("O‘chirish"))
async def reminder_delete_confirm(message: types.Message):

    time = message.text.split(" ")[1]

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        DELETE FROM reminders
        WHERE user_id=? AND time=?
        """, (message.from_user.id, time))

        await db.commit()

        await message.answer("✅ Eslatma o‘chirildi", reply_markup=reminder_menu)


# ================= ESLATMA FON TEKSHIRUV =================

async def reminder_checker():

    while True:
        now = datetime.datetime.now().strftime("%H:%M")

        async with aiosqlite.connect(DB_NAME) as db:

            cur = await db.execute("""
            SELECT user_id FROM reminders
            WHERE time=?
            """, (now,))

            users = await cur.fetchall()

        for u in users:
            try:
                await bot.send_message(
                    u[0],
                    "🔔 Bugungi xarajatlaringizni yozishni unutmang 🙂"
                )
            except:
                pass

        await asyncio.sleep(60)


# ================= BOTNI ISHGA TUSHIRISH =================

async def main():
    await create_tables()

    asyncio.create_task(reminder_checker())

    await dp.start_polling(bot)


    if name == "main":
    asyncio.run(main())

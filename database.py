import aiosqlite
import datetime

DB_NAME = "database.db"


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

        if not await cur.fetchone():

            await db.execute(
                "INSERT INTO users VALUES(?,?,?)",
                (
                    user_id,
                    username,
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                )
            )

            await db.commit()


# ================= EXPENSE =================

async def add_expense(user_id, amount, category):

    now = datetime.datetime.now()

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        INSERT INTO expenses(user_id,amount,category,date,time)
        VALUES(?,?,?,?,?)
        """, (
            user_id,
            amount,
            category,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M")
        ))

        cur = await db.execute("""
        SELECT id FROM categories
        WHERE user_id=? AND name=?
        """, (user_id, category))

        if await cur.fetchone():

            await db.execute("""
            UPDATE categories
            SET usage_count = usage_count + 1
            WHERE user_id=? AND name=?
            """, (user_id, category))

        else:

            await db.execute("""
            INSERT INTO categories(user_id,name)
            VALUES(?,?)
            """, (user_id, category))

        await db.commit()


async def get_categories(user_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT name FROM categories
        WHERE user_id=?
        ORDER BY usage_count DESC
        """, (user_id,))

        return [x[0] for x in await cur.fetchall()]


async def delete_last_expense(user_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT id FROM expenses
        WHERE user_id=?
        ORDER BY id DESC LIMIT 1
        """, (user_id,))

        row = await cur.fetchone()

        if row:
            await db.execute("DELETE FROM expenses WHERE id=?", (row[0],))
            await db.commit()
            return True

        return False


# ================= REPORTS =================

async def today_report(user_id):

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=? AND date=?
        GROUP BY category
        """, (user_id, today))

        return await cur.fetchall()


async def monthly_report(user_id):

    month = datetime.datetime.now().strftime("%Y-%m")

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=? AND date LIKE ?
        GROUP BY category
        """, (user_id, f"{month}%"))

        return await cur.fetchall()


# ================= REMINDERS =================

async def add_reminder(user_id, time):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        INSERT INTO reminders(user_id,time)
        VALUES(?,?)
        """, (user_id, time))

        await db.commit()


async def get_reminders():

    async with aiosqlite.connect(DB_NAME) as db:

        cur = await db.execute("""
        SELECT user_id,time FROM reminders
        """)

        return await cur.fetchall()

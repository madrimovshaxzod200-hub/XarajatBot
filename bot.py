import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from dotenv import load_dotenv

from database import create_tables, add_user
from keyboards import menu_keyboard


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):

    await add_user(
        message.from_user.id,
        message.from_user.username
    )

    await message.answer(
        "Salom 👋\nXarajatBotga xush kelibsiz!",
        reply_markup=menu_keyboard
    )


async def main():
    await create_tables()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

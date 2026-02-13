import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import router
from database import create_tables
from scheduler import reminder_loop


async def main():

    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Router ulash
    dp.include_router(router)

    # Database yaratish
    await create_tables()

    # Reminder loop ishga tushirish
    asyncio.create_task(reminder_loop(bot))

    print("Bot ishga tushdi 🚀")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

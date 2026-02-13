import asyncio
import datetime
from database import get_reminders


async def reminder_loop(bot):

    while True:

        now = datetime.datetime.now().strftime("%H:%M")

        reminders = await get_reminders()

        for user_id, time in reminders:

            if time == now:
                await bot.send_message(
                    user_id,
                    "💸 Xarajatlarni yozishni unutmang!"
                )

        await asyncio.sleep(60)

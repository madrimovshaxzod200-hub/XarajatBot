from database import today_report, monthly_report


async def today_text(user_id):

    data = await today_report(user_id)

    if not data:
        return "Bugun xarajat yo‘q"

    text = "📅 Bugungi xarajat\n\n"

    total = 0

    for cat, amount in data:
        total += amount
        text += f"{cat} — {amount}\n"

    text += f"\nJami: {total}"

    return text


async def monthly_text(user_id):

    data = await monthly_report(user_id)

    if not data:
        return "Oylik xarajat yo‘q"

    text = "📆 Oylik hisobot\n\n"

    total = 0

    for cat, amount in data:
        total += amount
        text += f"{cat} — {amount}\n"

    text += f"\nJami: {total}"

    return text

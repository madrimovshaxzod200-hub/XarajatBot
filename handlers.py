from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from database import *
from keyboards import main_menu
from states import ExpenseState, ReminderState
from reports import today_text, monthly_text

router = Router()


@router.message(CommandStart())
async def start(msg: Message):

    await add_user(msg.from_user.id, msg.from_user.username)

    await msg.answer(
        "Xush kelibsiz 😊",
        reply_markup=main_menu()
    )


@router.message(F.text == "➕ Chiqim qo‘shish")
async def add_exp(msg: Message, state: FSMContext):

    await msg.answer("Qancha sarfladingiz?")
    await state.set_state(ExpenseState.amount)


@router.message(ExpenseState.amount)
async def amount(msg: Message, state: FSMContext):

    if not msg.text.isdigit():
        return await msg.answer("Son kiriting")

    await state.update_data(amount=int(msg.text))

    cats = await get_categories(msg.from_user.id)

    if cats:
        await msg.answer("Sababi?")
        for c in cats:
            await msg.answer(c)

    await state.set_state(ExpenseState.category)


@router.message(ExpenseState.category)
async def category(msg: Message, state: FSMContext):

    data = await state.get_data()

    await add_expense(
        msg.from_user.id,
        data["amount"],
        msg.text
    )

    await msg.answer("Saqlandi ✅", reply_markup=main_menu())
    await state.clear()


@router.message(F.text == "📊 Hisobot")
async def report(msg: Message):

    text = await today_text(msg.from_user.id)

    await msg.answer(text)


@router.message(F.text == "❌ Oxirgi chiqimni bekor qilish")
async def delete(msg: Message):

    if await delete_last_expense(msg.from_user.id):
        await msg.answer("O‘chirildi")
    else:
        await msg.answer("Chiqim yo‘q")


@router.message(F.text == "🔔 Eslatma")
async def reminder(msg: Message, state: FSMContext):

    await msg.answer("Vaqt kiriting (HH:MM)")
    await state.set_state(ReminderState.time)


@router.message(ReminderState.time)
async def set_time(msg: Message, state: FSMContext):

    await add_reminder(msg.from_user.id, msg.text)

    await msg.answer("Eslatma qo‘shildi", reply_markup=main_menu())
    await state.clear()

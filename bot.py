import asyncio
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
)
from sqlalchemy import select

from config import BOT_TOKEN
from db import init_db, get_doctors, free_slots, book, Session, Doctor, Appointment

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ─── /start ───
@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
        [InlineKeyboardButton(text="🗂 Мои записи", callback_data="my")],
    ])
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\nВыберите действие:",
        reply_markup=kb,
    )


# ─── Кнопка "Записаться" → список врачей ───
@dp.callback_query(F.data == "book")
async def show_doctors(cb: CallbackQuery):
    doctors = get_doctors()
    if not doctors:
        await cb.message.edit_text("Пока нет доступных врачей.")
        return
    buttons = [
        [InlineKeyboardButton(
            text=f"{d.full_name} — {d.specialization}",
            callback_data=f"doc:{d.id}",
        )]
        for d in doctors
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    await cb.message.edit_text(
        "Выберите врача:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


# ─── Выбрали врача → показываем слоты ───
@dp.callback_query(F.data.startswith("doc:"))
async def show_slots(cb: CallbackQuery):
    doctor_id = int(cb.data.split(":")[1])
    slots = free_slots(doctor_id)
    if not slots:
        await cb.answer("Свободных слотов нет", show_alert=True)
        return
    buttons = [
        [InlineKeyboardButton(
            text=s.strftime("%d.%m %H:%M"),
            callback_data=f"slot:{doctor_id}:{int(s.timestamp())}",
        )]
        for s in slots[:20]
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="book")])
    await cb.message.edit_text(
        "Выберите время:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


# ─── Выбрали слот → записываем ───
@dp.callback_query(F.data.startswith("slot:"))
async def confirm_slot(cb: CallbackQuery):
    _, doctor_id, ts = cb.data.split(":")
    slot = datetime.fromtimestamp(int(ts), tz=timezone.utc)
    ok = book(int(doctor_id), cb.from_user.id, slot)
    if not ok:
        await cb.answer("Этот слот только что заняли 😔", show_alert=True)
        return
    await cb.message.edit_text(
        f"✅ Вы записаны на {slot.strftime('%d.%m.%Y %H:%M')} UTC"
    )


# ─── "Мои записи" ───
@dp.callback_query(F.data == "my")
async def my_appointments(cb: CallbackQuery):
    now = datetime.now(timezone.utc)
    with Session() as s:
        rows = s.execute(
            select(Appointment, Doctor)
            .join(Doctor, Appointment.doctor_id == Doctor.id)
            .where(Appointment.user_id == cb.from_user.id,
                   Appointment.slot >= now)
            .order_by(Appointment.slot)
        ).all()
    if not rows:
        await cb.message.edit_text("У вас нет активных записей.")
        return
    text = "Ваши записи:\n\n" + "\n".join(
        f"• {appt.slot.strftime('%d.%m %H:%M')} — {doc.full_name}"
        for appt, doc in rows
    )
    await cb.message.edit_text(text)


# ─── Кнопка "Назад" → главное меню ───
@dp.callback_query(F.data == "back")
async def back_to_menu(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
        [InlineKeyboardButton(text="🗂 Мои записи", callback_data="my")],
    ])
    await cb.message.edit_text("Выберите действие:", reply_markup=kb)


# ─── Запуск ───
async def main():
    init_db()
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.faq_handler import send_single_message
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("calculator"))
async def start_calculator(message: types.Message):
    """🧮 Запуск калькулятора бюджета"""
    
    logger.info(f"🧮 /calculator от пользователя {message.from_user.id}")
    
    text = """
🧮 <b>Калькулятор стоимости обучения</b>

💰 <b>Стоимость года:</b>
• Бакалавриат (очная): 135 000 - 153 300 ₽
• Специалитет: 153 300 ₽
• Заочная форма: 55 000 ₽

<b>Выберите стоимость:</b>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 153 300 ₽ (ИиВТ)", callback_data="cost_153300")],
        [InlineKeyboardButton(text="💰 135 000 ₽ (Матфак)", callback_data="cost_135000")],
        [InlineKeyboardButton(text="💰 55 000 ₽ (Заочка)", callback_data="cost_55000")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="main_menu")]
    ])
    
    await send_single_message(message, text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("cost_"))
async def select_cost(callback: types.CallbackQuery):
    """Выбор стоимости"""
    
    cost = int(callback.data.split("_")[1])
    logger.info(f"💰 Выбрана стоимость: {cost} ₽")
    
    text = f"""
✅ <b>Выбрано:</b> {cost:,} ₽/год

📅 <b>Сколько лет обучаться?</b>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 4 года (Бакалавриат)", callback_data=f"years_{cost}_4")],
        [InlineKeyboardButton(text="📚 5 лет (Специалитет)", callback_data=f"years_{cost}_5")],
        [InlineKeyboardButton(text="📚 2 года (Магистратура)", callback_data=f"years_{cost}_2")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="calculator")]
    ])
    
    await send_single_message(callback, text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("years_"))
async def calculate_result(callback: types.CallbackQuery):
    """Расчёт стоимости"""
    
    parts = callback.data.split("_")
    cost = int(parts[1])
    years = int(parts[2])
    
    total_cost = cost * years
    scholarship = 4500 * 10 * years
    final_cost = total_cost - scholarship
    
    logger.info(f"📊 Расчёт: {cost} ₽ × {years} лет = {final_cost:,} ₽")
    
    text = f"""
🧮 <b>Расчёт стоимости обучения</b>

💰 <b>Стоимость года:</b> {cost:,} ₽
📅 <b>Срок обучения:</b> {years} лет(а)

💵 <b>Общая стоимость:</b> {total_cost:,} ₽

🎓 <b>Стипендия (отличник):</b>
• В месяц: 4 500 ₽
• За {years} года: {scholarship:,} ₽

💡 <b>Итого с учётом стипендии:</b>
<b>{final_cost:,} ₽</b>

<i>📌 Не включая расходы на проживание!</i>
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Посчитать ещё раз", callback_data="calculator")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="main_menu")]
    ])
    
    await send_single_message(callback, text, reply_markup=keyboard)
    await callback.answer()

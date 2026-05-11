from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.faq_handler import send_single_message
import logging

logger = logging.getLogger(__name__)
router = Router()

# 🔥 ID ВОЛОНТЁРОВ (замени на реальные ID)
VOLUNTEER_IDS = [1057899073]  # Твой ID или ID волонтёров

@router.message(Command("quick_help"))
async def quick_help_command(message: types.Message):
    """📞 БЫСТРАЯ СВЯЗЬ С ВОЛОНТЁРОМ"""
    
    text = (
        "📞 <b>Быстрая связь с волонтёром-студентом</b>\n\n"
        
        "💬 <b>Напиши свой вопрос:</b>\n"
        "• По каким предметам ЕГЭ?\n"
        "• Какое направление интересует?\n"
        "• Что именно хочешь узнать?\n\n"
        
        "⏱️ <b>Ответим в течение 15 минут!</b>\n"
        "🕐 Рабочее время: 10:00-18:00\n\n"
        
        "👇 <b>Отправь сообщение или выбери:</b>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать волонтёру", callback_data="help_volunteer")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="main_menu")]
    ])
    
    await send_single_message(message, text, reply_markup=keyboard)

@router.callback_query(F.data == "help_volunteer")
async def help_volunteer(callback: types.CallbackQuery):
    """💬 СВЯЗЬ С ВОЛОНТЁРОМ"""
    
    text = (
        "💬 <b>Чат с волонтёром-студентом</b>\n\n"
        
        "📝 <b>Опиши свой вопрос:</b>\n"
        "• По каким предметам ЕГЭ?\n"
        "• Какое направление интересует?\n"
        "• Что именно хочешь узнать?\n\n"
        
        "⏱️ <b>Ответим в течение 15 минут!</b>\n\n"
        
        "🔙 <b>Отмена:</b> /start"
    )
    
    await send_single_message(callback, text)
    await callback.answer()
    
    # 🔥 УСТАНАВЛИВАЕМ ФЛАГ "ЖДЁМ ВОПРОС"
    from handlers.faq_handler import user_last_message
    user_last_message[callback.from_user.id] = {
        "mode": "waiting_volunteer_question",
        "message_id": callback.message.message_id
    }

# 🔥 ОБРАБОТКА СООБЩЕНИЙ ДЛЯ ВОЛОНТЁРА
@router.message(lambda msg: msg.text)
async def process_help_message(message: types.Message):
    """📞 Обработка вопросов для волонтёра"""
    
    from handlers.faq_handler import user_last_message
    
    user_data = user_last_message.get(message.from_user.id, {})
    mode = user_data.get("mode", "")
    
    if mode == "waiting_volunteer_question":
        # 🔥 ОТПРАВЛЯЕМ ВОЛОНТЁРУ
        for vol_id in VOLUNTEER_IDS:
            try:
                await message.bot.send_message(
                    vol_id,
                    f"📩 <b>Новый вопрос от @{message.from_user.username or message.from_user.first_name}</b>\n\n"
                    f"👤 ID: {message.from_user.id}\n"
                    f"💬 Вопрос:\n{message.text}\n\n"
                    f"🔗 <b>Ответить:</b> напиши этому пользователю напрямую"
                )
            except Exception as e:
                logger.error(f"❌ Не удалось отправить волонтёру: {e}")
        
        await message.answer(
            "✅ <b>Вопрос отправлен волонтёру!</b>\n\n"
            "⏱️ Ответим в течение 15 минут.\n"
            "Следи за уведомлениями!\n\n"
            "🔙 <b>В меню:</b> /start"
        )
        
        # 🔥 СБРАСЫВАЕМ РЕЖИМ
        user_last_message[message.from_user.id] = {}

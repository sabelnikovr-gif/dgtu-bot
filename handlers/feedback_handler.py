from aiogram import Router, types
from aiogram.filters import Command
from services.cache_service import cache
from handlers.keyboards import get_feedback_keyboard, get_feedback_reason_keyboard, get_main_keyboard
from datetime import datetime
import logging

router = Router()
logger = logging.getLogger(__name__)

feedback_pending = {}

@router.callback_query(lambda c: c.data == "feedback_good")
async def handle_feedback_good(callback: types.CallbackQuery):
    """👍 Обработка положительного отзыва"""
    user_id = callback.from_user.id
    
    feedback_data = {
        'user_id': user_id,
        'rating': 5,
        'timestamp': datetime.now().isoformat(),
        'question': 'unknown'
    }
    
    await cache.set(f"feedback:{user_id}:{datetime.now().timestamp()}", feedback_data)
    await cache.increment_user_count(f"feedback_good:{user_id}")
    
    await callback.answer("Спасибо за отзыв! 💙", show_alert=False)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    logger.info(f"👍 Положительный отзыв от пользователя {user_id}")

@router.callback_query(lambda c: c.data == "feedback_bad")
async def handle_feedback_bad(callback: types.CallbackQuery):
    """👎 Обработка отрицательного отзыва"""
    user_id = callback.from_user.id
    
    feedback_data = {
        'user_id': user_id,
        'rating': 1,
        'timestamp': datetime.now().isoformat(),
        'question': 'unknown'
    }
    
    await cache.set(f"feedback:{user_id}:{datetime.now().timestamp()}", feedback_data)
    await cache.increment_user_count(f"feedback_bad:{user_id}")
    
    feedback_pending[user_id] = True
    
    await callback.answer("Помоги нам стать лучше!", show_alert=False)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=get_feedback_reason_keyboard())
    except:
        await callback.message.answer(
            "❓ Что именно не понравилось?",
            reply_markup=get_feedback_reason_keyboard()
        )
    
    logger.info(f"👎 Отрицательный отзыв от пользователя {user_id}")

@router.callback_query(lambda c: c.data.startswith("feedback_reason_"))
async def handle_feedback_reason(callback: types.CallbackQuery):
    """❓ Обработка уточнения причины"""
    user_id = callback.from_user.id
    reason = callback.data.replace("feedback_reason_", "")
    
    reason_text = {
        'no_info': 'Нет информации',
        'wrong': 'Неправильный ответ',
        'old': 'Устаревшие данные',
        'other': 'Другое'
    }.get(reason, reason)
    
    await cache.set(f"feedback_reason:{user_id}:{datetime.now().timestamp()}", reason_text)
    
    if user_id in feedback_pending:
        del feedback_pending[user_id]
    
    await callback.answer(f"Спасибо! Причина: {reason_text}", show_alert=False)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    logger.info(f"📝 Причина отзыва от {user_id}: {reason_text}")

@router.callback_query(lambda c: c.data == "feedback_cancel")
async def handle_feedback_cancel(callback: types.CallbackQuery):
    """🔙 Отмена отзыва"""
    user_id = callback.from_user.id
    
    if user_id in feedback_pending:
        del feedback_pending[user_id]
    
    await callback.answer("Отменено", show_alert=False)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

@router.message(Command("feedback_stats"))
async def feedback_stats(message: types.Message):
    """📊 Статистика отзывов (ТОЛЬКО ДЛЯ ТЕБЯ - АДМИНА)"""
    
    ADMIN_ID = 1057899073  # Твой ID: @sabelnikovr
    
    # Проверка на админа
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён", reply_markup=get_main_keyboard())
        return
    
    # Считаем отзывы
    good_count = 0
    bad_count = 0
    reasons = {}
    
    for key in cache.cache.keys():
        if key.startswith("feedback:"):
            data = cache.cache[key]['value']
            if isinstance(data, dict) and 'rating' in data:  # ✅ ИСПРАВЛЕНО!
                if data['rating'] == 5:
                    good_count += 1
                elif data['rating'] == 1:
                    bad_count += 1
        elif key.startswith("feedback_reason:"):
            reason = cache.cache[key]['value']
            reasons[reason] = reasons.get(reason, 0) + 1
    
    total = good_count + bad_count
    good_percent = f"{(good_count / total * 100):.1f}" if total > 0 else "0.0"
    
    top_reasons = "\n".join(
        f"• {reason}: {count} раз" 
        for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]
    ) or "• Пока нет данных"
    
    bot_stats = cache.get_full_stats()
    
    text = (
        f"📊 <b>СТАТИСТИКА ОБРАТНОЙ СВЯЗИ</b>\n\n"
        f"👍 Полезно: <b>{good_count}</b> ({good_percent}%)\n"
        f"👎 Не помогло: <b>{bad_count}</b>\n"
        f"📈 Всего отзывов: <b>{total}</b>\n\n"
        f"❌ <b>Частые причины негатива:</b>\n"
        f"{top_reasons}\n\n"
        f"📈 <b>Общая статистика бота:</b>\n"
        f"• Пользователей: {bot_stats['total_users']}\n"
        f"• Сообщений: {bot_stats['total_messages']}\n"
        f"• Кеш: {bot_stats['hit_rate']} попаданий\n"
        f"• Экономия токенов: ~{bot_stats['hits'] * 300:,}\n\n"
        f"<i>🔄 Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>"
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

"""
🔧 Admin Commands for DGTU Bot
===============================
Команды для администратора: /stats, /users, /news, /reload_kb, /test_search
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.database import DatabaseService
from services.rag_service import rag_service
from models.database import db
from handlers.utils import get_back_keyboard, user_last_message
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

router = Router()

# ============================================================================
# 🔥 АДМИН ID
# ============================================================================

ADMIN_ID = 1057899073  # Твой ID

async def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id == ADMIN_ID

async def admin_only(message: types.Message):
    """Отправка сообщения о недоступности"""
    await message.answer(
        "⛔ <b>Доступ только для администратора</b>",
        reply_markup=get_back_keyboard()
    )

# ============================================================================
# 🔥 СТАТИСТИКА БОТА — ОБНОВЛЁННАЯ С МЕТРИКАМИ ПОИСКА
# ============================================================================

@router.message(Command("stats"))
async def show_stats(message: types.Message):
    """📊 Показать статистику бота — ОБНОВЛЁННАЯ"""
    
    if not await is_admin(message.from_user.id):
        return await admin_only(message)
    
    try:
        stats = await DatabaseService.get_stats()
        feedback = stats.get('feedback', {})
        
        positive = feedback.get('👍', 0)
        negative = feedback.get('👎', 0)
        total_feedback = positive + negative
        satisfaction = (positive / total_feedback * 100) if total_feedback > 0 else 0
        
        # 🔥 Получаем данные из БД
        users_count = await db.get_user_count() if hasattr(db, 'get_user_count') else stats.get('users', 0)
        messages_count = await db.get_message_count() if hasattr(db, 'get_message_count') else stats.get('messages', 0)
        
        # 🔥 НОВОЕ: Статистика поиска
        search_stats = {}
        if hasattr(db, 'get_search_stats'):
            search_stats = await db.get_search_stats()
        
        text = (
            f"📊 <b>Статистика бота ИиВТ ДГТУ</b>\n\n"
            f"👥 <b>Пользователи:</b> {users_count}\n"
            f"💬 <b>Сообщений обработано:</b> {messages_count}\n\n"
        )
        
        # 🔥 Блок поиска (если есть данные)
        if search_stats:
            text += (
                f"🔍 <b>Поиск:</b>\n"
                f"• Запросов всего: {search_stats.get('total_queries', 0)}\n"
                f"• Попаданий в кэш: {search_stats.get('cache_rate', 0)}%\n"
            )
            
            # Топ запросов
            top_queries = search_stats.get('top_queries', [])
            if top_queries:
                text += "• Топ-5 вопросов:\n"
                for i, item in enumerate(top_queries[:5], 1):
                    query = item.get('query', 'N/A')[:40]
                    count = item.get('count', 0)
                    text += f"  {i}. \"{query}\" ({count} раз)\n"
            text += "\n"
        
        text += (
            f"👍 <b>Отзывы:</b>\n"
            f"• Положительные: {positive}\n"
            f"• Отрицательные: {negative}\n"
            f"• Удовлетворённость: {satisfaction:.1f}%\n\n"
            f"📅 <b>Дата:</b> {message.date.strftime('%d.%m.%Y %H:%M')}"
        )
        
        await message.answer(text, reply_markup=get_back_keyboard())
        
    except Exception as e:
        logger.error(f"❌ Ошибка /stats: {e}")
        await message.answer(f"⚠️ <b>Ошибка:</b> {e}", reply_markup=get_back_keyboard())

# ============================================================================
# 🔥 СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================

@router.message(Command("users"))
async def show_users(message: types.Message):
    """👥 Показать список пользователей"""
    
    if not await is_admin(message.from_user.id):
        return await admin_only(message)
    
    try:
        users = await db.get_all_users()
        
        if not users:
            await message.answer("👥 <b>Пользователей пока нет</b>", reply_markup=get_back_keyboard())
            return
        
        text = f"👥 <b>Пользователи ({len(users)}):</b>\n\n"
        for i, user in enumerate(users[:50], 1):
            user_id = user.get('user_id') if isinstance(user, dict) else user
            text += f"{i}. <code>{user_id}</code>\n"
        
        if len(users) > 50:
            text += f"\n<i>... и ещё {len(users) - 50}</i>"
        
        await message.answer(text, reply_markup=get_back_keyboard())
        
    except Exception as e:
        logger.error(f"❌ Ошибка /users: {e}")
        await message.answer(f"⚠️ <b>Ошибка:</b> {e}", reply_markup=get_back_keyboard())

# ============================================================================
# 🔥 НОВОЕ: /reload_kb — ПЕРЕЗАГРУЗКА БАЗЫ ЗНАНИЙ
# ============================================================================

@router.message(Command("reload_kb"))
async def cmd_reload_kb(message: types.Message):
    """🔄 Перезагрузка базы знаний без перезапуска бота"""
    
    if not await is_admin(message.from_user.id):
        return await admin_only(message)
    
    try:
        import time
        start_time = time.time()
        
        # Перезагружаем базу знаний
        success = rag_service.reload_knowledge_base()
        
        elapsed = round(time.time() - start_time, 2)
        
        if success:
            kb_stats = rag_service.get_stats()
            text = (
                f"✅ <b>База знаний перезагружена!</b>\n\n"
                f"📚 <b>Разделов:</b> {kb_stats.get('total_sections', 0)}\n"
                f"📄 <b>Программ:</b> {kb_stats.get('programs_count', 0)}\n"
                f"❓ <b>Вопросов:</b> {kb_stats.get('faq_count', 0)}\n"
                f"⏱️ <b>Время:</b> {elapsed} сек"
            )
        else:
            text = "❌ <b>Ошибка перезагрузки базы знаний!</b>\nПроверь логи."
        
        await message.answer(text, reply_markup=get_back_keyboard())
        logger.info(f"🔄 База знаний перезапущена админом {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка /reload_kb: {e}")
        await message.answer(f"⚠️ <b>Ошибка:</b> {e}", reply_markup=get_back_keyboard())

# ============================================================================
# 🔥 НОВОЕ: /test_search — ТЕСТ ПОИСКА (DEBUG)
# ============================================================================

@router.message(Command("test_search"))
async def cmd_test_search(message: types.Message):
    """🧪 Тестирование поиска (debug режим)"""
    
    if not await is_admin(message.from_user.id):
        return await admin_only(message)
    
    # Парсим запрос после команды
    query = message.text.replace("/test_search", "").strip()
    
    if not query:
        await message.answer(
            "🧪 <b>Использование:</b>\n"
            "<code>/test_search твой вопрос</code>\n\n"
            "Пример: <code>/test_search какой проходной балл на ии</code>",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        return
    
    try:
        # Вызываем поиск в debug режиме
        result = await rag_service.find_relevant_context(
            question=query,
            debug=True,
            user_id=message.from_user.id
        )
        
        # Форматируем отчёт
        text = (
            f"🧪 <b>Тест поиска:</b> <i>{query[:100]}</i>\n\n"
            f"🎯 <b>Определена категория:</b> {result.get('category') or 'не определена'}\n"
            f"🔑 <b>Найдено ключевых слов:</b> {len(result.get('keywords', []))}\n"
        )
        
        if result.get('keywords'):
            text += f"   {', '.join(result['keywords'][:5])}\n"
        
        text += (
            f"\n📚 <b>Найден контекст ({result.get('parts', 0)} частей):</b>\n"
            f"✅ Итоговый контекст: {len(result.get('context', ''))} символов\n"
            f"🗄️ <b>Кэш:</b> {'✅ Попадание' if result.get('cache_hit') else '❌ Мимо'}\n"
            f"🔑 <b>Ключ кэша:</b> <code>{result.get('cache_key', 'N/A')}</code>\n\n"
        )
        
        # Показываем первые 500 символов контекста
        context_preview = result.get('context', '')[:500]
        if len(result.get('context', '')) > 500:
            context_preview += "..."
        
        text += f"<b>📄 Превью контекста:</b>\n<code>{context_preview}</code>"
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_keyboard())
        logger.info(f"🧪 Тест поиска: {query[:50]}...")
        
    except Exception as e:
        logger.error(f"❌ Ошибка /test_search: {e}")
        await message.answer(f"⚠️ <b>Ошибка:</b> {e}", reply_markup=get_back_keyboard())

# ============================================================================
# 🔥 РАССЫЛКА /news
# ============================================================================

@router.message(Command("news"))
async def cmd_news(message: types.Message):
    """📢 Рассылка новостей всем пользователям"""
    
    if not await is_admin(message.from_user.id):
        return await admin_only(message)
    
    news_text = message.text.replace("/news", "").strip()
    
    if not news_text:
        users_count = await db.get_user_count() if hasattr(db, 'get_user_count') else 'N/A'
        text = (
            "📢 <b>Рассылка новостей</b>\n\n"
            "💡 <b>Как использовать:</b>\n"
            "1. Напиши: <code>/news твой текст новости</code>\n"
            "2. Бот покажет предпросмотр\n"
            "3. Подтверди отправку кнопкой\n\n"
            "📝 <b>Пример:</b>\n"
            "<code>/news 📅 Дни открытых дверей 5 и 18 апреля!</code>\n\n"
            "📊 <b>Статистика:</b>\n"
            f"• Всего пользователей: {users_count}"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_keyboard())
        return
    
    user_last_message[message.from_user.id] = {
        "mode": "news_confirm",
        "text": news_text
    }
    
    users_count = await db.get_user_count() if hasattr(db, 'get_user_count') else 0
    
    preview_text = (
        "📢 <b>Предпросмотр рассылки:</b>\n\n"
        f"{news_text}\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Получателей:</b> {users_count}\n"
        f"⏱️ <b>Время:</b> {datetime.now().strftime('%H:%M:%S')}\n\n"
        "⚠️ <b>Отправить эту рассылку?</b>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="news_send")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="news_cancel")]
    ])
    
    await message.answer(preview_text, parse_mode="HTML", reply_markup=keyboard)

# ============================================================================
# 🔥 ПОДТВЕРЖДЕНИЕ РАССЫЛКИ
# ============================================================================

@router.callback_query(lambda c: c.data == "news_send")
async def news_send_confirm(callback: types.CallbackQuery):
    """✅ Подтверждение отправки рассылки"""
    
    user_id = callback.from_user.id
    user_data = user_last_message.get(user_id, {})
    
    if user_data.get("mode") != "news_confirm":
        await callback.answer("⚠️ Сессия истекла", show_alert=True)
        return
    
    news_text = user_data.get("text", "")
    user_last_message[user_id] = {}
    
    await callback.message.edit_text("🚀 <b>Начинаю рассылку...</b>\n\n⏳ Пожалуйста, подождите.")
    
    users = await db.get_all_users()
    total = len(users)
    success = 0
    failed = 0
    blocked = 0
    
    for i, user in enumerate(users):
        try:
            user_id_target = user.get('user_id') if isinstance(user, dict) else user
            
            await callback.bot.send_message(
                chat_id=user_id_target,
                text=f"📢 <b>Новость от ИиВТ ДГТУ!</b>\n\n{news_text}",
                parse_mode="HTML"
            )
            success += 1
            
            if hasattr(db, 'log_news_sent'):
                await db.log_news_sent(user_id_target)
            
        except Exception as e:
            error_text = str(e).lower()
            if "blocked" in error_text or "forbidden" in error_text:
                blocked += 1
                if hasattr(db, 'mark_user_inactive'):
                    await db.mark_user_inactive(user_id_target)
            else:
                failed += 1
        
        if (i + 1) % 30 == 0:
            await asyncio.sleep(1)
        
        if (i + 1) % 100 == 0:
            try:
                await callback.message.edit_text(
                    f"🚀 <b>Рассылка в процессе...</b>\n\n"
                    f"📊 <b>Прогресс:</b> {i + 1}/{total}\n"
                    f"✅ Успешно: {success}\n"
                    f"❌ Ошибок: {failed}\n"
                    f"🚫 Заблокировано: {blocked}"
                )
            except:
                pass
    
    report_text = (
        "✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 <b>Итоги:</b>\n"
        f"• Всего пользователей: {total}\n"
        f"• ✅ Доставлено: {success}\n"
        f"• ❌ Ошибок: {failed}\n"
        f"• 🚫 Заблокировано: {blocked}\n\n"
        f"📈 <b>Процент доставки:</b> {(success/total*100):.1f}%\n\n"
        f"🕐 <b>Время:</b> {datetime.now().strftime('%H:%M:%S')}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика рассылки", callback_data="news_stats")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
    ])
    
    try:
        await callback.message.edit_text(report_text, reply_markup=keyboard)
    except:
        await callback.message.answer(report_text, reply_markup=keyboard)
    
    logger.info(f"📢 Рассылка завершена: {success}/{total} успешно")
    await callback.answer()

# ============================================================================
# 🔥 ОТМЕНА РАССЫЛКИ
# ============================================================================

@router.callback_query(lambda c: c.data == "news_cancel")
async def news_cancel(callback: types.CallbackQuery):
    """❌ Отмена рассылки"""
    
    user_id = callback.from_user.id
    user_last_message[user_id] = {}
    
    await callback.message.edit_text("❌ <b>Рассылка отменена</b>")
    await callback.answer("Рассылка отменена")

# ============================================================================
# 🔥 СТАТИСТИКА РАССЫЛОК
# ============================================================================

@router.callback_query(lambda c: c.data == "news_stats")
async def news_stats(callback: types.CallbackQuery):
    """📊 Статистика рассылок"""
    
    if hasattr(db, 'get_news_stats'):
        stats = await db.get_news_stats()
        text = (
            "📊 <b>Статистика рассылок</b>\n\n"
            f"📬 <b>Всего рассылок:</b> {stats.get('total_news', 0)}\n"
            f"📤 <b>Всего отправлено:</b> {stats.get('total_sent', 0)}\n"
            f"✅ <b>Доставлено:</b> {stats.get('total_delivered', 0)}\n"
            f"🚫 <b>Заблокировано:</b> {stats.get('total_blocked', 0)}\n\n"
            f"📈 <b>Средний % доставки:</b> {stats.get('avg_delivery_rate', 0):.1f}%"
        )
    else:
        text = "📊 Статистика рассылок пока недоступна"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_main_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# ============================================================================
# 🔥 СТАРАЯ РАССЫЛКА /broadcast (оставляем для совместимости)
# ============================================================================

@router.message(Command("broadcast"))
async def broadcast_start(message: types.Message):
    """📢 Начало рассылки (старая версия)"""
    
    if not await is_admin(message.from_user.id):
        return await admin_only(message)
    
    await message.answer(
        "📢 <b>Режим рассылки активирован</b>\n\n"
        "Отправьте сообщение которое нужно разослать всем пользователям.\n"
        "Для отмены напишите /cancel\n\n"
        "💡 <b>Новая команда:</b> /news твой текст — быстрее и удобнее!",
        reply_markup=get_back_keyboard()
    )

@router.message(Command("cancel"))
async def cancel_broadcast(message: types.Message):
    """❌ Отмена рассылки"""
    user_last_message[message.from_user.id] = {}
    await message.answer("❌ Рассылка отменена", reply_markup=get_back_keyboard())

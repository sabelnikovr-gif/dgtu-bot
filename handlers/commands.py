"""
👋 Commands Handler for DGTU Bot
=================================
Обработчики команд: /start, /help, и главное меню
+ Аналитика + Персонализация + Улучшения

Автор: @sabelnikovr
Дата: 2026
"""

from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from handlers.keyboards import get_welcome_keyboard, get_main_keyboard
from handlers.utils import send_single_message, user_last_message, PHOTO_AI_LOGO, PHOTO_BUILDING
from services.cache_service import cache
from services.database import DatabaseService
from models.database import db
from config import Config
from pathlib import Path
import logging
from datetime import datetime, timedelta
import time 

router = Router()
logger = logging.getLogger(__name__)
# ============================================================================
# 🔥 ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================================================

ADMIN_ID = 1057899073  # ← ТВОЙ ADMIN_ID

# ============================================================================
# 🔥 ПЕРСОНАЛИЗАЦИЯ: РУССКИЕ НАЗВАНИЯ ИНТЕРЕСОВ
# ============================================================================

PROGRAM_NAMES = {
    "01.03.04": "Прикладная математика",
    "02.03.03": "Математическое обеспечение и администрирование ИС",
    "09.03.01": "Информатика и вычислительная техника",
    "09.03.02_ist": "Информационные системы и технологии (ИСТ)",
    "09.03.02_ai": "Искусственный интеллект (ИИ)",
    "09.03.02_web": "Web-разработка и программирование",
    "09.03.02_zaoch": "Информационные системы (заочное)",
    "09.03.03": "Прикладная информатика",
    "09.03.03_zaoch": "Прикладная информатика (заочное)",
    "09.03.04": "Программная инженерия",
    "10.03.01": "Информационная безопасность",
    "10.05.01": "Компьютерная безопасность (специалитет)",
    "10.05.02": "Информационная безопасность (специалитет)",
}

FAQ_NAMES = {
    "scholarships": "💰 Стипендии",
    "dormitory": "🏠 Общежитие",
    "documents": "📄 Документы для поступления",
    "deadlines": "📅 Сроки подачи документов",
    "cost": "💵 Стоимость обучения",
    "passing_scores": "📊 Проходные баллы ЕГЭ",
    "vuts": "🎖️ Военный учебный центр (ВУЦ)",
    "contacts": "📞 Контакты приёмной комиссии",
}

INTEREST_NAMES = {
    "program": "📚 Направление подготовки",
    "faq": FAQ_NAMES,
}


def get_interest_display(interest_type: str, interest_value: str) -> str:
    """🎯 Возвращает красивое название интереса на русском"""
    if interest_type == "program":
        name = PROGRAM_NAMES.get(interest_value, interest_value)
        return f"📚 {name}"
    elif interest_type == "faq":
        faq_names = INTEREST_NAMES.get("faq", {})
        name = faq_names.get(interest_value, interest_value)
        return f"❓ {name}"
    return f"🔹 {interest_type}: {interest_value}"


def get_personalized_recommendations(interests: list) -> str:
    """🎯 Генерирует персонализированные рекомендации"""
    recommendations = []
    
    for interest in interests[:3]:
        if hasattr(interest, 'keys'):
            interest_dict = dict(interest)
            interest_type = interest_dict['interest_type']
            interest_value = interest_dict['interest_value']
        else:
            interest_type = interest[0]
            interest_value = interest[1]
        
        if interest_type == "program":
            recommendations.append("🧮 Рассчитать шансы на поступление")
            recommendations.append("📋 Чек-лист для подачи документов")
            recommendations.append("📚 Узнать подробнее о направлении")
        elif interest_type == "faq":
            if interest_value == "scholarships":
                recommendations.append("💰 Узнать про стипендии 2026")
                recommendations.append("📊 Проверить проходные баллы")
            elif interest_value == "dormitory":
                recommendations.append("🏠 Подать заявку в общежитие")
                recommendations.append("📍 Узнать адрес и стоимость")
            elif interest_value == "documents":
                recommendations.append("📄 Скачать шаблоны документов")
                recommendations.append("📋 Чек-лист абитуриента")
            elif interest_value == "passing_scores":
                recommendations.append("🧮 Калькулятор баллов ЕГЭ")
                recommendations.append("📊 Сравнить направления")
    
    unique_recs = list(dict.fromkeys(recommendations))[:3]
    
    if not unique_recs:
        unique_recs = [
            "🧮 Рассчитать свои шансы",
            "📋 Чек-лист для подачи",
            "💬 Задать вопрос волонтёру"
        ]
    
    return "\n".join(f"• {rec}" for rec in unique_recs)


# ============================================================================
# 🔥 КОМАНДА /start — КРАСИВОЕ ПРИВЕТСТВИЕ
# ============================================================================

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """👋 Приветствие — С ПЕРСОНАЛИЗАЦИЕЙ"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = message.from_user.username or ""
    
    # 🔥 Сохраняем пользователя в БД
    await DatabaseService.track_user(
        user_id=user_id,
        username=username,
        first_name=user_name,
        last_name=message.from_user.last_name
    )
    
    # 🔥 Обновляем активность
    await db.update_user_activity(user_id)
    
    # 🔥 Получаем интересы
    interests = await db.get_user_interests(user_id, min_score=1)
    
    logger.info(f"✅ Пользователь {user_id} @{username} сохранён в БД")
    
    # 🔥 Формируем текст
    text = f"👋 <b>Привет, {user_name}!</b>\n\n"
    
    # 🔥 Персонализированный блок
    if interests:
        text += "💡 <b>Видим, ты интересовался:</b>\n"
        
        for interest in interests[:3]:
            if hasattr(interest, 'keys'):
                interest_dict = dict(interest)
                interest_type = interest_dict['interest_type']
                interest_value = interest_dict['interest_value']
            else:
                interest_type = interest[0]
                interest_value = interest[1]
            
            display_name = get_interest_display(interest_type, interest_value)
            text += f"• {display_name}\n"
        
        recommendations = get_personalized_recommendations(interests)
        text += f"\n🎯 <b>Возможно, будет полезно:</b>\n"
        text += recommendations
        text += "\n\n"
    
    # 🔥 Основной текст
    text += (
        "🎓 <b>ИиВТ ДГТУ Помощник</b>\n\n"
        "📌 <b>Все функции бота:</b>\n"
        "• 📚 13 направлений подготовки\n"
        "• 📅 Дни открытых дверей: 5 и 18 апреля\n"
        "• 💰 Проходные баллы 2025 и стоимость\n"
        "• 🧮 Калькулятор баллов ЕГЭ\n"
        "• 📋 Чек-лист абитуриента\n"
        "• ❓ Ответы на частые вопросы\n"
        "• 🤖 ИИ-помощник (GigaChat)\n"
        "• 🔍 Умный поиск\n"
        "• 📞 Связь с волонтёром\n"
        "• 💰 Стипендии 2026\n"
        "• 🎖️ ВУЦ\n"
        "• 👥 Руководство факультета\n\n"
        "👇 <b>Нажми кнопку для начала:</b>"
    )
    
    keyboard = get_welcome_keyboard()
    
    try:
        old_msg_id = user_last_message.get(user_id)
        if old_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=old_msg_id)
            except:
                pass
        
        photo_path = str(PHOTO_AI_LOGO) if PHOTO_AI_LOGO.exists() else None
        
        if photo_path:
            msg = await message.answer_photo(
                photo=FSInputFile(photo_path),
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            msg = await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
        user_last_message[user_id] = msg.message_id
        
    except Exception as e:
        logger.error(f"❌ Ошибка /start: {e}")
        msg = await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        user_last_message[user_id] = msg.message_id


# ============================================================================
# 🔥 БЫСТРЫЕ КОМАНДЫ
# ============================================================================

@router.message(Command("checklist"))
async def cmd_checklist(message: types.Message):
    """📋 Чек-лист — команда"""
    user_id = message.from_user.id
    tasks = await db.get_user_checklist(user_id)
    
    if not tasks:
        DEFAULT_TASKS = [
            "📄 Подготовить паспорт и копии",
            "🎓 Получить документ об образовании",
            "📸 Сделать фотографии 3×4 (4 шт.)",
            "💳 Получить СНИЛС",
            "📝 Подготовить результаты ЕГЭ",
            "🏥 Получить медсправку 086/у",
            "✍️ Подать заявление о приёме",
            "✅ Подать согласие на зачисление",
        ]
        for task in DEFAULT_TASKS:
            await db.add_checklist_task(user_id, task)
        tasks = await db.get_user_checklist(user_id)
    
    total = len(tasks)
    completed = sum(1 for task in tasks if task[2] == 1)
    progress_percent = round((completed / total * 100)) if total > 0 else 0
    
    text = f"📋 <b>Твой чек-лист:</b>\n\n"
    for task in tasks:
        task_name = task[1]
        is_completed = task[2] == 1
        status = "✅" if is_completed else "⬜️"
        text += f"{status} {task_name}\n"
    
    text += f"\n📈 Прогресс: {progress_percent}%\n"
    text += f"✅ {completed} из {total} выполнено"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Открыть полный чек-лист", callback_data="checklist_btn")]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.message(Command("calculator"))
async def cmd_calculator(message: types.Message):
    """🧮 Калькулятор — команда"""
    text = (
        "🧮 <b>Калькулятор баллов ЕГЭ</b>\n\n"
        "💡 <b>Минимум:</b>\n"
        "• Математика: 44\n"
        "• Русский: 40\n"
        "• Информатика/Физика: 44\n\n"
        "👇 <b>Нажми кнопку чтобы рассчитать:</b>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧮 Открыть калькулятор", callback_data="calculator_btn")]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.message(Command("quick_help"))
async def cmd_quick_help(message: types.Message):
    """📞 Быстрая помощь — команда"""
    text = (
        "📞 <b>Связь с волонтёром-студентом</b>\n\n"
        "💬 <b>Напиши свой вопрос:</b>\n"
        "• По каким предметам ЕГЭ?\n"
        "• Какое направление интересует?\n"
        "• Что именно хочешь узнать?\n\n"
        "⏱️ <b>Ответим в течение 15 минут!</b>\n"
        "🕐 Рабочее время: 10:00-18:00"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать волонтёру", callback_data="help_volunteer")]
    ])
    
    await message.answer(text, reply_markup=keyboard)




# ============================================================================
# 🔥 АНАЛИТИКА — ТОП ВОПРОСОВ
# ============================================================================

@router.message(Command("top_questions"))
async def cmd_top_questions(message: types.Message):
    """📊 Топ популярных вопросов к ИИ (АДМИН)"""
    ADMIN_ID = 1057899073
    
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён")
        return
    
    # Получаем топ вопросов из кэша
    top_queries = []
    for key in cache.cache.keys():
        if key.startswith("search_query:"):
            data = cache.cache[key]['value']
            if isinstance(data, dict):
                query = data.get('query', 'N/A')
                count = data.get('count', 1)
                top_queries.append((query, count))
    
    top_queries.sort(key=lambda x: x[1], reverse=True)
    
    text = "📊 <b>Топ-10 вопросов к ИИ:</b>\n\n"
    for i, (query, count) in enumerate(top_queries[:10], 1):
        text += f"{i}. <b>{query}</b> — {count} раз(а)\n"
    
    if not top_queries:
        text += "ℹ️ Пока нет данных"
    
    await message.answer(text, parse_mode="HTML")


# ============================================================================
# 🔥 АНАЛИТИКА — АКТИВНОСТЬ ПО ЧАСАМ
# ============================================================================

@router.message(Command("activity"))
async def cmd_activity(message: types.Message):
    """📈 Активность пользователей по часам (АДМИН)"""
    ADMIN_ID = 1057899073
    
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён")
        return
    
    # Считаем активность по часам
    hours = {i: 0 for i in range(24)}
    
    for key in cache.cache.keys():
        if key.startswith("user_activity:"):
            data = cache.cache[key]['value']
            if isinstance(data, dict) and 'hour' in data:
                hour = data['hour']
                hours[hour] = hours.get(hour, 0) + 1
    
    # Находим пик
    peak_hour = max(hours, key=hours.get) if any(hours.values()) else 12
    
    text = "📈 <b>Активность по часам:</b>\n\n"
    for hour in range(0, 24, 3):  # Каждые 3 часа
        count = hours[hour]
        bar = "🟩" * min(count, 10)
        text += f"{hour:02d}:00 | {bar} ({count})\n"
    
    text += f"\n🔥 <b>Пик активности:</b> {peak_hour:02d}:00"
    
    await message.answer(text, parse_mode="HTML")


# ============================================================================
# 🔥 АНАЛИТИКА — КОНВЕРСИЯ ЧЕК-ЛИСТА
# ============================================================================

@router.message(Command("conversion"))
async def cmd_conversion(message: types.Message):
    """📊 Конверсия чек-листов (АДМИН)"""
    ADMIN_ID = 1057899073
    
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён")
        return
    
    # Считаем конверсию
    total_users = 0
    completed_checklists = 0
    
    for key in cache.cache.keys():
        if key.startswith("checklist_progress:"):
            data = cache.cache[key]['value']
            if isinstance(data, dict):
                total_users += 1
                if data.get('percent', 0) == 100:
                    completed_checklists += 1
    
    conversion_rate = (completed_checklists / total_users * 100) if total_users > 0 else 0
    
    text = (
        "📊 <b>Конверсия чек-листов:</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Завершили чек-лист: {completed_checklists}\n"
        f"📈 Конверсия: {conversion_rate:.1f}%\n\n"
        f"💡 <b>Совет:</b> отправь напоминание тем, кто не завершил!"
    )
    
    await message.answer(text, parse_mode="HTML")


# ============================================================================
# 🔥 АНАЛИТИКА — ПОПУЛЯРНЫЕ НАПРАВЛЕНИЯ
# ============================================================================

@router.message(Command("popular_programs"))
async def cmd_popular_programs(message: types.Message):
    """📚 Популярные направления (АДМИН)"""
    ADMIN_ID = 1057899073
    
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён")
        return
    
    # Считаем просмотры направлений
    programs = {}
    
    for key in cache.cache.keys():
        if key.startswith("program_view:"):
            code = key.replace("program_view:", "")
            programs[code] = programs.get(code, 0) + 1
    
    sorted_programs = sorted(programs.items(), key=lambda x: x[1], reverse=True)
    
    text = "📚 <b>Популярные направления:</b>\n\n"
    for code, count in sorted_programs[:10]:
        name = PROGRAM_NAMES.get(code, code)
        text += f"• {name} — {count} просмотров\n"
    
    if not sorted_programs:
        text += "ℹ️ Пока нет данных"
    
    await message.answer(text, parse_mode="HTML")


# ============================================================================
# 🔥 АНАЛИТИКА — ВРЕМЯ ОТВЕТА ИИ
# ============================================================================

@router.message(Command("ai_stats"))
async def cmd_ai_stats(message: types.Message):
    """🤖 Статистика ИИ-помощника (АДМИН)"""
    ADMIN_ID = 1057899073
    
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён")
        return
    
    # Считаем среднее время ответа
    response_times = []
    total_queries = 0
    
    for key in cache.cache.keys():
        if key.startswith("ai_response_time:"):
            data = cache.cache[key]['value']
            if isinstance(data, (int, float)):
                response_times.append(data)
                total_queries += 1
    
    avg_time = sum(response_times) / len(response_times) if response_times else 0
    
    text = (
        "🤖 <b>Статистика ИИ-помощника:</b>\n\n"
        f"💬 Всего запросов: {total_queries}\n"
        f"⏱️ Среднее время ответа: {avg_time:.2f} сек\n"
        f"🚀 Быстрее 3 сек: {sum(1 for t in response_times if t < 3)}\n"
        f"🐌 Медленнее 5 сек: {sum(1 for t in response_times if t > 5)}\n\n"
        f"💡 <b>Цель:</b> среднее время < 3 сек"
    )
    
    await message.answer(text, parse_mode="HTML")


# ============================================================================
# 🔥 ПОДЕЛИТЬСЯ РЕЗУЛЬТАТОМ
# ============================================================================

@router.message(Command("share"))
async def cmd_share(message: types.Message):
    """📤 Поделиться результатом с другом"""
    text = (
        "📤 <b>Поделиться с другом</b>\n\n"
        "💡 <b>Отправь другу:</b>\n\n"
        "🎓 <b>ИиВТ ДГТУ Помощник</b>\n"
        "Твой персональный помощник для поступления!\n\n"
        "📚 13 направлений\n"
        "🧮 Калькулятор ЕГЭ\n"
        "📋 Чек-лист абитуриента\n"
        "🤖 ИИ-помощник 24/7\n\n"
        f"🔗 t.me/iivt_dgtu_bot"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться", switch_inline_query="🎓 ИиВТ ДГТУ Помощник — твой помощник для поступления!")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ============================================================================
# 🔥 ЗАКРЕПЛЁННОЕ СООБЩЕНИЕ
# ============================================================================

@router.message(Command("pin_info"))
async def cmd_pin_info(message: types.Message):
    """📌 Закрепить важную информацию (АДМИН)"""
    ADMIN_ID = 1057899073
    
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён")
        return
    
    text = (
        "📌 <b>ВАЖНАЯ ИНФОРМАЦИЯ</b>\n\n"
        "🗓️ <b>Дни открытых дверей:</b>\n"
        "• 5 апреля 2026 — ДГТУ\n"
        "• 18 апреля 2026 — ИиВТ\n\n"
        "📅 <b>Сроки подачи:</b>\n"
        "• С 20 июня — начало приёма\n"
        "• До 1 августа — согласие на зачисление\n\n"
        "📞 <b>Контакты:</b>\n"
        "• +7 (863) 273-85-31\n"
        "• abitur@donstu.ru\n\n"
        "🌐 donstu.ru/abitur"
    )
    
    msg = await message.answer(text, parse_mode="HTML")
    
    try:
        await msg.pin()
        await message.answer("✅ Сообщение закреплено!")
    except Exception as e:
        logger.error(f"❌ Ошибка закрепления: {e}")
        await message.answer("⚠️ Не удалось закрепить сообщение")


# ============================================================================
# 🔥 ОТЗЫВЫ — СТАТИСТИКА
# ============================================================================

@router.message(Command("feedback_stats"))
async def cmd_feedback_stats(message: types.Message):
    """📊 Статистика отзывов (АДМИН)"""
    ADMIN_ID = 1057899073
    
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён")
        return
    
    good_count = 0
    bad_count = 0
    reasons = {}
    
    for key in cache.cache.keys():
        if key.startswith("feedback:"):
            data = cache.cache[key]['value']
            if isinstance(data, dict) and 'rating' in data: 
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
    
    text = (
        f"📊 <b>СТАТИСТИКА ОБРАТНОЙ СВЯЗИ</b>\n\n"
        f"👍 Полезно: <b>{good_count}</b> ({good_percent}%)\n"
        f"👎 Не помогло: <b>{bad_count}</b>\n"
        f"📈 Всего отзывов: <b>{total}</b>\n\n"
        f"❌ <b>Частые причины негатива:</b>\n"
        f"{top_reasons}"
    )
    
    await message.answer(text, parse_mode="HTML")


# ============================================================================
# 🔥 ГЛАВНОЕ МЕНЮ ИЗ ПРИВЕТСТВИЯ
# ============================================================================

@router.callback_query(lambda c: c.data == "show_main_menu")
async def show_main_menu_from_welcome(callback: types.CallbackQuery):
    """🏠 Главное меню из приветствия"""
    user_id = callback.from_user.id
    
    text = "✨ <b>Главное меню</b>"
    keyboard = get_main_keyboard()
    
    photo_path = str(PHOTO_BUILDING) if PHOTO_BUILDING.exists() else None
    await send_single_message(callback, text, reply_markup=keyboard, photo_path=photo_path)
    await callback.answer()
# ============================================================================
# 🔄 CHANGELOG — ИСТОРИЯ ОБНОВЛЕНИЙ
# ============================================================================

CHANGELOG = [
    "🗓️ 29.04.2026 — Поиск теперь показывает ТОЛЬКО релевантные результаты",
    "🗓️ 29.04.2026 — Добавлена категория для каждого запроса поиска",
    "🗓️ 29.04.2026 — Исправлен дублирующий обработчик /search",
    "🗓️ 28.04.2026 — Исправлена ошибка ADMIN_ID в handle_text",
    "🗓️ 28.04.2026 — Добавлена отладка для функции поиска",
    "🗓️ 28.04.2026 — Улучшены синонимы для поиска (общага → общежит)",
    "🗓️ 22.04.2026 — Добавлены авто-ответы на частые вопросы",
    "🗓️ 22.04.2026 — Улучшен поиск: теперь понимает синонимы",
    "🗓️ 22.04.2026 — Добавлена команда /changelog",
    "🗓️ 22.04.2026 — Добавлена команда /feedback для отзывов",
    "🗓️ 20.04.2026 — Исправлена ошибка с тегами в ответах ИИ",
    "🗓️ 20.04.2026 — Добавлена очистка Markdown в ответах ИИ",
    "🗓️ 18.04.2026 — Добавлена анимация 'печатает...' перед ответом",
    "🗓️ 18.04.2026 — ИИ теперь отвечает в режиме 1 сообщения (reply)",
    "🗓️ 15.04.2026 — Добавлены кнопки 👍/👎 для оценки ответов ИИ",
    "🗓️ 15.04.2026 — Исправлена ошибка с тегом <ul> в ответах",
    "🗓️ 15.04.2026 — Добавлена очистка неподдерживаемых HTML-тегов",
    "🗓️ 12.04.2026 — Добавлен режим волонтёра для админа",
    "🗓️ 12.04.2026 — Абитуриенты могут писать волонтёру",
    "🗓️ 10.04.2026 — Запущен ИИ-помощник с контекстным поиском",
    "🗓️ 10.04.2026 — Добавлена интеграция с GigaChat API",
    "🗓️ 10.04.2026 — Добавлен RAG (поиск по базе знаний)",
    "🗓️ 08.04.2026 — Добавлен умный поиск /search",
    "🗓️ 08.04.2026 — Добавлена база знаний FAQ",
    "🗓️ 05.04.2026 — Добавлен чек-лист абитуриента с прогрессом",
    "🗓️ 05.04.2026 — Добавлен калькулятор баллов ЕГЭ",
    "🗓️ 05.04.2026 — Добавлены проходные баллы 2025",
    "🗓️ 03.04.2026 — Добавлена информация о стипендиях",
    "🗓️ 03.04.2026 — Добавлена информация об общежитии",
    "🗓️ 03.04.2026 — Добавлена информация о ВУЦ",
    "🗓️ 01.04.2026 — Добавлены разделы: Кафедры, Достижения",
    "🗓️ 01.04.2026 — Добавлены разделы: Руководство, Контакты",
    "🗓️ 01.04.2026 — Добавлена пагинация для направлений",
    "🗓️ 01.04.2026 — Добавлено 13 направлений подготовки",
    "🗓️ 01.04.2026 — Добавлены дни открытых дверей",
    "🗓️ 28.03.2026 — Добавлено кеширование запросов",
    "🗓️ 28.03.2026 — Добавлена база данных SQLite",
    "🗓️ 25.03.2026 — Добавлено логирование событий",
    "🗓️ 25.03.2026 — Добавлена аналитика для админа",
    "🗓️ 22.03.2026 — Добавлена персонализация приветствия",
    "🗓️ 22.03.2026 — Добавлено главное меню с фото",
    "🗓️ 20.03.2026 — Настроена работа через прокси",
    "🗓️ 20.03.2026 — Добавлена поддержка aiogram 3.x",
    "🗓️ 18.03.2026 — Добавлены команды администратора",
    "🗓️ 18.03.2026 — Добавлена система роутеров",
    "🗓️ 16.03.2026 — 🎉 ПЕРВЫЙ ЗАПУСК БОТА!",
    "🗓️ 16.03.2026 — Создана структура проекта",
    "🗓️ 16.03.2026 — Зарегистрирован бот @iivt_dgtu_bot",
]

@router.message(Command("changelog"))
async def cmd_changelog(message: types.Message):
    """🔄 Показать историю обновлений бота"""
    
    text = "🔄 <b>Что нового в боте:</b>\n\n"
    
    for entry in CHANGELOG[:8]:
        text += f"{entry}\n"
    
    if len(CHANGELOG) > 8:
        text += f"\n<i>💡 Всего обновлений: {len(CHANGELOG)}</i>"
    
    text += "\n\n🔗 <b>Нашёл баг или есть идея?</b>\n"
    text += "<b>Напиши:</b> /feedback твой_отзыв"
    
    # 🔥 ОБНОВЛЁННЫЕ КНОПКИ
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать отзыв", callback_data="feedback_text")],
        [InlineKeyboardButton(text="👍 Помогло", callback_data="feedback_good"),
         InlineKeyboardButton(text="👎 Не помогло", callback_data="feedback_bad")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    logger.info(f"🔄 /changelog запрошен пользователем {message.from_user.id}")
# ============================================================================
# 🔄 CHANGELOG — ПОЛНАЯ ИСТОРИЯ (АДМИН)
# ============================================================================

@router.message(Command("changelog_full"))
async def cmd_changelog_full(message: types.Message):
    """📜 Полная история обновлений (ТОЛЬКО АДМИН)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён")
        return
    
    # 🔥 Функция очистки от неподдерживаемых HTML-тегов
    def clean_changelog_text(text: str) -> str:
        """Убирает теги которые Telegram не поддерживает"""
        import re
        # Убираем ВСЕ HTML-теги кроме поддерживаемых
        text = re.sub(r'</?(ul|ol|li|p|div|span|table|tr|td|th|thead|tbody|hr|img|h[1-6])[^>]*>', '', text)
        # Заменяем <br> на перенос строки
        text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
        # Убираем лишние переносы
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    # Разбиваем на части (Telegram лимит 4096 символов)
    all_text = "\n".join(CHANGELOG)
    all_text = clean_changelog_text(all_text)  # 🔥 ОЧИЩАЕМ ТЕКСТ!
    
    if len(all_text) > 4000:
        # Отправляем частями
        for i in range(0, len(all_text), 4000):
            chunk = all_text[i:i+4000]
            # 🔥 Используем parse_mode="HTML" только для заголовка, текст — чистый
            await message.answer(
                f"📜 <b>История обновлений (часть {i//4000 + 1}):</b>\n\n<code>{chunk}</code>",
                parse_mode="HTML"
            )
    else:
        await message.answer(
            f"📜 <b>Полная история обновлений ({len(CHANGELOG)} записей):</b>\n\n<code>{all_text}</code>",
            parse_mode="HTML"
        )
    
    logger.info(f"📜 /changelog_full запрошен админом {message.from_user.id}")
# ============================================================================
# 💬 КОМАНДА /feedback — ОТПРАВИТЬ ОТЗЫВ
# ============================================================================

@router.message(Command("feedback"))
async def cmd_feedback(message: types.Message):
    """💬 Отправить отзыв разработчику"""
    
    # Получаем текст после команды
    args = message.text.replace("/feedback", "").strip()
    
    if not args:
        # Если нет текста — показываем инструкцию
        text = (
            "💬 <b>Отправить отзыв</b>\n\n"
            "✍️ <b>Напиши отзыв после команды:</b>\n"
            "<code>/feedback тут твой текст</code>\n\n"
            "📌 <b>Пример:</b>\n"
            "<code>/feedback Бот супер, но не хватает тёмной темы</code>\n\n"
            "💡 <b>Или нажми 👍/👎 под ответом ИИ</b>"
        )
        await message.answer(text, parse_mode="HTML")
        return
    
    # 🔥 Сохраняем отзыв в кэш
    from services.cache_service import cache
    import time
    
    # ✅ СТАЛО (правильный код):
    await cache.set(f"feedback:{message.from_user.id}:{int(time.time())}", {
        "user_id": message.from_user.id,
        "username": message.from_user.username or "N/A",
        "text": args,
        "timestamp": time.time(),
        "type": "text_feedback"
    })
    
    # 🔥 Логируем в консоль
    logger.info(f"💬 НОВЫЙ ОТЗЫВ от @{message.from_user.username or message.from_user.first_name}:")
    logger.info(f"💬 Текст: {args}")
    
    # 🔥 Отправляем админу в ЛС (опционально)
    ADMIN_ID = 1057899073
    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"💬 <b>Новый отзыв</b>\n\n"
            f"👤 От: @{message.from_user.username or message.from_user.first_name}\n"
            f"🆔 ID: {message.from_user.id}\n"
            f"💬 Текст: {args}"
        )
    except:
        pass
    
    # ✅ Ответ пользователю
    await message.answer(
        "✅ <b>Спасибо за отзыв!</b>\n\n"
        "💙 Твоё мнение помогает сделать бота лучше!"
    )

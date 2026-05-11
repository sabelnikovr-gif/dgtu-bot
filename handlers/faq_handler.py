from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from services.rag_service import rag_service
from services.llm_service import llm_service
from services.cache_service import cache, data_cache
from handlers.keyboards import (
    get_faq_keyboard, get_programs_keyboard,
    get_open_days_keyboard, get_leadership_keyboard,
    get_ai_assistant_keyboard, get_feedback_keyboard, get_feedback_reason_keyboard,
    get_calculator_subjects_keyboard, get_checklist_keyboard,
    get_departments_keyboard, get_achievements_keyboard
)
from handlers.utils import send_single_message, get_back_keyboard, user_last_message, PHOTO_BUILDING, PHOTO_AI_LOGO, PHOTO_CLOCK, PHOTO_DGTU_LOGO, PHOTO_BUILDING_FOUNTAIN
from config import Config
from pathlib import Path
import logging
import re
import asyncio
import time 

async def auto_delete_message(bot, chat_id, message_id, delay_seconds: int = 60):
    """🗑️ Автоматическое удаление сообщения через N секунд"""
    try:
        await asyncio.sleep(delay_seconds)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.debug(f"🗑️ Сообщение {message_id} удалено через {delay_seconds} сек")
    except Exception as e:
        # Игнорируем ошибки (сообщение уже удалено или не найдено)
        logger.debug(f"⚠️ Не удалось удалить сообщение {message_id}: {e}")

router = Router()
logger = logging.getLogger(__name__)

# ============================================================================
# 🔥 ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================================================

ai_mode_users = set()
volunteer_mode_users = {}
volunteer_reply_to = {}

ADMIN_ID = 1057899073
VOLUNTEER_IDS = [ADMIN_ID]
# ============================================================================
# 💬 АВТО-ОТВЕТЫ НА ЧАСТЫЕ ВОПРОСЫ (БЕЗ ИИ)
# ============================================================================

QUICK_REPLIES = {
    "привет": "👋 Привет! Чем могу помочь?",
    "здравствуй": "👋 Здравствуйте! Чем могу помочь?",
    "спасибо": "💙 Всегда рад помочь!",
    "спс": "💙 Всегда рад помочь!",
    "как дела": "🤖 У меня всё отлично, спасибо! А у тебя?",
    "кто ты": "🤖 Я ИИ-помощник ИиВТ ДГТУ. Отвечаю на вопросы абитуриентов 24/7!",
    "помощь": "💡 Напиши свой вопрос или выбери раздел в меню!",
    "сколько стоит": "💰 Стоимость обучения:\n• Бакалавриат: 135 000 - 153 300 ₽/год\n• Специалитет: 153 300 ₽/год",
    "цена": "💰 Стоимость обучения:\n• Бакалавриат: 135 000 - 153 300 ₽/год",
    "сколько баллов": "📊 Минимальные баллы ЕГЭ:\n• Математика: 44\n• Русский: 40\n• Информатика/Физика: 44",
    "баллы": "📊 Минимальные баллы ЕГЭ:\n• Математика: 44\n• Русский: 40\n• Информатика/Физика: 44",
    "общежитие": "🏠 Общежитие ДГТУ:\n• Есть места для иногородних\n• Стоимость: от 1 500 ₽/мес",
    "общага": "🏠 Общежитие ДГТУ:\n• Есть места для иногородних\n• Стоимость: от 1 500 ₽/мес",
    "когда подача": "📅 Сроки подачи:\n• С 20 июня — начало приёма\n• До 1 августа — согласие на зачисление",
    "сроки": "📅 Сроки подачи:\n• С 20 июня — начало приёма\n• До 1 августа — согласие на зачисление",
    "вуц": "🎖️ ВУЦ: Офицер 2.5 года, Сержант 2 года, Солдат 1.5 года. 📞 +7 (863) 258-92-89",
    "военка": "🎖️ ВУЦ: Офицер 2.5 года, Сержант 2 года, Солдат 1.5 года. 📞 +7 (863) 258-92-89",
    "пока": "👋 До связи! Заходи ещё!",
}

# ============================================================================
# 🔍 СИНОНИМЫ ДЛЯ ПОИСКА
# ============================================================================

SEARCH_SYNONYMS = {
    # 🔹 Общежитие → ключ "общежит" (как в keywords_map!)
    "общага": "общежит",
    "жиле": "общежит",
    "студгородок": "общежит",
    "комната общежития": "общежит",
    "место в общежитии": "общежит",
    
    # 🔹 Баллы → ключ "балл"
    "баллы": "балл",
    "егэ": "балл",
    "проходной": "балл",
    "проходные": "балл",
    "минимум баллов": "балл",
    
    # 🔹 Стоимость → ключ "стоим"
    "цена": "стоим",
    "сколько стоит": "стоим",
    "платно": "стоим",
    "контракт": "стоим",
    "обучение платное": "стоим",
    
    # 🔹 Стипендия → ключ "стипенд"
    "деньги": "стипенд",
    "стипендии": "стипенд",
    "выплата": "стипенд",
    "гас": "стипенд",
    "гсс": "стипенд",
    
    # 🔹 ВУЦ → ключ "вуц"
    "военка": "вуц",
    "военный": "вуц",
    "армия": "вуц",
    
    # 🔹 Сроки → ключ "срок"
    "подача": "срок",
    "дедлайн": "срок",
    "когда подавать": "срок",
    
    # 🔹 Документы → ключ "документ"
    "паспорт": "документ",
    "аттестат": "документ",
    "снилс": "документ",
    
    # 🔹 Контакты → ключ "контакт"
    "приёмка": "контакт",
    "приёмная": "контакт",
    "телефон": "контакт",
}

def normalize_search_query(query: str) -> str:
    """🔍 Нормализует поисковый запрос (синонимы + регистр)"""
    query = query.lower().strip()
    for synonym, official in SEARCH_SYNONYMS.items():
        if query == synonym or query.startswith(synonym) or synonym in query:
            query = query.replace(synonym, official)
            break
    return query
# ============================================================================
# 🔥 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def _clean_html(text: str) -> str:
    """🧹 Полная очистка от всех тегов"""
    if not text:
        return ""
    
    # 🔥 Убираем ВСЕ HTML-теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # 🔥 Убираем Markdown
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **жирный**
    text = re.sub(r'\*(.*?)\*', r'\1', text)       # *курсив*
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)  # # заголовки
    text = re.sub(r'```[\s\S]*?```', '', text)     # блоки кода
    text = re.sub(r'`([^`]+)`', r'\1', text)       # `inline code`
    
    # 🔥 Нормализуем переносы
    text = text.replace('<br>', '\n').replace('<br/>', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

async def safe_callback_answer(callback: types.CallbackQuery):
    """✅ Безопасный callback"""
    try:
        await callback.answer()
    except Exception as e:
        if "query is too old" not in str(e):
            logger.debug(f"⚠️ Ошибка callback: {e}")

async def send_photo_message(callback, text, reply_markup, photo_path):
    """
    🔥 ОТПРАВКА СООБЩЕНИЯ С ФОТО (всегда с фото!)
    """
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    bot = callback.bot
    old_msg_id = user_last_message.get(user_id)
    
    try:
        if old_msg_id:
            try:
                old_message = await bot.get_message(chat_id, old_msg_id)
                has_photo = bool(old_message.photo)
            except:
                has_photo = False
            
            if len(text) > 1024:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
                except:
                    pass
                new_msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
                user_last_message[user_id] = new_msg.message_id
            elif has_photo and photo_path and Path(photo_path).exists():
                media = InputMediaPhoto(media=FSInputFile(photo_path), caption=text, parse_mode="HTML")
                await bot.edit_message_media(media=media, chat_id=chat_id, message_id=old_msg_id, reply_markup=reply_markup)
            else:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
                except:
                    pass
                if photo_path and Path(photo_path).exists() and len(text) <= 1024:
                    new_msg = await bot.send_photo(chat_id=chat_id, photo=FSInputFile(photo_path), caption=text, reply_markup=reply_markup, parse_mode="HTML")
                else:
                    new_msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
                user_last_message[user_id] = new_msg.message_id
        else:
            if photo_path and Path(photo_path).exists() and len(text) <= 1024:
                new_msg = await bot.send_photo(chat_id=chat_id, photo=FSInputFile(photo_path), caption=text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                new_msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
            user_last_message[user_id] = new_msg.message_id
    except Exception as e:
        logger.error(f"❌ Ошибка отправки фото: {e}")
        try:
            new_msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
            user_last_message[user_id] = new_msg.message_id
        except Exception as e2:
            logger.error(f"❌ Ошибка отправки текста: {e2}")

# ============================================================================
# 🔥 ГЛАВНОЕ МЕНЮ — ВСЕГДА С ФОТО
# ============================================================================

@router.callback_query(lambda c: c.data == "show_main_menu")
async def show_main_menu_from_welcome(callback: types.CallbackQuery):
    """🏠 Главное меню — ВСЕГДА С ФОТО"""
    text = "✨ <b>Главное меню</b>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Направления", callback_data="programs"), 
         InlineKeyboardButton(text="📅 Дни открытых дверей", callback_data="open_days")],
        [InlineKeyboardButton(text="❓ Часто задаваемые вопросы", callback_data="faq"), 
         InlineKeyboardButton(text="👥 Руководство", callback_data="leadership")],
        [InlineKeyboardButton(text="🤖 ИИ-помощник", callback_data="ai_assistant"), 
         InlineKeyboardButton(text="📞 Волонтёр", callback_data="help_volunteer")],
        [InlineKeyboardButton(text="🧮 Калькулятор ЕГЭ", callback_data="calculator_btn"), 
         InlineKeyboardButton(text="📋 Чек-лист", callback_data="checklist_btn")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="smart_search_btn"), 
         InlineKeyboardButton(text="🎯 Тест", callback_data="quiz_start")],
        [InlineKeyboardButton(text="🏛️ Кафедры", callback_data="departments"), 
         InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements")],
        [InlineKeyboardButton(text="🌐 Сайт ДГТУ", url="https://donstu.ru"), 
         InlineKeyboardButton(text="💬 ВК", url="https://vk.ru/iivtdstu")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about_bot")]
    ])
    
    photo_path = str(PHOTO_BUILDING) if PHOTO_BUILDING.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

@router.callback_query(lambda c: c.data == "go_back")
async def go_back(callback: types.CallbackQuery):
    """⬅️ Кнопка "Назад" — всегда с фото"""
    text = "✨ <b>Главное меню</b>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Направления", callback_data="programs"), 
         InlineKeyboardButton(text="📅 Дни открытых дверей", callback_data="open_days")],
        [InlineKeyboardButton(text="❓ Часто задаваемые вопросы", callback_data="faq"), 
         InlineKeyboardButton(text="👥 Руководство", callback_data="leadership")],
        [InlineKeyboardButton(text="🤖 ИИ-помощник", callback_data="ai_assistant"), 
         InlineKeyboardButton(text="📞 Волонтёр", callback_data="help_volunteer")],
        [InlineKeyboardButton(text="🧮 Калькулятор ЕГЭ", callback_data="calculator_btn"), 
         InlineKeyboardButton(text="📋 Чек-лист", callback_data="checklist_btn")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="smart_search_btn"), 
         InlineKeyboardButton(text="🎯 Тест", callback_data="quiz_start")],
        [InlineKeyboardButton(text="🏛️ Кафедры", callback_data="departments"), 
         InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements")],
        [InlineKeyboardButton(text="🌐 Сайт ДГТУ", url="https://donstu.ru"), 
         InlineKeyboardButton(text="💬 ВК", url="https://vk.ru/iivtdstu")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about_bot")]
    ])
    
    photo_path = str(PHOTO_BUILDING) if PHOTO_BUILDING.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

# ============================================================================
# 🔥 ОСНОВНЫЕ РАЗДЕЛЫ
# ============================================================================

@router.callback_query(lambda c: c.data == "ai_assistant")
async def activate_ai_assistant(callback: types.CallbackQuery):
    """🤖 ИИ-помощник"""
    ai_mode_users.add(callback.from_user.id)
    
    text = (
        "🤖 <b>Нейро-помощник ИиВТ ДГТУ активирован!</b>\n\n"
        "✨ <b>Задавай любой вопрос о поступлении!</b>\n\n"
        "📌 <b>Что я могу рассказать:</b>\n"
        "• 📚 О направлениях подготовки и профилях\n"
        "• 💰 О стоимости обучения и бюджетных местах\n"
        "• 📅 О днях открытых дверей и сроках подачи\n"
        "• 🏠 Об общежитиях и студенческом городке\n"
        "• 📞 Контакты приёмной комиссии и деканата"
    )
    
    photo_path = str(PHOTO_AI_LOGO) if PHOTO_AI_LOGO.exists() else None
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])
    
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

@router.callback_query(lambda c: c.data == "faq")
async def show_faq(callback: types.CallbackQuery):
    """❓ Частые вопросы"""
    text = (
        "❓ <b>Частые вопросы абитуриента</b>\n\n"
        "<i>Здесь ты найдёшь ответы на самые важные вопросы!</i>\n\n"
        "👇 <b>Выбери тему:</b>"
    )
    
    keyboard = get_faq_keyboard()
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

@router.callback_query(lambda c: c.data.startswith("faq_"))
async def show_faq_item(callback: types.CallbackQuery):
    """❓ Обработка FAQ"""
    faq_key = callback.data.replace("faq_", "")
    
    if faq_key == "scholarships":
        text = (
            "💎 <b>Стипендии в ДГТУ с 01.01.2026</b>\n\n"
            "<i>Приказ №2662-ЛС-О от 23.05.2025</i>\n\n"
            
            "🎓 <b>Гос. академическая (бакалавриат/специалитет):</b>\n"
            "• 1 курс, 1 семестр: 3 000 ₽/мес ⭐\n"
            "• На «удовл.» / задолженность: 3 000 ₽/мес ⭐\n"
            "• На «хорошо»: 3 500 ₽/мес ⭐\n"
            "• На «хорошо» и «отлично»: 4 000 ₽/мес ⭐\n"
            "• На «отлично»: 4 500 ₽/мес ⭐\n\n"
            
            "🎓 <b>Гос. академическая (магистратура):</b>\n"
            "• 1 курс, 1 семестр: 4 000 ₽/мес ⭐\n"
            "• На «хорошо»: 4 500 ₽/мес ⭐\n"
            "• На «хорошо» и «отлично»: 5 000 ₽/мес ⭐\n"
            "• На «отлично»: 5 500 ₽/мес ⭐\n\n"
            
            "🏆 <b>Повышенная академическая (с ГАС):</b>\n"
            "• 1-2 курс: 15 500 ₽/мес ⭐\n"
            "• 3 курс: 16 000 ₽/мес ⭐\n"
            "• 4-6 курс: 17 000 ₽/мес ⭐\n"
            "• Магистратура: 18 000 ₽/мес ⭐\n\n"
            
            "🏛️ <b>Стипендия Ученого совета (с ГАС):</b>\n"
            "• 1-2 курс: 15 500 ₽/мес ⭐\n"
            "• 3 курс: 16 000 ₽/мес ⭐\n"
            "• 4-6 курс: 17 000 ₽/мес ⭐\n"
            "• Магистратура: 18 000 ₽/мес ⭐\n\n"
            
            "👤 <b>Стипендия им. Л.В. Красниченко (с ГАС):</b>\n"
            "• 1-2 курс: 15 500 ₽/мес ⭐\n"
            "• 3 курс: 16 000 ₽/мес ⭐\n"
            "• 4-6 курс: 17 000 ₽/мес ⭐\n"
            "• Магистратура: 18 000 ₽/мес ⭐\n\n"
            
            "🤝 <b>Гос. социальная (ВО):</b>\n"
            "• Дети-сироты, инвалиды: 6 000 ₽/мес ⭐\n"
            "• Гос. соц. помощь: 4 000 ₽/мес ⭐\n\n"
            
            "✨ <b>Повышенная социальная (1-2 курс, с ГАС+ГСС):</b>\n"
            "• 15 500 ₽/мес ⭐\n\n"
            
            "🎓 <b>Аспиранты (технические науки):</b>\n"
            "• На «отлично»: 13 000 ₽/мес ⭐\n\n"
            
            "🎖️ <b>ВУЦ — доп. стипендия:</b>\n"
            "• 1 год: 4 000 ₽/мес ⭐\n"
            "• 2+ год на «отлично»: 9 000 ₽/мес ⭐\n"
            "• 2+ год на «хорошо»: 7 000 ₽/мес ⭐\n\n"
            
            "📍 <b>Контакты:</b>\n"
            "📞 +7 (863) 273-86-27\n"
            "📧 spu-46@donstu.ru"
        )
        
        keyboard = get_back_keyboard()
        photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
        await send_photo_message(callback, text, keyboard, photo_path)
        await safe_callback_answer(callback)
        return
    
    kb = rag_service.knowledge_base.get("faq", {})
    for key, data in kb.items():
        if key == faq_key:
            answer = _clean_html(data["answer"])
            keyboard = get_back_keyboard()
            photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
            await send_photo_message(callback, answer, keyboard, photo_path)
            await safe_callback_answer(callback)
            return
    await callback.answer("ℹ️ Информация уточняется")

@router.callback_query(lambda c: c.data == "open_days")
async def show_open_days(callback: types.CallbackQuery):
    """📅 Дни открытых дверей"""
    open_days = rag_service.knowledge_base.get("open_days", {})
    text = (
        "📅 <b>Дни открытых дверей ИиВТ ДГТУ:</b>\n\n"
        f"🗓️ <b>ДГТУ:</b> {open_days.get('dstu', '5 апреля 2026')}\n"
        f"🗓️ <b>ИиВТ:</b> {open_days.get('iivt', '18 апреля 2026')}\n\n"
        "🎉 <b>Приходите! Мы расскажем о всех направлениях!</b>\n\n"
        "<i>✨ Вход свободный для всех желающих!</i>"
    )
    
    keyboard = get_open_days_keyboard()
    photo_path = str(PHOTO_CLOCK) if PHOTO_CLOCK.exists() else str(PHOTO_DGTU_LOGO)
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

@router.callback_query(lambda c: c.data == "reminder_set")
async def set_reminder(callback: types.CallbackQuery):
    """🔔 Установка напоминания"""
    text = "🔔 <b>Напоминание установлено!</b>\n\n📅 5 апреля — ДГТУ\n📅 18 апреля — ИиВТ"
    keyboard = get_back_keyboard()
    photo_path = str(PHOTO_CLOCK) if PHOTO_CLOCK.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

@router.callback_query(lambda c: c.data == "reminder_skip")
async def skip_reminder(callback: types.CallbackQuery):
    """⏭️ Пропуск напоминания"""
    text = "✅ Хорошо! Заходите снова."
    keyboard = get_back_keyboard()
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

# ============================================================================
# 📚 НАПРАВЛЕНИЯ С ПАГИНАЦИЕЙ
# ============================================================================

@router.callback_query(lambda c: c.data == "programs")
async def show_programs(callback: types.CallbackQuery):
    """📚 Направления подготовки (страница 0)"""
    await show_programs_page(callback, 0)

@router.callback_query(lambda c: c.data.startswith("programs_page_"))
async def show_programs_page(callback: types.CallbackQuery, page: int = None):
    """📚 Направления подготовки с пагинацией и кэшем"""
    
    if page is None:
        page = int(callback.data.split("_")[-1])
    
    user_id = callback.from_user.id
    
    programs = data_cache.get("programs_list")
    if programs is None:
        programs = [
            {"code": "01.03.04", "name": "Прикладная математика"},
            {"code": "02.03.03", "name": "Математическое обеспечение"},
            {"code": "09.03.01", "name": "Информатика и ВТ"},
            {"code": "09.03.02", "name": "Информационные системы (ИСТ)"},
            {"code": "09.03.02", "name": "Искусственный интеллект (AI)"},
            {"code": "09.03.02", "name": "Web-разработка (WEB)"},
            {"code": "09.03.02", "name": "Инф. системы (заочное)"},
            {"code": "09.03.03", "name": "Прикладная информатика"},
            {"code": "09.03.03", "name": "Прикл. информатика (заочное)"},
            {"code": "09.03.04", "name": "Программная инженерия"},
            {"code": "10.03.01", "name": "Информационная безопасность"},
            {"code": "10.05.01", "name": "Компьютерная безопасность (спец)"},
            {"code": "10.05.02", "name": "Инф. безопасность (спец)"},
        ]
        data_cache.set("programs_list", programs, ttl=600)
    
    old_msg_id = user_last_message.get(user_id)
    if old_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=old_msg_id)
        except:
            pass
    
    text = (
        "📚 <b>Направления подготовки ИиВТ ДГТУ:</b>\n\n"
        "<i>🎯 4 направления, 13 образовательных профилей</i>\n\n"
        f"<b>💡 Страница {page+1} из 4</b>\n"
        "<b>Выбери направление 👇</b>"
    )
    
    keyboard = get_programs_keyboard(page)
    
    # 🔥 ЕДИНОЕ ФОТО — ВСЕГДА ОДНО И ТО ЖЕ
    photo_path = str(PHOTO_BUILDING) if PHOTO_BUILDING.exists() else None
    
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

@router.callback_query(lambda c: c.data.startswith("program_"))
async def show_program_details(callback: types.CallbackQuery):
    """📚 Информация о направлении"""
    program_code = callback.data.replace("program_", "")
    context = rag_service._search_by_code(program_code)
    
    if context:
        text = _clean_html(context)
        if program_code.startswith("09.03."):
            text += "\n\n━━━━━━━━━━━━━━━\n"
            text += "<b>💡 477* бюджетных мест</b>\n"
            text += "на все направления 09.xx.xx!"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ К списку направлений", callback_data="programs")],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
        ])
    else:
        program_names = {
            "01.03.04": "Прикладная математика",
            "02.03.03": "Математическое обеспечение",
            "09.03.01": "Информатика и ВТ",
            "09.03.02_ist": "Информационные системы (ИСТ)",
            "09.03.02_ai": "Искусственный интеллект (AI)",
            "09.03.02_web": "Web-разработка (WEB)",
            "09.03.02_zaoch": "Инф. системы (заочное)",
            "09.03.03": "Прикладная информатика",
            "09.03.03_zaoch": "Прикл. информатика (заочное)",
            "09.03.04": "Программная инженерия",
            "10.03.01": "Информационная безопасность",
            "10.05.01": "Компьютерная безопасность (спец)",
            "10.05.02": "Инф. безопасность (спец)"
        }
        name = program_names.get(program_code, program_code)
        text = f"<b>📚 {name}</b>\n\nℹ️ <b>Информация уточняется</b>\n\n🔗 <a href='https://donstu.ru'>donstu.ru</a>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ К списку направлений", callback_data="programs")],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
        ])
    
    photo_path = str(PHOTO_BUILDING) if PHOTO_BUILDING.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

@router.callback_query(lambda c: c.data == "noop")
async def handle_noop(callback: types.CallbackQuery):
    """⚡ Пустой callback для кнопок страницы"""
    await callback.answer()

# ============================================================================
# 👥 РУКОВОДСТВО
# ============================================================================

@router.callback_query(lambda c: c.data == "leadership")
async def show_leadership(callback: types.CallbackQuery):
    """👥 Руководство"""
    text = "👥 <b>Руководящий состав факультета ИиВТ:</b>"
    
    keyboard = get_leadership_keyboard()
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

@router.callback_query(lambda c: c.data == "dean")
async def show_dean(callback: types.CallbackQuery):
    """👤 Декан"""
    text = (
        "👤 <b>Декан факультета ИиВТ</b>\n\n"
        "<b>Панфилов Иван Александрович</b>\n\n"
        "📍 <b>Адрес:</b>\n"
        "г. Ростов-на-Дону, пл. Гагарина, 1, каб. 1-346"
    )
    
    keyboard = get_back_keyboard()
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

@router.callback_query(lambda c: c.data == "deputies")
async def show_deputies(callback: types.CallbackQuery):
    """👥 Заместители декана"""
    text = (
        "👥 <b>Заместители декана ИиВТ</b>\n\n"
        "👤 <b>Бедоидзе Мария Васильевна</b>\n"
        "Заместитель декана по учебной работе\n\n"
        
        "👤 <b>Токарев Павел Викторович</b>\n"
        "Заместитель декана по проектной деятельности и общим вопросам\n\n"
        
        "👤 <b>Климова Елена Николаевна</b>\n"
        "Заместитель декана по воспитательной работе\n\n"
        "📍 каб. 1-347а, 📞 +7 (863) 273-86-27"
    )
    
    keyboard = get_back_keyboard()
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

@router.callback_query(lambda c: c.data == "contacts")
async def show_contacts(callback: types.CallbackQuery):
    """📞 Контакты"""
    university = rag_service.knowledge_base.get("university", {})
    text = (
        f"📞 <b>Контакты приёмной комиссии:</b>\n\n"
        f"📍 {university.get('address', 'пл. Гагарина, 1')}\n"
        f"📞 {university.get('phone', '+7 (863) 273-85-31')}\n"
        f"🌐 {university.get('website', 'donstu.ru')}"
    )
    
    keyboard = get_back_keyboard()
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

# ============================================================================
# ℹ️ О БОТЕ — КРАСИВОЕ ОФОРМЛЕНИЕ
# ============================================================================

@router.callback_query(lambda c: c.data == "about_bot")
async def about_bot(callback: types.CallbackQuery):
    """ℹ️ О боте — КРАСИВОЕ ОФОРМЛЕНИЕ"""
    config = Config()
    cache_stats = data_cache.get_stats()
    
    text = (
        "🤖 <b>ИиВТ ДГТУ Помощник</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "✨ <b>Твой персональный помощник для поступления!</b>\n\n"
        
        "📌 <b>ВОЗМОЖНОСТИ БОТА:</b>\n\n"
        
        "📚 <b>13 направлений подготовки</b>\n"
        "   • Полная информация о всех профилях\n"
        "   • Проходные баллы 2025\n"
        "   • Количество бюджетных мест\n"
        "   • Стоимость обучения\n\n"
        
        "🧮 <b>Калькулятор баллов ЕГЭ</b>\n"
        "   • Рассчитай свои шансы\n"
        "   • Сравнение с проходными\n"
        "   • Запас/недостача баллов\n\n"
        
        "📋 <b>Чек-лист абитуриента</b>\n"
        "   • 8 важных задач\n"
        "   • Интерактивные кнопки\n"
        "   • Сохранение прогресса\n\n"
        
        "🎯 <b>Тест на выбор направления</b>\n"
        "   • 5 вопросов о предпочтениях\n"
        "   • Анализ интересов\n"
        "   • Рекомендация профиля\n\n"
        
        "🤖 <b>ИИ-помощник (GigaChat)</b>\n"
        "   • Ответы 24/7 за 3 секунды\n"
        "   • Официальные данные ДГТУ\n"
        "   • Понимает естественный язык\n\n"
        
        "🔍 <b>Умный поиск</b>\n"
        "   • Быстрый поиск информации\n"
        "   • По ключевым словам\n"
        "   • Команда /search\n\n"
        
        "📅 <b>Дни открытых дверей</b>\n"
        "   • 5 апреля 2026 — ДГТУ\n"
        "   • 18 апреля 2026 — ИиВТ\n"
        "   • Напоминания\n\n"
        
        "💰 <b>Стипендии 2026</b>\n"
        "   • Актуальные размеры\n"
        "   • Все виды стипендий\n"
        "   • Приказ №2662-ЛС-О\n\n"
        
        "📞 <b>Связь с волонтёром</b>\n"
        "   • Ответ за 15 минут\n"
        "   • Живое общение\n"
        "   • Рабочее время: 10:00-18:00\n\n"
        
        "🎖️ <b>ВУЦ</b>\n"
        "   • Информация о военном центре\n"
        "   • Длительность обучения\n"
        "   • Контакты\n\n"
        
        "👥 <b>Руководство факультета</b>\n"
        "   • Декан и заместители\n"
        "   • Контакты\n"
        "   • Кабинеты\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        
        "⚠️ <b>Бот в разработке!</b>\n"
        "Нашёл ошибку? Пиши: @sabelnikovr\n\n"
        
        f"👨‍💻 <b>Разработчик:</b> {config.BOT_AUTHOR}\n"
        "📅 <b>2026 ИиВТ ДГТУ</b>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])
    
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

# ============================================================================
# 💬 ОБРАТНАЯ СВЯЗЬ
# ============================================================================

@router.callback_query(lambda c: c.data.startswith("feedback_"))
async def handle_feedback(callback: types.CallbackQuery):
    """💬 Обратная связь"""
    from models.database import db
    from services.cache_service import cache
    import time
    
    user_id = callback.from_user.id
    
    if callback.data == "feedback_good":
        # 👍 Положительный отзыв
        await db.add_feedback(user_id, "👍")
        
        # Сохраняем в кэш
        await cache.set(f"feedback:{user_id}:{int(time.time())}", {
            "rating": 5,
            "type": "button_good"
        })
        
        logger.info(f"💬  Отзыв от пользователя {user_id}")
        
        await callback.answer("👍 Спасибо!")
        text = "👍 <b>Спасибо за отзыв!</b>"
        
    elif callback.data == "feedback_bad":
        # 👎 Негативный — спрашиваем причину
        await callback.answer()
        text = "❓ <b>Что не так?</b>"
        keyboard = get_feedback_reason_keyboard()
        photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
        await send_photo_message(callback, text, keyboard, photo_path)
        return
    
    elif callback.data == "feedback_text":
        # 💬 Текстовый отзыв из /changelog
        await callback.answer()
        text = (
            "💬 <b>Напиши свой отзыв:</b>\n\n"
            "✍️ <b>Просто отправь текст сообщения</b>\n"
            "Я перешлю его разработчику!"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="show_main_menu")]
        ])
        await send_photo_message(callback, text, keyboard, None)
        
        # Устанавливаем режим ожидания отзыва
        user_last_message[user_id] = {"mode": "waiting_feedback_text"}
        return
        
    elif callback.data == "feedback_cancel":
        await callback.answer("Отмена")
        text = "👋 <b>Главное меню</b>"
        
    elif callback.data.startswith("feedback_reason_"):
        # Причина негатива
        reason = callback.data.replace("feedback_reason_", "")
        await db.add_feedback(user_id, f"👎 {reason}")
        
        # Сохраняем в кэш
        await cache.set(f"feedback_reason:{reason}", {
        "reason": reason,
        "count": 1
    })  # ✅ Без ttl
        
        logger.info(f"💬 👎 Негатив: {reason} от пользователя {user_id}")
        
        await callback.answer("💬 Спасибо!")
        text = "✅ <b>Отправлено! Мы учтём твоё мнение.</b>"
    else:
        return
    
    keyboard = get_back_keyboard()
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

# ============================================================================
# 🎖️ ВУЦ
# ============================================================================

@router.callback_query(lambda c: c.data == "vuts")
async def show_vuts(callback: types.CallbackQuery):
    """🎖️ ВУЦ — Военный Учебный Центр"""
    text = (
         "🎖️ <b>Военный Учебный Центр (ВУЦ)</b>\n\n"
        
        "📚 <b>Длительность обучения:</b>\n"
        "• <b>Офицер:</b> 2.5 года\n"
        "• <b>Сержант:</b> 2 года\n"
        "• <b>Солдат:</b> 1.5 года\n\n"
        
        "📌 <b>Важно:</b>\n"
        "• Студенты обучаются на своих специальностях и направлениях\n"
        "• Посещение ВУЦ — 1 раз в неделю\n"
        "• После выпуска считаются отслужившими срочную службу\n"
        "• Получают военный билет\n"
        "• <b>Не получают стипендию в ВУЦ</b>\n"
        "• Оценки в ВУЦ <b>НЕ влияют</b> на стипендию в ДГТУ\n\n"
        
        "📅 <b>Сбор документов:</b>\n"
        "• <b>Офицеры запаса:</b> с сентября 2-го курса\n"
        "• <b>Солдаты, сержанты запаса:</b> с февраля 2-го курса\n\n"
        
        "🎓 <b>Программа кадровых офицеров:</b>\n"
        "• Со стипендией и последующей службой\n"
        
        "💡 <b>Право на обучение:</b>\n"
        "Студенты <b>ВСЕХ</b> направлений факультета!\n\n"
        
        "📍 <b>Контакты:</b>\n"
        "📞 +7 (863) 258-92-89"
    )
    
    keyboard = get_back_keyboard()
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await safe_callback_answer(callback)

# ============================================================================
# 🏛️ КАФЕДРЫ
# ============================================================================

@router.callback_query(lambda c: c.data == "departments")
async def show_departments(callback: types.CallbackQuery):
    """🏛️ Кафедры факультета"""
    text = (
        "🏛️ <b>Кафедры факультета ИиВТ</b>\n\n"
        "📌 <b>6 кафедр готовят специалистов:</b>\n\n"
        "1️⃣ <b>Высшая математика</b>\n"
        "   • 01.03.04 Прикладная математика\n\n"
        "2️⃣ <b>Программное обеспечение</b>\n"
        "   • 02.03.03 Мат. обеспечение\n"
        "   • 09.03.04 Программная инженерия\n\n"
        "3️⃣ <b>Кибербезопасность</b> (ФСБ, ФСТЭК)\n"
        "   • 10.05.01 Комп. безопасность\n\n"
        "4️⃣ <b>Информационные технологии</b>\n"
        "   • 09.03.01 Информатика и ВТ\n"
        "   • 09.03.02 ИСТ/AI/WEB\n\n"
        "5️⃣ <b>Информ. безопасность</b>\n"
        "   • 10.03.01, 10.05.02\n\n"
        "6️⃣ <b>Математика и информатика</b>\n"
        "   • 09.03.02 ИИ\n"
        "   • 09.03.03 Прикладная информатика"
    )
    
    keyboard = get_departments_keyboard()
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("dept_"))
async def show_department_details(callback: types.CallbackQuery):
    """🏛️ Детали кафедры"""
    dept_data = {
        "dept_math": {
            "name": "Высшая математика",
            "programs": "01.03.04 Прикладная математика",
            "description": "Кафедра готовит специалистов в области применения математических методов к решению инженерных и экономических задач."
        },
        "dept_software": {
            "name": "Программное обеспечение вычислительной техники",
            "programs": "02.03.03 Мат. обеспечение, 09.03.04 Программная инженерия",
            "description": "Кафедра готовит специалистов в области разработки программного обеспечения, больших данных и машинного обучения."
        },
        "dept_cyber": {
            "name": "Кибербезопасность информационных систем",
            "programs": "10.05.01 Компьютерная безопасность",
            "description": "Кафедра готовит специалистов в области защиты информации под кураторством ФСБ и ФСТЭК."
        },
        "dept_it": {
            "name": "Информационные технологии",
            "programs": "09.03.01, 09.03.02 (ИСТ/AI/WEB)",
            "description": "Кафедра готовит специалистов в области информационных систем, web-технологий и ИТ."
        },
        "dept_security": {
            "name": "Информационная безопасность в вычислительных системах",
            "programs": "10.03.01, 10.05.02",
            "description": "Кафедра готовит специалистов по защите автоматизированных систем и телекоммуникационных сетей."
        },
        "dept_math_info": {
            "name": "Математика и информатика",
            "programs": "09.03.02 ИИ, 09.03.03 Прикладная информатика",
            "description": "Кафедра готовит специалистов в области искусственного интеллекта, прикладной информатики и математического моделирования."
        }
    }
    
    dept_key = callback.data
    dept = dept_data.get(dept_key, {})
    
    text = (
        f"🏛️ <b>{dept.get('name', 'Кафедра')}</b>\n\n"
        f"📚 <b>Направления:</b>\n{dept.get('programs', '—')}\n\n"
        f"📝 <b>Описание:</b>\n{dept.get('description', '—')}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К кафедрам", callback_data="departments")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
    ])
    
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await callback.answer()

# ============================================================================
# 🏆 ДОСТИЖЕНИЯ
# ============================================================================

@router.callback_query(lambda c: c.data == "achievements")
async def show_achievements(callback: types.CallbackQuery):
    """🏆 Достижения факультета"""
    text = (
        "🏆 <b>Достижения факультета ИиВТ</b>\n\n"
        "🎉 <b>Хакатон Осень 2025:</b>\n"
        "• Jacobs Kolpak — победители\n"
        "• input math — победили в кейсе\n"
        "• Слоныри — Приз зрительских симпатий\n\n"
        "🛡️ <b>Cyber Garden Hardware:</b>\n"
        "• 2-е место — кейс РНИИРС\n\n"
        "🔒 <b>DDoS-Guard 2025:</b>\n"
        "• 1 место — SecureOne (NOC)\n"
        "• 2 место — Роскомнадзор (DevOps)\n\n"
        "🎯 <b>Приоритет 2030:</b>\n"
        "• Участие во всех стратегических проектах\n"
        "• ДонТех — центр технологического развития"
    )
    
    keyboard = get_achievements_keyboard()
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("ach_"))
async def show_achievement_details(callback: types.CallbackQuery):
    """🏆 Детали достижений"""
    ach_data = {
        "ach_hackathon": {
            "title": "🏆 Хакатон Осень 2025",
            "description": (
                "<b>Победители:</b>\n"
                "• Jacobs Kolpak и Digital Hustle (ДГТУ) — победители от генерального партнера ПАО КБ «Центр-инвест»\n"
                "• input math (ДГТУ) — победили в кейсе партнера «Ахеникс»\n"
                "• Слоныри (ДГТУ) — завоевали Приз зрительских симпатий"
            )
        },
        "ach_cyber": {
            "title": "🛡️ Cyber Garden Hardware",
            "description": "<b>2-е место</b> — кейс от ФГУП РНИИРС"
        },
        "ach_ddos": {
            "title": "🔒 DDoS-Guard 2025!",
            "description": (
                "<b>Результаты:</b>\n"
                "• 1 место в кейсе «NOC» — команда «SecureOne»\n"
                "• 2 место в кейсе «DevOps» — команда «Роскомнадзор»"
            )
        },
        "ach_priority": {
            "title": "🎯 Приоритет 2030",
            "description": (
                "<b>Участие во всех стратегических проектах:</b>\n"
                "• ДонТех — создание центра технологического развития для цифровизации и автоматизации\n"
                "• Единое здоровье — система прогнозирования и контроля рисков\n"
                "• Интеллектуальные материалы — разработка «умных» материалов"
            )
        }
    }
    
    ach_key = callback.data
    ach = ach_data.get(ach_key, {})
    
    text = f"{ach.get('title', '🏆 Достижение')}\n\n{ach.get('description', '—')}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К достижениям", callback_data="achievements")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
    ])
    
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await callback.answer()

# ============================================================================
# 🔍 УМНЫЙ ПОИСК — ИСПРАВЛЕННЫЙ
# ============================================================================

@router.callback_query(lambda c: c.data == "smart_search_btn")
async def smart_search_btn(callback: types.CallbackQuery):
    """🔍 Кнопка умного поиска"""
    user_id = callback.from_user.id
    
    old_msg_id = user_last_message.get(user_id)
    if old_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=old_msg_id)
        except:
            pass
    
    text = (
        "🔍 <b>Умный поиск по базе знаний</b>\n\n"
        "📝 <b>Напиши свой вопрос:</b>\n"
        "• Общежитие и студенческий городок 🏠\n"
        "• Стоимость обучения и бюджетные места 💰\n"
        "• Проходные баллы ЕГЭ 2025 📊\n"
        "• Стипендии и материальная помощь 💎\n"
        "• Дни открытых дверей и сроки подачи 📅\n"
        "• Документы для поступления 📄\n"
        "• Контакты приёмной комиссии 📞\n\n"
        "💡 <b>Или используй команду:</b>\n"
        "<code>/search твой вопрос</code>"
    )
    
    try:
        new_msg = await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
        user_last_message[user_id] = new_msg.message_id
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    await callback.answer()

@router.message(Command("search"))
async def cmd_search(message: types.Message):
    """🔍 Умный поиск — команда"""
    # 🔥 DEBUG — ПРОВЕРКА
    print(f"🔥 ФУНКЦИЯ cmd_search ВЫЗВАНА!")
    print(f"🔥 Текст сообщения: {message.text}")
    print(f"🔥 Количество слов: {len(message.text.split())}")
    
    # 🔥 Если есть запрос после /search — запускаем поиск
    if len(message.text.split()) > 1:
        query = message.text.replace("/search", "").strip()
        print(f"🔥 Запрос: {query}")
        logger.info(f"🔍 Запрос поиска: '{query}'")
        await process_smart_search(message, query)
        return
    
    
    # 🔥 Если запроса нет — показываем подсказки
    text = (
        "🔍 <b>Умный поиск</b>\n\n"
        "📝 <b>Примеры:</b>\n"
        "• <code>/search общежитие</code>\n"
        "• <code>/search стоимость</code>\n"
        "• <code>/search баллы</code>\n"
        "• <code>/search документы</code>"
    )
    await message.answer(text, parse_mode="HTML")

async def process_smart_search(message: types.Message, query: str):
    """🔍 Обработка умного поиска"""
    
    # 🔥 ОТЛАДКА
    print(f"\n🔥 ===== ПОИСК =====")
    print(f"🔥 Исходный запрос: '{query}'")
    
    original_query = query
    query = normalize_search_query(query)
    
    print(f"🔥 После нормализации: '{query}'")
    
    query_lower = query.lower().strip()
    query_words = set(query_lower.split())
    
    print(f"🔥 query_lower: '{query_lower}'")
    print(f"🔥 query_words: {query_words}")
    
    # ... дальше идёт старый код с keywords_map ...    
    
    try:
         # 🔥 МАППИНГ: категории поиска → ключи FAQ (чтобы искать только нужное)
        CATEGORY_TO_FAQ = {
            "общежит": ["dormitory"],
            "балл": ["passing_scores"],
            "стоим": ["cost"],
            "стипенд": ["scholarships"],
            "срок": ["deadlines"],
            "документ": ["documents"],
            "контакт": ["contacts"],
            "вуц": ["vuts"],
            "кафедр": ["departments"],
            "достижен": ["achievements"],
        }
        keywords_map = {
            "балл": ["балл", "баллы", "егэ", "проходной", "проходные", "минимум", "порог", "сумма", "177", "193", "205", "210", "198", "188", "187"],
            "стипенд": ["стипенд", "выплата", "академическая", "социальная", "повышенная", "денег", "гас", "гсс", "3000", "4000", "15500", "6000"],
            "общежит": ["общежитие", "общага", "жильё", "студгородок", "комната", "место", "поселение", "заселение", "нагибина", "5"],
            "стоим": ["стоимость", "цена", "платно", "контракт", "договор", "обучение", "платёж", "оплата", "руб", "тыс", "153300", "135000", "55000"],
            "документ": ["документ", "паспорт", "аттестат", "снилс", "фото", "копия", "оригинал", "подач", "приём", "заявлен"],
            "срок": ["срок", "дата", "дедлайн", "приём", "зачисление", "подача", "август", "июль", "июнь", "20 июня", "1 августа", "календарь"],
            "контакт": ["контакт", "телефон", "адрес", "почта", "связь", "email", "декана", "приёмн", "комисс", "гагарина", "273-86"],
            "вуц": ["вуц", "военн", "кафедра", "армия", "военный", "служба", "учебн", "центр", "отсрочк", "билет", "офицер", "сержант"],
            "кафедр": ["кафедр", "кафедра", "высшая математика", "программное обеспечение", "кибербезопасность", "информационные технологии"],
            "достижен": ["достижен", "хакатон", "победа", "приоритет", "ddos", "cyber garden"],
        }
        
        matched_category = None
        best_match_count = 0
        
        for category, keywords in keywords_map.items():
            match_count = sum(1 for kw in keywords if kw in query_lower)
            match_count += sum(1 for word in query_words if any(kw in word or word in kw for kw in keywords))
            
            if match_count > best_match_count:
                best_match_count = match_count
                matched_category = category
        
        # 🔥 ОТЛАДКА: покажи что нашли
        print(f"🔥 matched_category: {matched_category}")
        print(f"🔥 best_match_count: {best_match_count}")
        
        if matched_category and best_match_count >= 1:
            kb = rag_service.knowledge_base.get("faq", {})
            
            # 🔥 Получаем релевантные ключи FAQ для этой категории
            relevant_keys = CATEGORY_TO_FAQ.get(matched_category, [])
            
            found_results = []
            
            for key, data in kb.items():
                # 🔥 Если есть привязка к категории — ищем ТОЛЬКО в ней!
                if relevant_keys and key not in relevant_keys:
                    continue  # ← Пропускаем нерелевантные вопросы
                
                answer_text = data.get("answer", "").lower()
                question_text = data.get("question", "").lower()
                category_keywords = keywords_map[matched_category]
                
                # Считаем совпадения
                match_count = sum(1 for kw in category_keywords if kw in answer_text or kw in question_text)
                match_count += sum(1 for word in query_words if word in answer_text or word in question_text)
                
                if match_count >= 1:
                    found_results.append((key, data, match_count))
            
            found_results.sort(key=lambda x: x[2], reverse=True)
            
            if found_results:
                text = f"🔍 <b>Результаты по запросу:</b> <i>{query}</i>\n\n"
                
                # 🔥 Показываем ТОЛЬКО ТОП-1 результат (самый релевантный)
                for key, data, count in found_results[:1]:
                    title = data.get("question", key)
                    answer = _clean_html(data.get("answer", ""))[:500]
                    if len(data.get("answer", "")) > 500:
                        answer += "..."
                    text += f"📌 <b>{title}</b>\n{answer}\n\n"
                
                text += "<i>💡 Выбери раздел в меню для полной информации</i>"
                await send_single_message(message, text, reply_markup=get_back_keyboard())
                return
        
        await message.answer(
            f"⚠️ <b>Точного ответа не найдено</b>\n\n"
            f"💡 <b>Но я могу помочь:</b>\n"
            f"• 🤖 <b>Спроси ИИ-помощника:</b> нажми '🤖 ИИ-помощник'\n"
            f"• ❓ <b>Посмотри FAQ:</b> нажми '❓ Часто задаваемые вопросы'\n"
            f"• 📞 <b>Спроси волонтёра:</b> нажми '📞 Волонтёр'",
            reply_markup=get_back_keyboard()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка поиска: {e}")
        await message.answer("⚠️ <b>Ошибка поиска</b>", reply_markup=get_back_keyboard())

# ============================================================================
# 📞 СВЯЗЬ С ВОЛОНТЁРОМ — ИСПРАВЛЕННЫЙ
# ============================================================================

@router.callback_query(lambda c: c.data == "help_volunteer")
async def help_volunteer(callback: types.CallbackQuery):
    """📞 Связь с волонтёром"""
    user_id = callback.from_user.id
    
    old_msg_id = user_last_message.get(user_id)
    if old_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=old_msg_id)
        except:
            pass
    
    text = (
        "📞 <b>Связь с волонтёром-студентом</b>\n\n"
        "💬 <b>Напиши свой вопрос:</b>\n"
        "• По предметам ЕГЭ?\n"
        "• Какое направление?\n"
        "• Что именно хочешь узнать?\n\n"
        "⏱️ <b>Ответим в течение 15 минут!</b>\n"
        "🕐 Рабочее время: 10:00-18:00"
    )
    
    try:
        new_msg = await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
        user_last_message[user_id] = {"mode": "waiting_volunteer", "msg_id": new_msg.message_id}
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ============================================================================
# 🔧 РЕЖИМ ВОЛОНТЁРА (АДМИН)
# ============================================================================

@router.message(Command("volunteer"))
async def volunteer_mode(message: types.Message):
    """🔧 Включить режим волонтёра (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ <b>Доступ только для администратора</b>", reply_markup=get_back_keyboard())
        return
    
    volunteer_mode_users[message.from_user.id] = True
    
    text = (
        "✅ <b>Режим волонтёра включён!</b>\n\n"
        "📌 <b>Теперь ты будешь получать вопросы от абитуриентов.</b>\n\n"
        "💡 <b>Как отвечать:</b>\n"
        "1. Абитуриент пишет вопрос → ты получаешь уведомление\n"
        "2. Отвечаешь ЧЕРЕЗ REPLY на это сообщение\n"
        "3. Ответ автоматически отправляется абитуриенту\n\n"
        "❌ <b>Для отключения:</b> /stop_volunteer"
    )
    
    await message.answer(text, reply_markup=get_back_keyboard())

@router.message(Command("stop_volunteer"))
async def stop_volunteer_mode(message: types.Message):
    """🔧 Выключить режим волонтёра"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ <b>Доступ только для администратора</b>", reply_markup=get_back_keyboard())
        return
    
    volunteer_mode_users.pop(message.from_user.id, None)
    
    text = "❌ <b>Режим волонтёра выключен</b>"
    await message.answer(text, reply_markup=get_back_keyboard())

# ============================================================================
# 🧮 КАЛЬКУЛЯТОР ЕГЭ — ИСПРАВЛЕННЫЙ
# ============================================================================

@router.callback_query(lambda c: c.data == "calculator_btn")
async def calculator_from_button(callback: types.CallbackQuery):
    """🧮 Калькулятор баллов ЕГЭ"""
    text = "🧮 <b>Калькулятор баллов ЕГЭ</b>\n\n💡 <b>Минимум:</b>\n• Математика: 44 • Русский: 40 • Информатика/Физика: 44"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📐 Мат + 📝 Рус + 💻 Инф", callback_data="calc_start")],
        [InlineKeyboardButton(text="📐 Мат + 📝 Рус + ⚛️ Физ", callback_data="calc_start_physics")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
    ])
    
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await callback.answer()

@router.callback_query(lambda c: c.data in ["calc_start", "calc_start_physics"])
async def calc_start_input(callback: types.CallbackQuery):
    """🧮 Ввод баллов"""
    text = "🧮 <b>Ввод:</b>\n\n📝 <b>Отправь 3 числа:</b>\n<code>85 78 92</code>"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]])
    
    photo_path = str(PHOTO_DGTU_LOGO) if PHOTO_DGTU_LOGO.exists() else None
    await send_photo_message(callback, text, keyboard, photo_path)
    await callback.answer()
    user_last_message[callback.from_user.id] = {"mode": "waiting_scores"}

@router.message(lambda msg: msg.text and msg.text.strip().replace(' ', '').isdigit() and len(msg.text.strip().split()) == 3)
async def process_scores_input(message: types.Message):
    """🧮 Обработка баллов"""
    user_id = message.from_user.id
    user_data = user_last_message.get(user_id, {})
    
    if user_data.get("mode") != "waiting_scores":
        return
    
    try:
        scores = message.text.strip().split()
        math, russian, third = int(scores[0]), int(scores[1]), int(scores[2])
        total = math + russian + third
        
        programs_info = [
            {"code": "01.03.04", "name": "Прикладная математика", "pass": 177, "budget": 50, "form": "очная"},
            {"code": "02.03.03", "name": "Математическое обеспечение", "pass": 193, "budget": 75, "form": "очная"},
            {"code": "09.03.01", "name": "Информатика и ВТ", "pass": 205, "budget": 477, "form": "очная"},
            {"code": "09.03.02_ist", "name": "Информационные системы (ИСТ)", "pass": 201, "budget": 477, "form": "очная"},
            {"code": "09.03.02_ai", "name": "Искусственный интеллект (AI)", "pass": 205, "budget": 477, "form": "очная"},
            {"code": "09.03.02_web", "name": "Web-разработка (WEB)", "pass": 210, "budget": 477, "form": "очная"},
            {"code": "09.03.03", "name": "Прикладная информатика", "pass": 205, "budget": 477, "form": "очная"},
            {"code": "09.03.04", "name": "Программная инженерия", "pass": 205, "budget": 477, "form": "очная"},
            {"code": "10.03.01", "name": "Информационная безопасность", "pass": 210, "budget": 42, "form": "очная"},
            {"code": "10.05.01", "name": "Компьютерная безопасность (спец)", "pass": 198, "budget": 150, "form": "очная"},
            {"code": "10.05.02", "name": "Инф. безопасность (спец)", "pass": 198, "budget": 150, "form": "очная"},
            {"code": "09.03.02_zaoch", "name": "Инф. системы (заочное)", "pass": 188, "budget": 30, "form": "заочная"},
            {"code": "09.03.03_zaoch", "name": "Прикл. информатика (заочное)", "pass": 187, "budget": 30, "form": "заочная"},
        ]
        
        text = f"🎯 <b>Результат:</b>\n📐 Мат: {math}\n📝 Рус: {russian}\n📊 3-й: {third}\n✨ <b>Итого: {total}</b>\n\n"
        ochna = [p for p in programs_info if p["form"] == "очная" and "спец" not in p["name"]]
        
        if ochna:
            text += "<b>🎓 Бакалавриат:</b>\n"
            for prog in ochna:
                if total >= prog["pass"]:
                    status, diff_text = "✅", f"+{total - prog['pass']}"
                else:
                    status, diff_text = "❌", f"-{prog['pass'] - total}"
                budget_text = f"{prog['budget']}*" if prog['budget'] == 477 else prog['budget']
                text += f"{status} <b>{prog['name']}</b>\n   Проходной: {prog['pass']} | Ты: {diff_text} | Бюджет: {budget_text}\n\n"
            text += "<i>💡 477* — на все 09.xx.xx</i>\n\n"
        
        text += "<i>💡 Проходные ориентировочные!</i>"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧮 Ещё раз", callback_data="calculator_btn")],
            [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
        ])
        
        await send_single_message(message, text, reply_markup=keyboard)
        await message.delete()
        user_last_message[user_id] = {}
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await message.answer("⚠️ <b>Ошибка!</b>\nОтправь: <code>85 78 92</code>", parse_mode="HTML", reply_markup=get_back_keyboard())



# ============================================================================
# 🔥 ИИ + ВОЛОНТЁР — ОБРАБОТКА ТЕКСТА (РЕЖИМ 1 СООБЩЕНИЯ + REPLY)
# ============================================================================

@router.message(lambda msg: msg.text and not msg.text.startswith('/'))
async def handle_text(message: types.Message):
    """🔥 Обработка текстовых сообщений"""
    
    user_id = message.from_user.id
    
    # ========================================================================
    # 💬 ОБРАБОТКА ТЕКСТОВОГО ОТЗЫВА (после feedback_text)
    # ========================================================================
    user_data = user_last_message.get(user_id, {})
    if isinstance(user_data, dict) and user_data.get("mode") == "waiting_feedback_text":
        # Пользователь написал отзыв текстом
        feedback_text = message.text
        
        # Сохраняем в кэш
        from services.cache_service import cache
        import time
        await cache.set(f"feedback:{user_id}:{int(time.time())}", {
            "user_id": user_id,
            "text": feedback_text,
            "type": "text_from_button",
            "timestamp": time.time()
        })
        
        # Логируем
        logger.info(f"💬 ТЕКСТОВЫЙ ОТЗЫВ от {user_id}: {feedback_text[:100]}")
        
        
        try:
            await message.bot.send_message(
                ADMIN_ID,
                f"💬 <b>Текстовый отзыв</b>\n\n"
                f"👤 От: {message.from_user.first_name} (ID: {user_id})\n"
                f"💬 Текст: {feedback_text}"
            )
        except:
            pass
        
        await message.answer(
            "✅ <b>Спасибо за отзыв!</b>\n\n"
            "💙 Твоё мнение помогает сделать бота лучше!"
        )
        
        # Сбрасываем режим
        user_last_message[user_id] = {}
        return
    

    # ========================================================================
    # 💬 АВТО-ОТВЕТЫ (ПРОВЕРЯЕМ ПЕРВЫМ!)
    # ========================================================================
    message_lower = message.text.lower().strip()
    import re
    message_clean = re.sub(r'[^\w\sа-яё]', '', message_lower)
    
    for key, reply in QUICK_REPLIES.items():
        if message_clean == key or message_clean.startswith(key) or key in message_clean:
            await message.answer(
                reply,
                reply_to_message_id=message.message_id,
                parse_mode="HTML"
            )
            logger.info(f"💬 Авто-ответ на: {message.text[:50]}")
            return
    # ========================================================================
    # 🔥 ВОЛОНТЁР ОТВЕЧАЕТ АБИТУРИЕНТУ (через reply)
    # ========================================================================
    if user_id == ADMIN_ID and user_id in volunteer_mode_users:
        if message.reply_to_message:
            try:
                replied_text = message.reply_to_message.text
                logger.info(f"🔍 Текст ответа: {replied_text[:200]}...")
                
                applicant_id = None
                import re
                patterns = [
                    r'👤 ID: <code>(\d+)</code>',
                    r'👤 ID: (\d+)',
                    r'ID: (\d+)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, replied_text)
                    if match:
                        applicant_id = int(match.group(1))
                        logger.info(f"✅ Найден ID абитуриента: {applicant_id}")
                        break
                
                if not applicant_id:
                    if message.reply_to_message.forward_from:
                        applicant_id = message.reply_to_message.forward_from.id
                
                if not applicant_id:
                    replied_user = message.reply_to_message.from_user
                    if not replied_user.is_bot:
                        applicant_id = replied_user.id
                
                if not applicant_id:
                    logger.error(f"❌ Не удалось найти ID абитуриента!")
                    await message.answer(
                        "⚠️ <b>Не удалось найти ID!</b>",
                        reply_markup=get_back_keyboard()
                    )
                    return
                
                await message.bot.send_message(
                    applicant_id,
                    f"📞 <b>Ответ волонтёра:</b>\n\n{message.text}"
                )
                
                logger.info(f"✅ Ответ волонтёра отправлен {applicant_id}")
                await message.answer(
                    f"✅ <b>Ответ отправлен!</b>",
                    reply_markup=get_back_keyboard()
                )
                
            except Exception as e:
                logger.error(f"❌ Ошибка: {e}")
        return
    
    # ========================================================================
    # 🔥 АБИТУРИЕНТ ПИШЕТ ВОЛОНТЁРУ
    # ========================================================================
    user_data = user_last_message.get(user_id)
    if isinstance(user_data, dict) and user_data.get("mode") == "waiting_volunteer":
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
        user_last_message[user_id] = {}
        return
    
    # ========================================================================
    # 🔥 ИИ-ПОМОЩНИК — РЕЖИМ 1 СООБЩЕНИЯ + REPLY ✅
    # ========================================================================
    if user_id in ai_mode_users:
        try:
            from services.llm_service import llm_service
            from services.rag_service import rag_service
            
            # 🔥 Поиск контекста из базы знаний
            context_result = await rag_service.find_relevant_context(question=message.text)
            
            # 🔥 Проверка типа контекста
            if isinstance(context_result, str):
                context_text = context_result
            elif isinstance(context_result, dict):
                context_text = context_result.get('context', 'Нет данных')
            else:
                context_text = str(context_result)
            
            # 🔥 АНИМАЦИЯ "ПЕЧАТАЕТ..."
            await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
            await asyncio.sleep(0.3)
            
            # 🔥 Генерация ответа через GigaChat
            ai_response = await llm_service.generate_answer(
                question=message.text,
                context=context_text,
                user_id=user_id,
                is_male=None
            )
            
            # 🔥 ОЧИСТКА ОТ НЕПОДДЕРЖИВАЕМЫХ ТЕГОВ И MARKDOWN (ОБНОВЛЁННАЯ!)
            def clean_telegram_html(text: str) -> str:
                """Убирает теги и Markdown которые Telegram не поддерживает в HTML режиме"""
                import re
                
                # 🔥 Убираем ВСЕ неподдерживаемые HTML-теги
                text = re.sub(r'</?(ul|ol|li|h[1-6]|p|div|span|table|tr|td|th|thead|tbody|hr|img)[^>]*>', '', text)
                
                # 🔥 Убираем Markdown маркеры:
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)  # **жирный** → <b>жирный</b>
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)       # *курсив* → <i>курсив</i>
                text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)       # __подчёркнутый__ → <u>подчёркнутый</u>
                text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)       # ~~зачёркнутый~~ → <s>зачёркнутый</s>
                text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text) # `код` → <code>код</code>
                
                # 🔥 Убираем лишние ** и * если они не в парах
                text = text.replace('**', '').replace('*', '')
                
                # 🔥 Заменяем <br> на перенос строки
                text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                
                # 🔥 Убираем горизонтальные линии (---, ***, ___)
                text = re.sub(r'\n?[-*_]{3,}\n?', '\n\n', text)
                
                # 🔥 Убираем лишние переносы
                text = re.sub(r'\n{3,}', '\n\n', text)
                
                return text.strip()
            
            ai_response = clean_telegram_html(ai_response)
            
            # 🔥 Кнопки обратной связи
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👍 Полезно", callback_data="feedback_good"),
                 InlineKeyboardButton(text="👎 Не помогло", callback_data="feedback_bad")],
                [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
            ])
            
            # 🔥 ОТПРАВЛЯЕМ КАК REPLY НА СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ (РЕЖИМ 1 СООБЩЕНИЯ!)
            await message.answer(
                ai_response,
                reply_markup=keyboard,
                parse_mode="HTML",
                reply_to_message_id=message.message_id  # ← ГЛАВНОЕ: ответ на вопрос!
            )
            
            logger.info(f"🤖 ИИ ответил: {message.text[:50]}...")
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Ошибка ИИ: {e}")
            logger.error(f"❌ Трассировка:\n{traceback.format_exc()}")
            
            await message.answer(
                f"⚠️ <b>Ошибка ИИ:</b> <code>{str(e)[:150]}</code>\n\n"
                "Попробуйте перефразировать вопрос или выберите раздел в меню.",
                reply_markup=get_back_keyboard(),
                parse_mode="HTML",
                reply_to_message_id=message.message_id  # ← И ошибка тоже как reply!
            )
        return
    
    # ========================================================================
    # 🔥 ОБЫЧНОЕ СООБЩЕНИЕ (не ИИ, не волонтёр)
    # ========================================================================
    await message.answer(
        "💡 <b>Выберите раздел в меню</b>\n\n"
        "Или нажмите 🤖 ИИ-помощник для вопроса.",
        reply_markup=get_back_keyboard()
    )

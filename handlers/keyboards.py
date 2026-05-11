"""
⌨️ Keyboards for DGTU Bot
==========================
Все клавиатуры бота с эмодзи и персонализацией
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ============================================================================
# 🔥 ОСНОВНЫЕ КЛАВИАТУРЫ
# ============================================================================

def get_welcome_keyboard() -> InlineKeyboardMarkup:
    """🚀 Приветственная клавиатура"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Начать использование", callback_data="show_main_menu")],
        [
            InlineKeyboardButton(text="🌐 Сайт ДГТУ", url="https://donstu.ru"),
            InlineKeyboardButton(text="💬 Группа ВК", url="https://vk.ru/iivtdstu")
        ]
    ])


def get_main_keyboard() -> InlineKeyboardMarkup:
    """🏠 Главное меню — 14 функций"""
    return InlineKeyboardMarkup(inline_keyboard=[
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


def get_back_keyboard() -> InlineKeyboardMarkup:
    """🔙 Кнопка назад в главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])


def get_back_with_cancel_keyboard() -> InlineKeyboardMarkup:
    """🔙 Кнопки "Назад" и "В меню" """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])


# ============================================================================
# 🔥 FAQ КЛАВИАТУРА
# ============================================================================

def get_faq_keyboard() -> InlineKeyboardMarkup:
    """❓ Частые вопросы"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Документы", callback_data="faq_documents"),
         InlineKeyboardButton(text="📅 Сроки подачи", callback_data="faq_dates")],
        [InlineKeyboardButton(text="📊 Проходные баллы", callback_data="faq_scores"),
         InlineKeyboardButton(text="💰 Стоимость", callback_data="faq_cost")],
        [InlineKeyboardButton(text="🏠 Общежитие", callback_data="faq_dormitory"),
         InlineKeyboardButton(text="💵 Стипендии", callback_data="faq_scholarships")],
        [InlineKeyboardButton(text="🎖️ ВУЦ", callback_data="vuts")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])


# ============================================================================
# 🔥 НАПРАВЛЕНИЯ С ПАГИНАЦИЕЙ
# ============================================================================

def get_programs_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """📚 Направления подготовки с пагинацией"""
    
    programs = [
        {"code": "01.03.04", "name": "Прикладная математика"},
        {"code": "02.03.03", "name": "Математическое обеспечение"},
        {"code": "09.03.01", "name": "Информатика и ВТ"},
        {"code": "09.03.02_ist", "name": "Инф. системы (ИСТ)"},
        {"code": "09.03.02_ai", "name": "Искусственный интеллект (ИИ)"},
        {"code": "09.03.02_web", "name": "Web-разработка (WEB)"},
        {"code": "09.03.02_zaoch", "name": "Инф. системы (заочное)"},
        {"code": "09.03.03", "name": "Прикладная информатика"},
        {"code": "09.03.03_zaoch", "name": "Прикл. информатика (заочное)"},
        {"code": "09.03.04", "name": "Программная инженерия"},
        {"code": "10.03.01", "name": "Информационная безопасность"},
        {"code": "10.05.01", "name": "Комп. безопасность (спец)"},
        {"code": "10.05.02", "name": "Инф. безопасность (спец)"},
    ]
    
    items_per_page = 4
    total_pages = (len(programs) + items_per_page - 1) // items_per_page
    
    start = page * items_per_page
    end = min(start + items_per_page, len(programs))
    page_programs = programs[start:end]
    
    keyboard_buttons = []
    for prog in page_programs:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{prog['code']} • {prog['name']}", 
                callback_data=f"program_{prog['code']}"
            )
        ])
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"programs_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"programs_page_{page+1}"))
    
    keyboard_buttons.append(nav_buttons)
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


# ============================================================================
# 🔥 ДНИ ОТКРЫТЫХ ДВЕРЕЙ
# ============================================================================

def get_open_days_keyboard() -> InlineKeyboardMarkup:
    """📅 Дни открытых дверей"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Установить напоминание", callback_data="reminder_set"),
         InlineKeyboardButton(text="⏭️ Пропустить", callback_data="reminder_skip")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])


# ============================================================================
# 🔥 РУКОВОДСТВО
# ============================================================================

def get_leadership_keyboard() -> InlineKeyboardMarkup:
    """👥 Руководство"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Декан факультета", callback_data="dean"),
         InlineKeyboardButton(text="👥 Заместители декана", callback_data="deputies")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])


# ============================================================================
# 🔥 ИИ-ПОМОЩНИК И ОБРАТНАЯ СВЯЗЬ
# ============================================================================

def get_ai_assistant_keyboard() -> InlineKeyboardMarkup:
    """🤖 ИИ-помощник"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])


def get_feedback_keyboard() -> InlineKeyboardMarkup:
    """👍👎 Обратная связь"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👍 Полезно", callback_data="feedback_good"),
         InlineKeyboardButton(text="👎 Не помогло", callback_data="feedback_bad")]
    ])


def get_feedback_reason_keyboard() -> InlineKeyboardMarkup:
    """❓ Почему не помогло"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Нет информации", callback_data="feedback_reason_no_info"),
         InlineKeyboardButton(text="❌ Неправильный ответ", callback_data="feedback_reason_wrong")],
        [InlineKeyboardButton(text="🔄 Устаревшие данные", callback_data="feedback_reason_old"),
         InlineKeyboardButton(text="✏️ Другое", callback_data="feedback_reason_other")],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="feedback_cancel")]
    ])


# ============================================================================
# 🔥 КАЛЬКУЛЯТОР ЕГЭ
# ============================================================================

def get_calculator_subjects_keyboard() -> InlineKeyboardMarkup:
    """🧮 Калькулятор ЕГЭ — выбор предметов"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📐 Мат + 📝 Рус + 💻 Инф", callback_data="calc_start")],
        [InlineKeyboardButton(text="📐 Мат + 📝 Рус + ⚛️ Физ", callback_data="calc_start_physics")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
    ])


def get_calculator_result_keyboard() -> InlineKeyboardMarkup:
    """🧮 Калькулятор — кнопки после результата"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Посмотреть направления", callback_data="programs")],
        [InlineKeyboardButton(text="📋 Мой чек-лист", callback_data="checklist_btn")],
        [InlineKeyboardButton(text="💬 Спросить волонтёра", callback_data="help_volunteer")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
    ])


# ============================================================================
# 🔥 ЧЕК-ЛИСТ — НОВЫЕ КНОПКИ
# ============================================================================

def get_checklist_task_keyboard(task_id: int, is_completed: bool) -> InlineKeyboardMarkup:
    """
    📋 Кнопки для отдельной задачи чек-листа
    
    Args:
        task_id: ID задачи в БД
        is_completed: Текущий статус задачи
    """
    btn_text = "↩️ Сбросить" if is_completed else "✓ Выполнить"
    btn_data = f"toggle_task_{task_id}_{0 if is_completed else 1}"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, callback_data=btn_data)],
        [InlineKeyboardButton(text="🔙 Назад к чек-листу", callback_data="checklist_btn")]
    ])


def get_checklist_keyboard(tasks: list) -> InlineKeyboardMarkup:
    """
    📋 Клавиатура для всего чек-листа (устаревшая, используется get_checklist_task_keyboard)
    
    Args:
        tasks: Список задач из БД [(id, name, is_completed), ...]
    """
    keyboard_buttons = []
    for task in tasks:
        task_id, task_name, is_completed = task
        btn_text = "✓" if not is_completed else "↩️"
        keyboard_buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"toggle_task_{task_id}")
        ])
    keyboard_buttons.append([InlineKeyboardButton(text="🔄 Сбросить", callback_data="reset_checklist")])
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


# ============================================================================
# 🔥 КАФЕДРЫ И ДОСТИЖЕНИЯ
# ============================================================================

def get_departments_keyboard() -> InlineKeyboardMarkup:
    """🏛️ Кафедры"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])


def get_achievements_keyboard() -> InlineKeyboardMarkup:
    """🏆 Достижения"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Хакатон 2025", callback_data="ach_hackathon")],
        [InlineKeyboardButton(text="🛡️ Cyber Garden", callback_data="ach_cyber")],
        [InlineKeyboardButton(text="🔒 DDoS-Guard", callback_data="ach_ddos")],
        [InlineKeyboardButton(text="🎯 Приоритет 2030", callback_data="ach_priority")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])


# ============================================================================
# 🔥 УМНЫЙ ПОИСК И ТЕСТ
# ============================================================================

def get_smart_search_keyboard() -> InlineKeyboardMarkup:
    """🔍 Умный поиск — подсказки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Примеры запросов", callback_data="search_examples")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
    ])


def get_quiz_keyboard() -> InlineKeyboardMarkup:
    """🎯 Тест — навигация"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить тест", callback_data="quiz_cancel")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="show_main_menu")]
    ])

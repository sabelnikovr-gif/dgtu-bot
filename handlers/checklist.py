"""
📋 Checklist Handler for DGTU Bot
==================================
Интерактивный чек-лист абитуриента с визуальным прогрессом.

Функции:
• 📊 Прогресс-бар с эмодзи (🟩⬜)
• 🎨 Эмодзи для каждой задачи
• 💬 Мотивирующие сообщения
• 🔄 Переключение и сброс задач

Автор: @sabelnikovr
Дата: 2026
"""

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.utils import send_single_message
from models.database import db
import logging

router = Router()
logger = logging.getLogger(__name__)

# ============================================================================
# 🔥 КОНФИГУРАЦИЯ
# ============================================================================

DEFAULT_TASKS: list[str] = [
    "📄 Подготовить паспорт и копии",
    "🎓 Получить документ об образовании",
    "📸 Сделать фотографии 3×4 (4 шт.)",
    "💳 Получить СНИЛС",
    "📝 Подготовить результаты ЕГЭ",
    "🏥 Получить медсправку 086/у",
    "✍️ Подать заявление о приёме",
    "✅ Подать согласие на зачисление",
]

TASK_EMOJIS: dict[str, str] = {
    "паспорт": "📄",
    "аттестат": "🎓",
    "диплом": "🎓",
    "фото": "📸",
    "снилс": "💳",
    "егэ": "📝",
    "медсправка": "🏥",
    "заявление": "✍️",
    "согласие": "✅",
    "общежитие": "🏠",
}

# ============================================================================
# 🔥 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def get_task_emoji(task_name: str) -> str:
    """🎨 Возвращает пустую строку (эмодзи уже есть в задачах)"""
    return ""


def get_progress_bar(percent: int, length: int = 10) -> str:
    """📊 Генерирует прогресс-бар с эмодзи"""
    filled = int(length * percent / 100)
    empty = length - filled
    return "🟩" * filled + "⬜" * empty


def get_progress_status(percent: int) -> tuple[str, str]:
    """🎯 Возвращает эмодзи и текст статуса"""
    if percent == 100:
        return "🎉", "Всё готово! Ты супер! 🚀"
    elif percent >= 75:
        return "🔥", "Почти финиш! Ещё немного! 💪"
    elif percent >= 50:
        return "📈", "Отличный прогресс! Продолжай! ✨"
    elif percent >= 25:
        return "🚀", "Хорошее начало! Не останавливайся! 💙"
    else:
        return "🌱", "Начинаем путь к поступлению! 🎓"


# ============================================================================
# 🔥 ОСНОВНОЙ ОБРАБОТЧИК
# ============================================================================

@router.callback_query(F.data == "checklist_btn")
async def show_checklist(callback: types.CallbackQuery):
    """📋 Показать чек-лист с прогресс-баром"""
    
    user_id = callback.from_user.id
    
    try:
        tasks = await db.get_user_checklist(user_id)
        if not tasks:
            for task_name in DEFAULT_TASKS:
                await db.add_checklist_task(user_id, task_name)
            tasks = await db.get_user_checklist(user_id)
        
        total = len(tasks)
        completed = sum(1 for task in tasks if task[2] == 1)
        progress_percent = round((completed / total * 100)) if total > 0 else 0
        
        status_emoji, status_text = get_progress_status(progress_percent)
        progress_bar = get_progress_bar(progress_percent)
        
        # 🔥 Формируем текст
        text = f"📋 <b>Твой чек-лист абитуриента</b>\n\n"
        
        # 🔥 1. Список задач
        for task in tasks:
            task_id: int = task[0]
            task_name: str = task[1]
            is_completed: bool = task[2] == 1
            
            status = "⬜️" if not is_completed else "✅"
            text += f"{status} {task_name}\n"
        
        # 🔥 2. Прогресс
        text += f"\n📈 <b>Прогресс:</b> {progress_percent}%\n"
        text += f"{progress_bar}\n"
        text += f"✅ <b>{completed}</b> из <b>{total}</b> выполнено\n"
        text += f"💡 <i>{status_text}</i>\n\n"
        
        # 🔥 3. Инструкция
        text += f"👇 <b>Нажми на кнопку чтобы отметить задачу:</b>\n"
        
        # 🔥 Кнопки
        keyboard_buttons: list[list[InlineKeyboardButton]] = []
        
        for task in tasks:
            task_id: int = task[0]
            is_completed: bool = task[2] == 1
            
            btn_text = "↩️ Сбросить" if is_completed else "✓ Выполнить"
            btn_data = f"toggle_task_{task_id}_{0 if is_completed else 1}"
            
            keyboard_buttons.append([
                InlineKeyboardButton(text=btn_text, callback_data=btn_data)
            ])
        
        keyboard_buttons.append([])
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔄 Сбросить весь чек-лист", callback_data="reset_checklist")
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        try:
            await send_single_message(callback, text, reply_markup=keyboard)
        except Exception as send_error:
            logger.error(f"❌ Ошибка отправки: {send_error}")
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в show_checklist: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка загрузки чек-листа", show_alert=True)


# ============================================================================
# 🔥 ПЕРЕКЛЮЧЕНИЕ ЗАДАЧИ
# ============================================================================

@router.callback_query(F.data.startswith("toggle_task_"))
async def handle_toggle_task(callback: types.CallbackQuery):
    """🔄 Переключить статус задачи"""
    
    try:
        parts = callback.data.split("_")
        task_id = int(parts[2])
        
        await db.toggle_checklist_task(task_id)
        await callback.answer("✅ Статус обновлён!", show_alert=False)
        await show_checklist(callback)
        
    except (IndexError, ValueError) as e:
        logger.error(f"❌ Ошибка парсинга: {callback.data}")
        await callback.answer("⚠️ Ошибка обновления", show_alert=True)
    except Exception as e:
        logger.error(f"❌ Ошибка toggle_task: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)


# ============================================================================
# 🔥 СБРОС ЧЕК-ЛИСТА
# ============================================================================

@router.callback_query(F.data == "reset_checklist")
async def handle_reset_checklist(callback: types.CallbackQuery):
    """🔄 Сбросить весь чек-лист"""
    
    user_id = callback.from_user.id
    
    try:
        await db.clear_user_checklist(user_id)
        
        for task_name in DEFAULT_TASKS:
            await db.add_checklist_task(user_id, task_name)
        
        await callback.answer("🔄 Чек-лист сброшен! Начинаем заново! 🚀", show_alert=True)
        await show_checklist(callback)
        
        logger.info(f"🔄 Чек-лист сброшен: user_id={user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка reset_checklist: {e}")
        await callback.answer("⚠️ Ошибка сброса", show_alert=True)

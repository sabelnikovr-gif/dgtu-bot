"""
🔧 Utilities for DGTU Bot
=========================
Вспомогательные функции: отправка сообщений, клавиатуры
"""

from aiogram import types
from aiogram.types import FSInputFile, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# 🔥 ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================================================

user_last_message = {}

# ============================================================================
# 🔥 ПУТИ К ФОТО
# ============================================================================

BASE_PATH = Path(__file__).parent.parent
DATA_PATH = BASE_PATH / 'data'

PHOTO_BUILDING = DATA_PATH / 'building.jpg'
PHOTO_BUILDING_FOUNTAIN = DATA_PATH / 'building_fountain.jpg'
PHOTO_AI_LOGO = DATA_PATH / 'ai_logo.png'
PHOTO_CLOCK = DATA_PATH / 'clock.jpg'
PHOTO_DGTU_LOGO = DATA_PATH / 'dgtu_logo.png'

# ============================================================================
# 🔥 ИСПРАВЛЕННАЯ ФУНКЦИЯ ОТПРАВКИ
# ============================================================================

async def send_single_message(message_or_callback, text, reply_markup=None, parse_mode="HTML", photo_path=None, force_new: bool = False):
    """
    🔥 Отправка сообщения с умной обработкой фото/текст
    
    Аргументы:
        message_or_callback: Message или CallbackQuery
        text: Текст сообщения
        reply_markup: Клавиатура
        parse_mode: Режим парсинга (HTML/Markdown)
        photo_path: Путь к фото (опционально)
        force_new: Если True — всегда отправлять новое сообщение (не редактировать)
    
    Возвращает:
        Message: Отправленное сообщение
    """
    
    # 🔥 Определяем параметры из message/callback
    if isinstance(message_or_callback, types.CallbackQuery):
        cb = message_or_callback
        user_id = cb.from_user.id
        chat_id = cb.message.chat.id
        bot = cb.bot
        old_msg_id = cb.message.message_id
        old_is_photo = bool(cb.message.photo)
    else:
        msg = message_or_callback
        user_id = msg.from_user.id
        chat_id = msg.chat.id
        bot = msg.bot
        old_msg_id = user_last_message.get(user_id)
        old_is_photo = False  # Для Message сложно определить, предполагаем текст
    
    photo_exists = photo_path and Path(photo_path).exists()
    new_will_be_photo = photo_exists and len(text) <= 1024  # Caption limit
    
    # 🔥 Если текст длинный — НЕ используем фото (чтобы не обрезать)
    if len(text) > 1024:
        photo_exists = False
        new_will_be_photo = False
        logger.debug(f"📝 Текст длинный ({len(text)} симв.), отправляем без фото")
    
    # 🔥 Если принудительно новое сообщение — пропускаем редактирование
    if force_new or not old_msg_id:
        return await _send_new_message(bot, chat_id, text, reply_markup, parse_mode, photo_path, user_id)
    
    # 🔥 Пытаемся отредактировать существующее
    try:
        # Случай 1: Было фото, будет фото → edit_message_media
        if old_is_photo and new_will_be_photo:
            media = InputMediaPhoto(
                media=FSInputFile(photo_path),
                caption=text,
                parse_mode=parse_mode
            )
            await bot.edit_message_media(
                media=media,
                chat_id=chat_id,
                message_id=old_msg_id,
                reply_markup=reply_markup
            )
            user_last_message[user_id] = old_msg_id
            logger.debug(f"✏️ Отредактировано фото: user_id={user_id}")
            return
        
        # Случай 2: Было текст, будет текст → edit_message_text
        elif not old_is_photo and not new_will_be_photo:
            await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=old_msg_id,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            user_last_message[user_id] = old_msg_id
            logger.debug(f"✏️ Отредактирован текст: user_id={user_id}")
            return
        
        # Случай 3: Конфликт фото/текст → удаляем старое, отправляем новое
        else:
            logger.debug(f"🔄 Конфликт типов (фото↔текст), отправляем новое: user_id={user_id}")
            await _delete_old_message(bot, chat_id, old_msg_id)
            return await _send_new_message(bot, chat_id, text, reply_markup, parse_mode, photo_path, user_id)
            
    except Exception as e:
        logger.warning(f"⚠️ Ошибка редактирования: {e}. Отправляем новое сообщение.")
        await _delete_old_message(bot, chat_id, old_msg_id)
        return await _send_new_message(bot, chat_id, text, reply_markup, parse_mode, photo_path, user_id)


async def _send_new_message(bot, chat_id: int, text: str, reply_markup, parse_mode: str, photo_path, user_id: int):
    """📤 Внутренняя функция: отправка нового сообщения"""
    try:
        photo_exists = photo_path and Path(photo_path).exists()
        use_caption = photo_exists and len(text) <= 1024
        
        if use_caption:
            new_msg = await bot.send_photo(
                chat_id=chat_id,
                photo=FSInputFile(photo_path),
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            new_msg = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        
        user_last_message[user_id] = new_msg.message_id
        logger.debug(f"✅ Новое сообщение отправлено: user_id={user_id}, msg_id={new_msg.message_id}")
        return new_msg
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки нового сообщения: {e}")
        # 🔥 Последний шанс: отправляем простой текст без форматирования
        try:
            new_msg = await bot.send_message(
                chat_id=chat_id,
                text=text.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', ''),
                reply_markup=reply_markup
            )
            user_last_message[user_id] = new_msg.message_id
            return new_msg
        except:
            return None


async def _delete_old_message(bot, chat_id: int, message_id: int):
    """🗑️ Внутренняя функция: безопасное удаление старого сообщения"""
    if message_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.debug(f"⚠️ Не удалось удалить старое сообщение {message_id}: {e}")


# ============================================================================
# 🔥 КЛАВИАТУРЫ
# ============================================================================

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


def get_previous_menu_keyboard(previous_callback: str) -> InlineKeyboardMarkup:
    """⬅️ Кнопка "Назад" с кастомным callback"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=previous_callback)],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="show_main_menu")]
    ])

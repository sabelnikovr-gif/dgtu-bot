"""
🤖 DGTU Bot — Main Entry Point
===============================
Точка входа для бота ИиВТ ДГТУ Помощник

Автор: @sabelnikovr
Дата: 2026
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from config import Config
from services.database import db
from services.llm_service import llm_service
from services.cache_service import cache, data_cache
from handlers import commands, faq_handler, feedback_handler, admin, checklist, calculator, quiz_direction
from handlers.utils import user_last_message, PHOTO_AI_LOGO

# ============================================================================
# 🔥 НАСТРОЙКА ЛОГИРОВАНИЯ — ТОЛЬКО ВАЖНОЕ
# ============================================================================

class ImportantOnlyFilter(logging.Filter):
    """Фильтр: показывает только важные сообщения"""
    
    def filter(self, record):
        msg = record.getMessage().lower()
        
        # Всегда показываем ошибки
        if record.levelno >= logging.ERROR:
            return True
        
        # Показываем важные INFO
        important_keywords = [
            'запущен', 'запуск', 'старт', 'bot:', 'id:',
            'пользователь', 'сохранён', 'добавлен',
            'база данных', 'подключена', 'отключена',
            'кеш', 'активирован', 'ошибка запуска',
            'рассылка', 'завершена', 'волонтёр',
            'режим', 'включён', 'выключен'
        ]
        
        if record.levelno == logging.INFO:
            return any(kw in msg for kw in important_keywords)
        
        return False

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)

# Применяем фильтр
logging.getLogger().addFilter(ImportantOnlyFilter())
logging.getLogger('aiogram.event').setLevel(logging.WARNING)
logging.getLogger('aiogram.dispatcher').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
config = Config()

# ============================================================================
# 🔥 НАСТРОЙКА ПРОКСИ И БОТА
# ============================================================================

def create_session(proxy_url: str = None):
    """Создание AiohttpSession с прокси"""
    if proxy_url:
        return AiohttpSession(proxy=proxy_url)
    return AiohttpSession()

session = create_session(config.PROXY_URL)

bot = Bot(
    token=config.BOT_TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ============================================================================
# 🔥 ПОДКЛЮЧЕНИЕ РОУТЕРОВ
# ============================================================================

dp.include_router(commands.router)
dp.include_router(faq_handler.router)
dp.include_router(feedback_handler.router)
dp.include_router(admin.router)
dp.include_router(checklist.router)
dp.include_router(calculator.router)
dp.include_router(quiz_direction.router)

# ============================================================================
# 🔥 ЗАПУСК БОТА
# ============================================================================

async def main():
    """🚀 Основная функция запуска бота"""
    try:
        # Инициализация сервисов
        logger.info("✅ Кеш токенов активирован")
        logger.info("✅ Кеш данных активирован")
        
        await db.connect()
        logger.info("✅ База данных подключена (SQLite)")
        
        # Получение информации о боте
        try:
            bot_info = await bot.get_me(request_timeout=60)
            logger.info(f"✅ Бот: @{bot_info.username} | ID: {bot_info.id}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить info бота: {e}")
        
        # Финальное сообщение о запуске
        logger.info("=" * 80)
        logger.info("🤖 ИиВТ ДГТУ Помощник — ЗАПУЩЕН")
        logger.info("=" * 80)
        logger.info(f"✅ Токен: {config.BOT_TOKEN[:20]}...")
        logger.info(f"✅ Прокси: {config.PROXY_URL if config.PROXY_URL else 'Нет'}")
        logger.info("✅ ИИ (GigaChat) готов")
        logger.info("✅ Кеширование включено")
        logger.info("✅ Умный поиск: /search")
        logger.info("✅ Связь с волонтёром: /quick_help")
        logger.info("✅ Тест направления: /quiz")
        logger.info("=" * 80)
        logger.info("🚀 БОТ ЗАПУЩЕН!")
        logger.info("📱 Telegram: /start")
        logger.info("📊 Статистика: /stats")
        logger.info("📋 Чек-лист: /checklist")
        logger.info("🧮 Калькулятор: /calculator")
        logger.info("🔍 Поиск: /search")
        logger.info("📞 Помощь: /quick_help")
        logger.info("🎯 Тест: /quiz")
        logger.info("⏹️  Остановка: Ctrl + C")
        logger.info("=" * 80)
        
        # Запуск polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}", exc_info=True)
        raise
    
    finally:
        await db.close()
        logger.info("🔌 База данных отключена")
        await bot.session.close()
        logger.info("🔌 Бот отключён")

# ============================================================================
# 🔥 ТОЧКА ВХОДА
# ============================================================================

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️  Остановка: Ctrl + C")

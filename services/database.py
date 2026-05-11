from models.database import db
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Сервис для работы с базой данных"""
    
    @staticmethod
    async def init():
        """Инициализация БД"""
        await db.connect()
        logger.info("✅ База данных подключена (SQLite)")
    
    @staticmethod
    async def close():
        """Закрытие БД"""
        await db.close()
        logger.info("🔌 База данных отключена")
    
    @staticmethod
    async def track_user(user_id: int, username: str, first_name: str, last_name: str = None):
        """Отслеживание пользователя"""
        await db.add_user(user_id, username, first_name, last_name)
    
    @staticmethod
    async def track_message(user_id: int, message_text: str):
        """Отслеживание сообщения"""
        await db.add_message(user_id, message_text)
    
    @staticmethod
    async def get_stats() -> dict:
        """📊 Получение статистики"""
        feedback = await db.get_feedback_stats()
        positive = feedback.get("👍", 0)
        negative = feedback.get("👎", 0)
        
        return {
            'users': await db.get_user_count(),
            'messages': await db.get_message_count(),
            'feedback': {
                '👍': positive,
                '👎': negative
            }
        }
    
    @staticmethod
    async def get_users_count() -> int:
        """📊 Получить количество пользователей"""
        return await db.get_user_count()
    
    @staticmethod
    async def get_active_users_count(days: int = 7) -> int:
        """🟢 Активные пользователи за N дней"""
        return await db.get_active_users_count(days)
    
    @staticmethod
    async def get_messages_count() -> int:
        """💬 Количество сообщений"""
        return await db.get_message_count()
    
    @staticmethod
    async def get_all_users() -> list:
        """📋 Получить всех пользователей для рассылки"""
        return await db.get_all_users()
    
    @staticmethod
    async def log_news_sent(user_id: int, delivered: bool = True):
        """📊 Логирование отправки новости"""
        await db.log_news_sent(user_id, delivered)
    
    @staticmethod
    async def mark_user_inactive(user_id: int):
        """🚫 Пометить пользователя как неактивного"""
        await db.mark_user_inactive(user_id)
    
    @staticmethod
    async def get_news_stats() -> dict:
        """📈 Статистика рассылок"""
        return await db.get_news_stats()
    
    @staticmethod
    async def update_user_activity(user_id: int):
        """🔄 Обновить активность пользователя"""
        await db.update_user_activity(user_id)

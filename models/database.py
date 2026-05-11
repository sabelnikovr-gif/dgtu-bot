"""
🗄️ Database Service for DGTU Bot
=================================
SQLite база данных с асинхронным доступом (aiosqlite)
"""

import aiosqlite
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any


class Database:
    """🗄️ SQLite база данных для бота"""
    
    def __init__(self, db_path: str = "data/bot_database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.db = None
    
    async def connect(self):
        """🔌 Подключение к БД"""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self.create_tables()
    
    async def close(self):
        """🔌 Закрытие подключения"""
        if self.db:
            await self.db.close()
    
    async def create_tables(self):
        """📋 Создание таблиц + миграции"""
        
        # Пользователи
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Сообщения
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Чек-листы
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS checklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_name TEXT,
                is_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Отзывы
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                rating TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Активность пользователей
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Статистика рассылок
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS news_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivered INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # 🔥 НОВОЕ: Логи поиска
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS search_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT,
                category TEXT,
                cache_hit INTEGER DEFAULT 0,
                context_parts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # 🔥 НОВОЕ: Интересы пользователей (персонализация)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS user_interests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                interest_type TEXT,
                interest_value TEXT,
                score INTEGER DEFAULT 1,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, interest_type, interest_value)
            )
        """)
        
        # Индексы для скорости
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_news_user ON news_stats(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_search_query ON search_log(query)",
            "CREATE INDEX IF NOT EXISTS idx_search_user ON search_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_interests_user ON user_interests(user_id)",
        ]
        
        for index_sql in indexes:
            try:
                await self.db.execute(index_sql)
            except aiosqlite.OperationalError:
                pass
        
        await self.db.commit()
    
    # ============================================================================
    # 🔹 ПОЛЬЗОВАТЕЛИ
    # ============================================================================
    
    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str = None):
        """➕ Добавить пользователя"""
        await self.db.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_seen, is_active)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        """, (user_id, username, first_name, last_name))
        await self.db.commit()
    
    async def get_user_count(self) -> int:
        """📊 Получить количество пользователей"""
        cursor = await self.db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        result = await cursor.fetchone()
        return result[0] if result else 0
    
    async def get_all_users(self) -> list:
        """📋 Получить всех пользователей"""
        cursor = await self.db.execute("SELECT user_id FROM users WHERE is_active = 1")
        results = await cursor.fetchall()
        return [row[0] for row in results]
    
    async def get_active_users_count(self, days: int = 7) -> int:
        """🟢 Активные за N дней"""
        cursor = await self.db.execute("""
            SELECT COUNT(DISTINCT user_id) FROM user_activity 
            WHERE last_active >= datetime('now', ?)
        """, (f'-{days} days',))
        result = await cursor.fetchone()
        return result[0] if result else 0
    
    async def mark_user_inactive(self, user_id: int):
        """🚫 Пометить неактивным"""
        await self.db.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
        await self.db.commit()
    
    async def update_user_activity(self, user_id: int):
        """🔄 Обновить активность"""
        await self.db.execute("""
            INSERT INTO user_activity (user_id, last_active) 
            VALUES (?, CURRENT_TIMESTAMP)
        """, (user_id,))
        await self.db.execute("""
            UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE user_id = ?
        """, (user_id,))
        await self.db.commit()
    
    # ============================================================================
    # 🔹 СООБЩЕНИЯ
    # ============================================================================
    
    async def add_message(self, user_id: int, message_text: str):
        """💬 Сохранить сообщение"""
        await self.db.execute("""
            INSERT INTO messages (user_id, message_text)
            VALUES (?, ?)
        """, (user_id, message_text[:500]))
        await self.db.commit()
    
    async def get_message_count(self) -> int:
        """📊 Количество сообщений"""
        cursor = await self.db.execute("SELECT COUNT(*) FROM messages")
        result = await cursor.fetchone()
        return result[0] if result else 0
    
    # ============================================================================
    # 🔹 ЧЕК-ЛИСТЫ
    # ============================================================================
    
    async def add_checklist_task(self, user_id: int, task_name: str):
        """📋 Добавить задачу"""
        await self.db.execute("""
            INSERT INTO checklists (user_id, task_name, is_completed)
            VALUES (?, ?, 0)
        """, (user_id, task_name))
        await self.db.commit()
    
    async def get_user_checklist(self, user_id: int) -> list:
        """📋 Получить чек-лист"""
        cursor = await self.db.execute("""
            SELECT id, task_name, is_completed FROM checklists
            WHERE user_id = ?
            ORDER BY created_at
        """, (user_id,))
        return await cursor.fetchall()
    
    async def toggle_checklist_task(self, task_id: int):
        """🔄 Переключить задачу"""
        await self.db.execute("""
            UPDATE checklists SET is_completed = 1 - is_completed
            WHERE id = ?
        """, (task_id,))
        await self.db.commit()
    
    async def clear_user_checklist(self, user_id: int):
        """🗑️ Очистить чек-лист"""
        await self.db.execute("DELETE FROM checklists WHERE user_id = ?", (user_id,))
        await self.db.commit()
    
    # ============================================================================
    # 🔹 ОТЗЫВЫ
    # ============================================================================
    
    async def add_feedback(self, user_id: int, rating: str):
        """💬 Сохранить отзыв"""
        await self.db.execute("""
            INSERT INTO feedback (user_id, rating)
            VALUES (?, ?)
        """, (user_id, rating))
        await self.db.commit()
    
    async def get_feedback_stats(self) -> dict:
        """📊 Статистика отзывов"""
        cursor = await self.db.execute("""
            SELECT rating, COUNT(*) as count FROM feedback
            GROUP BY rating
        """)
        results = await cursor.fetchall()
        return {row[0]: row[1] for row in results}
    
    # ============================================================================
    # 🔹 РАССЫЛКИ
    # ============================================================================
    
    async def log_news_sent(self, user_id: int, delivered: bool = True):
        """📊 Лог отправки новости"""
        await self.db.execute("""
            INSERT INTO news_stats (user_id, sent_at, delivered)
            VALUES (?, CURRENT_TIMESTAMP, ?)
        """, (user_id, 1 if delivered else 0))
        await self.db.commit()
    
    async def get_news_stats(self) -> dict:
        """📈 Статистика рассылок"""
        cursor = await self.db.execute("SELECT COUNT(DISTINCT date(sent_at)) FROM news_stats")
        total_news = (await cursor.fetchone())[0] or 0
        
        cursor = await self.db.execute("SELECT COUNT(*) FROM news_stats")
        total_sent = (await cursor.fetchone())[0] or 0
        
        cursor = await self.db.execute("SELECT COUNT(*) FROM news_stats WHERE delivered = 1")
        total_delivered = (await cursor.fetchone())[0] or 0
        
        cursor = await self.db.execute("SELECT COUNT(*) FROM users WHERE is_active = 0")
        total_blocked = (await cursor.fetchone())[0] or 0
        
        avg_delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        
        return {
            "total_news": total_news,
            "total_sent": total_sent,
            "total_delivered": total_delivered,
            "total_blocked": total_blocked,
            "avg_delivery_rate": round(avg_delivery_rate, 1)
        }
    
    # ============================================================================
    # 🔥 НОВОЕ: ЛОГИ ПОИСКА
    # ============================================================================
    
    async def log_search_query(self, user_id: int, query: str, category: Optional[str], 
                               cache_hit: bool, context_parts: int):
        """🔍 Записать запрос поиска в лог"""
        await self.db.execute("""
            INSERT INTO search_log (user_id, query, category, cache_hit, context_parts)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, query, category, 1 if cache_hit else 0, context_parts))
        await self.db.commit()
    
    async def get_search_stats(self) -> dict:
        """📊 Статистика поиска"""
        # Всего запросов
        cursor = await self.db.execute("SELECT COUNT(*) FROM search_log")
        total_queries = (await cursor.fetchone())[0] or 0
        
        # Попадания в кэш
        cursor = await self.db.execute("SELECT COUNT(*) FROM search_log WHERE cache_hit = 1")
        cache_hits = (await cursor.fetchone())[0] or 0
        cache_rate = round((cache_hits / total_queries * 100), 1) if total_queries > 0 else 0
        
        # Топ-5 запросов
        cursor = await self.db.execute("""
            SELECT query, COUNT(*) as count FROM search_log
            GROUP BY query
            ORDER BY count DESC
            LIMIT 5
        """)
        top_queries = await cursor.fetchall()
        
        return {
            "total_queries": total_queries,
            "cache_hits": cache_hits,
            "cache_rate": cache_rate,
            "top_queries": [{"query": row[0], "count": row[1]} for row in top_queries]
        }
    
    # ============================================================================
    # 🔥 НОВОЕ: ИНТЕРЕСЫ ПОЛЬЗОВАТЕЛЕЙ (ПЕРСОНАЛИЗАЦИЯ)
    # ============================================================================
    
    async def save_user_interest(self, user_id: int, interest_type: str, interest_value: str):
        """🎯 Сохранить интерес пользователя (или обновить score)"""
        await self.db.execute("""
            INSERT INTO user_interests (user_id, interest_type, interest_value, score, last_seen)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, interest_type, interest_value) 
            DO UPDATE SET score = score + 1, last_seen = CURRENT_TIMESTAMP
        """, (user_id, interest_type, interest_value))
        await self.db.commit()
    
    async def get_user_interests(self, user_id: int, min_score: int = 2) -> list:
        """🎯 Получить интересы пользователя (с минимальным score)"""
        cursor = await self.db.execute("""
            SELECT interest_type, interest_value, score FROM user_interests
            WHERE user_id = ? AND score >= ?
            ORDER BY score DESC, last_seen DESC
            LIMIT 5
        """, (user_id, min_score))
        return await cursor.fetchall()
    
    async def decay_user_interests(self):
        """📉 Снизить score у старых интересов (вызывать раз в неделю)"""
        await self.db.execute("""
            UPDATE user_interests 
            SET score = score - 1 
            WHERE last_seen < datetime('now', '-30 days') AND score > 0
        """)
        await self.db.execute("""
            DELETE FROM user_interests WHERE score <= 0
        """)
        await self.db.commit()


# ============================================================================
# 🔥 ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ============================================================================

db = Database()

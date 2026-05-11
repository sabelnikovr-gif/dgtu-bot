from collections import OrderedDict
from datetime import datetime, timedelta
import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# 🔥 КЭШ ДЛЯ ТОКЕНОВ GIGACHAT (async)
# ============================================================================

class TokenCache:
    """💾 Кеш для экономии токенов GigaChat"""
    
    def __init__(self, max_size: int = 1000, ttl_minutes: int = 60):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
        
        # 🔥 Статистика
        self.hits = 0
        self.misses = 0
        self.user_counts = {}
        
    async def get(self, key: str) -> str | None:
        """🔍 Получить значение из кеша"""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry['expires']:
                self.cache.move_to_end(key)
                self.hits += 1
                logger.debug(f"✅ Cache HIT: {key[:30]}")
                return entry['value']
            else:
                del self.cache[key]
        self.misses += 1
        logger.debug(f"❌ Cache MISS: {key[:30]}")
        return None
    
    async def set(self, key: str, value: str):
        """💾 Сохранить значение в кеш"""
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key] = {
                'value': value,
                'expires': datetime.now() + self.ttl
            }
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            self.cache[key] = {
                'value': value,
                'expires': datetime.now() + self.ttl
            }
        logger.debug(f"💾 Cache SET: {key[:30]}")
    
    async def clear(self):
        """🧹 Очистить кеш"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("🧹 Кеш токенов очищен")
    
    def get_stats(self) -> dict:
        """📊 Статистика кеша токенов"""
        total = self.hits + self.misses
        hit_rate = f"{(self.hits / total * 100):.1f}%" if total > 0 else "0%"
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }
    
    async def increment_user_count(self, user_id: int, username: str = None):
        """👤 Увеличить счётчик сообщений"""
        if user_id not in self.user_counts:
            self.user_counts[user_id] = 0
        self.user_counts[user_id] += 1
        await asyncio.sleep(0)
    
    async def cleanup_expired(self):
        """🧹 Удалить просроченные записи"""
        now = datetime.now()
        expired_keys = [key for key, entry in self.cache.items() if entry['expires'] < now]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            logger.info(f"🧹 Очистка кеша: удалено {len(expired_keys)} записей")

# ============================================================================
# 🔥 НОВЫЙ: ОБЩИЙ КЭШ ДЛЯ ДАННЫХ БОТА (sync)
# ============================================================================

class DataCache:
    """🗄️ Общий кеш для данных бота (направления, стипендии, и т.д.)"""
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_time: Dict[str, float] = {}
        self.max_size = max_size
        self.ttl = ttl_seconds  # 5 минут по умолчанию
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """📥 Получить данные из кэша"""
        if key in self.cache:
            if time.time() - self.cache_time[key] < self.ttl:
                self.hits += 1
                return self.cache[key]
            else:
                self.delete(key)
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """💾 Сохранить данные в кэш"""
        if ttl is None:
            ttl = self.ttl
        
        if len(self.cache) >= self.max_size:
            # Удаляем самый старый
            oldest_key = min(self.cache_time, key=self.cache_time.get)
            self.delete(oldest_key)
        
        self.cache[key] = value
        self.cache_time[key] = time.time()
    
    def delete(self, key: str):
        """🗑️ Удалить данные из кэша"""
        if key in self.cache:
            del self.cache[key]
        if key in self.cache_time:
            del self.cache_time[key]
    
    def clear(self):
        """🧹 Очистить весь кэш"""
        self.cache.clear()
        self.cache_time.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> dict:
        """📊 Статистика кэша"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 1),
            "ttl": self.ttl
        }

# ============================================================================
# 🔥 ГЛОБАЛЬНЫЕ ЭКЗЕМПЛЯРЫ
# ============================================================================

import time  # ← Добавь этот импорт!

# Кеш для токенов GigaChat (async)
token_cache = TokenCache(max_size=1000, ttl_minutes=60)

# Кеш для данных бота (sync)
data_cache = DataCache(max_size=500, ttl_seconds=300)

# 🔥 Для обратной совместимости — старый интерфейс
cache = token_cache  # ← Оставляем для старого кода

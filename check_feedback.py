import asyncio
from services.cache_service import cache

async def check_feedback():
    print("🔍 Ищем отзывы в кэше...\n")
    
    for key, value in cache.cache.items():
        if key.startswith("feedback:"):
            print(f"📌 {key}: {value}")
    
    print("\n✅ Готово!")

if __name__ == "__main__":
    asyncio.run(check_feedback())

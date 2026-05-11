import aiohttp
import asyncio

async def test():
    print("🔍 Проверяю доступ к Telegram API...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.telegram.org") as resp:
                print(f"✅ Доступ есть! Статус: {resp.status}")
                print("💚 VPN работает correctly!")
    except Exception as e:
        print(f"❌ Нет доступа: {e}")
        print("💡 VPN не помогает, попробуй другой")

asyncio.run(test())
input("\nНажми Enter чтобы выйти...")

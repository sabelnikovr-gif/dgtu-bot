import asyncio
import aiohttp

PROXY = "http://103.78.189.79:8000"

async def test():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.telegram.org/bot8628225993:getMe",
                proxy=PROXY,
                timeout=10
            ) as resp:
                print(f"✅ Прокси работает! {resp.status}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

asyncio.run(test())

from config import Config
from gigachat import GigaChat

config = Config()

print("🔍 Проверяю GigaChat...")
print(f"Ключ найден: {config.GIGACHAT_AUTHORIZATION_KEY is not None}")

try:
    client = GigaChat(
        credentials=config.GIGACHAT_AUTHORIZATION_KEY,
        verify_ssl_certs=False,
    )
    print("✅ Подключение к GigaChat...")
    
    response = client.chat("Привет! Ты работаешь? Ответь кратко.")
    print("✅ GigaChat ответил:", response.choices[0].message.content)
    print("\n🎉 GIGACHAT РАБОТАЕТ!")
except Exception as e:
    print("❌ Ошибка:", e)
    print("\n⚠️ GigaChat не работает, но бот будет отвечать из базы знаний")

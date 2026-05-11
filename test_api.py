import requests
import time

print("🔍 Проверяю доступ к Telegram API...")
print("⏳ Подожди 10 секунд...")

try:
    # Пробуем подключиться к Telegram API
    response = requests.get("https://api.telegram.org", timeout=10)
    print(f"✅ Telegram API доступен! Статус: {response.status_code}")
except Exception as e:
    print(f"❌ Telegram API НЕ доступен: {e}")
    print("\n💡 Решение:")
    print("1. Перезапусти VPN")
    print("2. Попробуй другой VPN")
    print("3. Попробуй мобильный интернет")

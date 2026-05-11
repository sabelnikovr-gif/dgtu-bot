from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Конфигурация бота"""
    
    # 🔑 ТОКЕН БОТА
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8628225993:AAEvnCL9BWCN_zDUkta...")
    
    # 🌐 ПРОКСИ (если нужен)
    # Форматы:
    # • SOCKS5: "socks5://login:password@ip:port"
    # • HTTP: "http://login:password@ip:port"
    # • Без авторизации: "socks5://ip:port"
    PROXY_URL = "socks5://p180JC:Axk2MM@196.19.120.14:8000"
    # Если прокси не нужен:
    # PROXY_URL = None
    
    # 🤖 GIGACHAT
    GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID", "")
    GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET", "")
    GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    
    # 📁 ПУТИ
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    
    # 👨‍💻 АВТОР
    BOT_AUTHOR = "@sabelnikovr"

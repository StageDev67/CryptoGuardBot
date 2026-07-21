import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Класс конфигурации бота"""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
    
    # URL API CoinGecko
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Настройки базы данных
    DATABASE_PATH = "database/bot.db"
    
    # Настройки планировщика
    CHECK_INTERVAL_MINUTES = 5
    
    # Логирование
    LOG_FILE = "logs/bot.log"
    LOG_LEVEL = "INFO"

# Проверка наличия необходимых переменных
if not Config.BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")
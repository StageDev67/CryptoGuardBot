import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import Config
from handlers import (
    start_router,
    price_router,
    alerts_router,
    portfolio_router,
    callback_router
)
from utils import setup_scheduler
import os

# Настройка логирования
def setup_logging():
    """Настройка логирования"""
    log_dir = os.path.dirname(Config.LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()  # Вывод в консоль
        ]
    )
    
    # Устанавливаем уровень логирования для сторонних библиотек
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

async def main():
    """Главная функция запуска бота"""
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Инициализация бота
        bot = Bot(
            token=Config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        
        # Инициализация диспетчера
        dp = Dispatcher()
        
        # Регистрация роутеров
        dp.include_router(start_router)
        dp.include_router(price_router)
        dp.include_router(alerts_router)
        dp.include_router(portfolio_router)
        dp.include_router(callback_router)
        
        # Запуск планировщика для фоновых задач
        scheduler = setup_scheduler(bot)
        
        logger.info("Бот успешно запущен!")
        
        # Запуск бота
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        raise
    finally:
        # Остановка планировщика при завершении
        if 'scheduler' in locals():
            scheduler.shutdown()
            logger.info("Планировщик остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
    except Exception as e:
        logging.error(f"Неожиданная ошибка: {e}")
        raise
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot
import logging
from datetime import datetime
from config import Config
from database import Database
from utils import CoinGeckoAPI

logger = logging.getLogger(__name__)

# Инициализация
db = Database(Config.DATABASE_PATH)
coingecko = CoinGeckoAPI(Config.COINGECKO_API_KEY, Config.COINGECKO_BASE_URL)

async def check_alerts(bot: Bot):
    """
    Фоновая задача для проверки алертов
    Запускается каждые 5 минут
    """
    try:
        # Получаем все активные алерты
        alerts = db.get_all_active_alerts()
        
        if not alerts:
            return
        
        logger.info(f"Проверка алертов: {len(alerts)} активных")
        
        # Группируем алерты по монетам
        alerts_by_coin = {}
        for alert in alerts:
            coin = alert['coin_symbol']
            if coin not in alerts_by_coin:
                alerts_by_coin[coin] = []
            alerts_by_coin[coin].append(alert)
        
        # Проверяем цены для каждой монеты
        for coin_symbol, coin_alerts in alerts_by_coin.items():
            try:
                # Получаем текущую цену
                price_data = await coingecko.get_price(coin_symbol)
                
                if price_data is None:
                    logger.warning(f"Не удалось получить цену для {coin_symbol}")
                    continue
                
                current_price = price_data.get('usd', 0)
                if current_price <= 0:
                    continue
                
                # Проверяем каждый алерт для этой монеты
                for alert in coin_alerts:
                    await check_single_alert(bot, alert, current_price)
                    
            except Exception as e:
                logger.error(f"Ошибка проверки алертов для {coin_symbol}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка в фоновой задаче проверки алертов: {e}")

async def check_single_alert(bot: Bot, alert: dict, current_price: float):
    """Проверка одного алерта"""
    try:
        alert_id = alert['id']
        user_id = alert['user_id']
        threshold = alert['threshold']
        direction = alert['direction']
        coin_symbol = alert['coin_symbol']
        
        # Проверяем условие
        triggered = False
        if direction == 'above' and current_price >= threshold:
            triggered = True
        elif direction == 'below' and current_price <= threshold:
            triggered = True
        
        if triggered:
            # Отправляем уведомление
            direction_text = "выше" if direction == 'above' else "ниже"
            direction_emoji = "⬆️" if direction == 'above' else "⬇️"
            
            message = (
                f"🔔 **Уведомление!**\n\n"
                f"{direction_emoji} Цена {coin_symbol.upper()} {direction_text} ${threshold:,.2f}\n"
                f"💰 Текущая цена: ${current_price:,.2f}\n\n"
                f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            try:
                await bot.send_message(user_id, message)
                logger.info(f"Отправлено уведомление пользователю {user_id} для {coin_symbol}")
                
                # Обновляем время последнего срабатывания
                db.update_alert_triggered(alert_id)
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка проверки алерта {alert.get('id')}: {e}")

def setup_scheduler(bot: Bot):
    """Настройка и запуск планировщика"""
    scheduler = AsyncIOScheduler()
    
    # Добавляем задачу проверки алертов
    scheduler.add_job(
        check_alerts,
        trigger=IntervalTrigger(minutes=Config.CHECK_INTERVAL_MINUTES),
        args=[bot],
        id='check_alerts',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Планировщик запущен, интервал проверки: {Config.CHECK_INTERVAL_MINUTES} минут")
    
    return scheduler
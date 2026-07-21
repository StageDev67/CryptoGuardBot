import sqlite3
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица для уведомлений (алертов)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        coin_symbol TEXT NOT NULL,
                        threshold REAL NOT NULL,
                        direction TEXT NOT NULL CHECK(direction IN ('above', 'below')),
                        is_active INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_triggered TIMESTAMP,
                        UNIQUE(user_id, coin_symbol, threshold, direction)
                    )
                ''')
                
                # Таблица для портфеля
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        coin_symbol TEXT NOT NULL,
                        amount REAL NOT NULL,
                        purchase_price REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, coin_symbol)
                    )
                ''')
                
                conn.commit()
                logger.info("База данных успешно инициализирована")
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def add_alert(self, user_id: int, coin_symbol: str, threshold: float, direction: str) -> bool:
        """Добавление нового алерта"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO alerts 
                    (user_id, coin_symbol, threshold, direction, is_active, created_at)
                    VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ''', (user_id, coin_symbol.upper(), threshold, direction))
                conn.commit()
                logger.info(f"Добавлен алерт для user_id={user_id}, coin={coin_symbol}, threshold={threshold}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка добавления алерта: {e}")
            return False
    
    def remove_alert(self, user_id: int, alert_id: int) -> bool:
        """Удаление алерта"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM alerts 
                    WHERE id = ? AND user_id = ?
                ''', (alert_id, user_id))
                conn.commit()
                logger.info(f"Удален алерт id={alert_id} для user_id={user_id}")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления алерта: {e}")
            return False
    
    def get_user_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение всех активных алертов пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, coin_symbol, threshold, direction, is_active, created_at, last_triggered
                    FROM alerts 
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                ''', (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения алертов: {e}")
            return []
    
    def get_all_active_alerts(self) -> List[Dict[str, Any]]:
        """Получение всех активных алертов для фоновой проверки"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, user_id, coin_symbol, threshold, direction
                    FROM alerts 
                    WHERE is_active = 1
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения всех алертов: {e}")
            return []
    
    def update_alert_triggered(self, alert_id: int):
        """Обновление времени последнего срабатывания алерта"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE alerts 
                    SET last_triggered = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (alert_id,))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления алерта: {e}")
    
    def add_portfolio_item(self, user_id: int, coin_symbol: str, amount: float, purchase_price: float = None) -> bool:
        """Добавление монеты в портфель"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO portfolio 
                    (user_id, coin_symbol, amount, purchase_price, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, coin_symbol.upper(), amount, purchase_price))
                conn.commit()
                logger.info(f"Добавлена монета в портфель: user_id={user_id}, coin={coin_symbol}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка добавления в портфель: {e}")
            return False
    
    def remove_portfolio_item(self, user_id: int, coin_symbol: str) -> bool:
        """Удаление монеты из портфеля"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM portfolio 
                    WHERE user_id = ? AND coin_symbol = ?
                ''', (user_id, coin_symbol.upper()))
                conn.commit()
                logger.info(f"Удалена монета из портфеля: user_id={user_id}, coin={coin_symbol}")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления из портфеля: {e}")
            return False
    
    def get_portfolio(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение портфеля пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, coin_symbol, amount, purchase_price, created_at
                    FROM portfolio 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения портфеля: {e}")
            return []
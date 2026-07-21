import aiohttp
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class CoinGeckoAPI:
    """Клиент для работы с CoinGecko API"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'x-cg-demo-api-key': api_key,
            'accept': 'application/json'
        }
    
    async def get_price(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение текущей цены криптовалюты
        
        Args:
            coin_id: ID монеты (например, 'bitcoin', 'ethereum')
        
        Returns:
            Словарь с данными о цене или None в случае ошибки
        """
        # ПРИВОДИМ К НИЖНЕМУ РЕГИСТРУ
        coin_id = coin_id.lower()
        
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if coin_id in data:
                            return data[coin_id]
                        else:
                            logger.warning(f"Монета {coin_id} не найдена в ответе API")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка API CoinGecko: {response.status} - {error_text}")
                        return None
                        
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка соединения с CoinGecko API: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении цены: {e}")
            return None
    
    async def search_coin(self, query: str) -> List[Dict[str, Any]]:
        """
        Поиск монеты по названию или символу
        
        Args:
            query: Поисковый запрос
        
        Returns:
            Список найденных монет
        """
        try:
            url = f"{self.base_url}/search"
            params = {'query': query}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('coins', [])
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка поиска монеты: {response.status} - {error_text}")
                        return []
                        
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка соединения при поиске: {e}")
            return []
        except Exception as e:
            logger.error(f"Неожиданная ошибка при поиске: {e}")
            return []
    
    async def get_supported_coins(self) -> List[str]:
        """Получение списка поддерживаемых монет"""
        # Для упрощения вернем популярные монеты
        return ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana', 
                'ripple', 'polkadot', 'dogecoin', 'avalanche-2', 'chainlink']
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import Config
from utils import CoinGeckoAPI
from keyboards import get_back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

class PriceState(StatesGroup):
    """Состояния для получения цены"""
    waiting_for_coin = State()

# Инициализация API
coingecko = CoinGeckoAPI(Config.COINGECKO_API_KEY, Config.COINGECKO_BASE_URL)

@router.message(Command("price"))
async def cmd_price(message: types.Message, state: FSMContext):
    """Обработчик команды /price"""
    args = message.text.split(maxsplit=1)
    
    if len(args) > 1:
        # Если указан символ в команде
        coin_symbol = args[1].strip().lower()
        await get_price(message, coin_symbol)
    else:
        # Если символ не указан, запрашиваем
        await message.answer(
            "Введите символ криптовалюты (например: bitcoin, ethereum):",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(PriceState.waiting_for_coin)

@router.message(PriceState.waiting_for_coin)
async def process_coin_input(message: types.Message, state: FSMContext):
    """Обработка ввода символа монеты"""
    coin_symbol = message.text.strip().lower()
    await get_price(message, coin_symbol)
    await state.clear()

async def get_price(message: types.Message, coin_symbol: str):
    """Получение и отображение цены монеты"""
    try:
        # Получаем цену
        price_data = await coingecko.get_price(coin_symbol)
        
        if price_data is None:
            await message.answer(
                f"❌ Монета '{coin_symbol}' не найдена\n\n"
                f"Проверьте правильность написания или используйте ID монеты",
                reply_markup=get_back_keyboard()
            )
            return
        
        # Форматируем ответ
        price_usd = price_data.get('usd', 0)
        change_24h = price_data.get('usd_24h_change', 0)
        market_cap = price_data.get('usd_market_cap', 0)
        volume_24h = price_data.get('usd_24h_vol', 0)
        
        # Эмодзи для изменения цены
        change_emoji = "📈" if change_24h >= 0 else "📉"
        change_sign = "+" if change_24h >= 0 else ""
        
        response = f"""
💰 **{coin_symbol.upper()}**

💵 Цена: **${price_usd:,.2f}**
{change_emoji} Изменение за 24ч: {change_sign}{change_24h:.2f}%
💹 Рыночная капитализация: ${market_cap:,.0f}
📊 Объем торгов (24ч): ${volume_24h:,.0f}

📅 Обновлено: сейчас
        """
        
        await message.answer(response, reply_markup=get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка получения цены для {coin_symbol}: {e}")
        await message.answer(
            "❌ Произошла ошибка при получении цены. Попробуйте позже",
            reply_markup=get_back_keyboard()
        )
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from config import Config
from utils import CoinGeckoAPI
from keyboards.inline import get_portfolio_actions_keyboard, get_back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

class PortfolioState(StatesGroup):
    """Состояния для управления портфелем"""
    waiting_for_add_coin = State()
    waiting_for_add_amount = State()
    waiting_for_add_price = State()
    waiting_for_remove_coin = State()

# Инициализация базы данных и API
db = Database(Config.DATABASE_PATH)
coingecko = CoinGeckoAPI(Config.COINGECKO_API_KEY, Config.COINGECKO_BASE_URL)

@router.message(Command("portfolio"))
async def cmd_portfolio(message: types.Message):
    """Показать портфель пользователя"""
    user_id = message.from_user.id
    portfolio = db.get_portfolio(user_id)
    
    if not portfolio:
        await message.answer(
            "📊 Ваш портфель пуст\n\n"
            "Добавьте монеты с помощью кнопок ниже или командой /portfolio_add",
            reply_markup=get_portfolio_actions_keyboard(),
            parse_mode=None  # Отключаем парсинг Markdown
        )
        return
    
    # Получаем актуальные цены для всех монет
    total_value = 0
    portfolio_text = "📊 *Ваш криптопортфель*\n\n"
    
    for item in portfolio:
        coin = item['coin_symbol']
        amount = item['amount']
        purchase_price = item.get('purchase_price')
        
        # Получаем текущую цену
        price_data = await coingecko.get_price(coin)
        current_price = price_data.get('usd', 0) if price_data else 0
        
        value = amount * current_price
        total_value += value
        
        # Расчет прибыли/убытка
        if purchase_price:
            profit = (current_price - purchase_price) * amount
            profit_percent = ((current_price - purchase_price) / purchase_price) * 100 if purchase_price > 0 else 0
            profit_emoji = "📈" if profit >= 0 else "📉"
            profit_text = f"{profit_emoji} {profit:+,.2f} USD ({profit_percent:+.2f}%)"
        else:
            profit_text = "ℹ️ Цена покупки не указана"
        
        portfolio_text += (
            f"🪙 *{coin.upper()}*\n"
            f"   Количество: {amount:.4f}\n"
            f"   Цена: ${current_price:,.2f}\n"
            f"   Стоимость: ${value:,.2f}\n"
            f"   {profit_text}\n\n"
        )
    
    portfolio_text += f"💰 *Общая стоимость: ${total_value:,.2f}*"
    
    await message.answer(
        portfolio_text,
        reply_markup=get_portfolio_actions_keyboard(),
        parse_mode="Markdown"  # Включаем Markdown только для этого сообщения
    )

# ===== НОВАЯ КОМАНДА /portfolio_add =====
@router.message(Command("portfolio_add"))
async def cmd_portfolio_add(message: types.Message, state: FSMContext):
    """Обработчик команды /portfolio_add"""
    await message.answer(
        "➕ *Добавление монеты в портфель*\n\n"
        "Введите символ монеты (например: bitcoin, ethereum):",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(PortfolioState.waiting_for_add_coin)

@router.callback_query(lambda c: c.data == "portfolio_add")
async def process_portfolio_add(callback: types.CallbackQuery, state: FSMContext):
    """Добавление монеты в портфель (из инлайн-кнопки)"""
    await callback.answer()
    
    await callback.message.edit_text(
        "➕ *Добавление монеты в портфель*\n\n"
        "Введите символ монеты (например: bitcoin, ethereum):",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(PortfolioState.waiting_for_add_coin)

@router.message(PortfolioState.waiting_for_add_coin)
async def process_add_coin(message: types.Message, state: FSMContext):
    """Ввод символа монеты для добавления"""
    coin_symbol = message.text.strip().lower()
    
    # Проверяем, существует ли монета
    price_data = await coingecko.get_price(coin_symbol)
    if price_data is None:
        await message.answer(
            f"❌ Монета '{coin_symbol}' не найдена. Попробуйте снова:",
            reply_markup=get_back_keyboard(),
            parse_mode=None
        )
        return
    
    await state.update_data(coin=coin_symbol)
    
    await message.answer(
        f"💰 Монета: {coin_symbol.upper()}\n"
        "Введите количество монет:",
        reply_markup=get_back_keyboard(),
        parse_mode=None
    )
    
    await state.set_state(PortfolioState.waiting_for_add_amount)

@router.message(PortfolioState.waiting_for_add_amount)
async def process_add_amount(message: types.Message, state: FSMContext):
    """Ввод количества монет"""
    try:
        amount = float(message.text.strip())
        
        if amount <= 0:
            await message.answer(
                "❌ Количество должно быть больше 0. Попробуйте снова:",
                reply_markup=get_back_keyboard(),
                parse_mode=None
            )
            return
        
        await state.update_data(amount=amount)
        
        await message.answer(
            "💰 Введите цену покупки (в USD) или '0' если не хотите указывать:",
            reply_markup=get_back_keyboard(),
            parse_mode=None
        )
        
        await state.set_state(PortfolioState.waiting_for_add_price)
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число. Попробуйте снова:",
            reply_markup=get_back_keyboard(),
            parse_mode=None
        )

@router.message(PortfolioState.waiting_for_add_price)
async def process_add_price(message: types.Message, state: FSMContext):
    """Ввод цены покупки"""
    try:
        purchase_price = float(message.text.strip())
        
        # Если пользователь ввел 0, не сохраняем цену
        if purchase_price == 0:
            purchase_price = None
        
        data = await state.get_data()
        user_id = message.from_user.id
        
        # Сохраняем в базу
        if db.add_portfolio_item(user_id, data['coin'], data['amount'], purchase_price):
            await message.answer(
                f"✅ Монета {data['coin'].upper()} успешно добавлена в портфель\n\n"
                f"Количество: {data['amount']:.4f}\n"
                f"Цена покупки: {'не указана' if purchase_price is None else f'${purchase_price:,.2f}'}",
                reply_markup=get_back_keyboard(),
                parse_mode=None
            )
            
            logger.info(f"Пользователь {user_id} добавил в портфель {data['coin']}")
        else:
            await message.answer(
                "❌ Не удалось добавить монету. Возможно, она уже есть в портфеле",
                reply_markup=get_back_keyboard(),
                parse_mode=None
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число. Попробуйте снова:",
            reply_markup=get_back_keyboard(),
            parse_mode=None
        )

@router.callback_query(lambda c: c.data == "portfolio_remove")
async def process_portfolio_remove(callback: types.CallbackQuery, state: FSMContext):
    """Удаление монеты из портфеля"""
    await callback.answer()
    
    user_id = callback.from_user.id
    portfolio = db.get_portfolio(user_id)
    
    if not portfolio:
        await callback.message.edit_text(
            "📊 Ваш портфель пуст. Нечего удалять",
            reply_markup=get_back_keyboard(),
            parse_mode=None
        )
        return
    
    # Создаем список монет для удаления
    coins_text = "🗑 *Удаление монеты из портфеля*\n\n"
    for i, item in enumerate(portfolio, 1):
        coins_text += f"{i}. {item['coin_symbol'].upper()} (Количество: {item['amount']:.4f})\n"
    
    coins_text += "\nВведите номер монеты для удаления:"
    
    await callback.message.edit_text(
        coins_text,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(PortfolioState.waiting_for_remove_coin)

@router.message(PortfolioState.waiting_for_remove_coin)
async def process_remove_coin(message: types.Message, state: FSMContext):
    """Обработка выбора монеты для удаления"""
    try:
        index = int(message.text.strip()) - 1
        user_id = message.from_user.id
        portfolio = db.get_portfolio(user_id)
        
        if 0 <= index < len(portfolio):
            coin_to_remove = portfolio[index]['coin_symbol']
            
            if db.remove_portfolio_item(user_id, coin_to_remove):
                await message.answer(
                    f"✅ Монета {coin_to_remove.upper()} удалена из портфеля",
                    reply_markup=get_back_keyboard(),
                    parse_mode=None
                )
                logger.info(f"Пользователь {user_id} удалил {coin_to_remove} из портфеля")
            else:
                await message.answer(
                    "❌ Не удалось удалить монету. Попробуйте позже",
                    reply_markup=get_back_keyboard(),
                    parse_mode=None
                )
        else:
            await message.answer(
                "❌ Неверный номер. Попробуйте снова:",
                reply_markup=get_back_keyboard(),
                parse_mode=None
            )
            return
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Введите номер монеты. Попробуйте снова:",
            reply_markup=get_back_keyboard(),
            parse_mode=None
        )
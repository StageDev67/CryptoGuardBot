from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from config import Config
from utils import CoinGeckoAPI
from keyboards import get_alert_actions_keyboard, get_back_keyboard, get_coin_list_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

class AlertState(StatesGroup):
    """Состояния для управления уведомлениями"""
    waiting_for_coin = State()
    waiting_for_threshold = State()
    waiting_for_direction = State()
    waiting_for_remove = State()

# Инициализация базы данных и API
db = Database(Config.DATABASE_PATH)
coingecko = CoinGeckoAPI(Config.COINGECKO_API_KEY, Config.COINGECKO_BASE_URL)

# Новая функция для создания уведомления из обычной кнопки
async def start_alert_creation(message: types.Message):
    """Начало создания уведомления из обычной кнопки"""
    # Получаем список популярных монет
    coins = await coingecko.get_supported_coins()
    coin_symbols = [coin[:10] for coin in coins]
    
    await message.answer(
        "🔔 *Создание уведомления*\n\n"
        "Выберите монету для установки уведомления",
        reply_markup=get_coin_list_keyboard(coin_symbols),
        parse_mode="Markdown"
    )

@router.message(Command("alerts"))
async def cmd_alerts(message: types.Message, state: FSMContext):
    """Показать все уведомления пользователя"""
    user_id = message.from_user.id
    alerts = db.get_user_alerts(user_id)
    
    if not alerts:
        await message.answer(
            "📋 У вас нет активных уведомлений\n\n"
            "Чтобы создать уведомление, нажмите кнопку 'Установить уведомление' в главном меню",
            reply_markup=get_back_keyboard(),
            parse_mode=None
        )
        return
    
    alert_text = "📋 *Ваши уведомления*\n\n"
    for alert in alerts:
        direction_emoji = "⬆️" if alert['direction'] == 'above' else "⬇️"
        status = "✅ Активно" if alert['is_active'] else "⏸️ Неактивно"
        alert_text += (
            f"🆔 {alert['id']}: {direction_emoji} {alert['coin_symbol'].upper()} "
            f"{'выше' if alert['direction'] == 'above' else 'ниже'} ${alert['threshold']:,.2f}\n"
            f"   Статус: {status}\n\n"
        )
    
    alert_text += "Для удаления уведомления используйте /remove_alert [id]"
    
    await message.answer(
        alert_text,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )

@router.message(Command("remove_alert"))
async def cmd_remove_alert(message: types.Message):
    """Удаление уведомления по ID"""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "❌ Укажите ID уведомления для удаления\n"
            "Пример: /remove_alert 1",
            reply_markup=get_back_keyboard(),
            parse_mode=None
        )
        return
    
    try:
        alert_id = int(args[1])
        user_id = message.from_user.id
        
        if db.remove_alert(user_id, alert_id):
            await message.answer(
                f"✅ Уведомление #{alert_id} успешно удалено",
                reply_markup=get_back_keyboard(),
                parse_mode=None
            )
        else:
            await message.answer(
                f"❌ Уведомление #{alert_id} не найдено или уже удалено",
                reply_markup=get_back_keyboard(),
                parse_mode=None
            )
    except ValueError:
        await message.answer(
            "❌ ID должен быть числом.",
            reply_markup=get_back_keyboard(),
            parse_mode=None
        )

@router.callback_query(lambda c: c.data == "set_alert")
async def process_set_alert(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса создания уведомления из инлайн-кнопки"""
    await callback.answer()
    
    # Получаем список популярных монет
    coins = await coingecko.get_supported_coins()
    coin_symbols = [coin[:10] for coin in coins]
    
    await callback.message.edit_text(
        "🔔 *Создание уведомления*\n\n"
        "Выберите монету для установки уведомления",
        reply_markup=get_coin_list_keyboard(coin_symbols),
        parse_mode="Markdown"
    )
    
    await state.set_state(AlertState.waiting_for_coin)

@router.callback_query(lambda c: c.data.startswith("coin_"))
async def process_coin_selection(callback: types.CallbackQuery, state: FSMContext):
    """Выбор монеты для уведомления"""
    coin_symbol = callback.data.replace("coin_", "")
    await callback.answer()
    
    # Сохраняем выбранную монету
    await state.update_data(coin=coin_symbol)
    
    await callback.message.edit_text(
        f"💰 Выбрана монета: *{coin_symbol.upper()}*\n\n"
        "Теперь выберите направление уведомления:",
        reply_markup=get_alert_actions_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(AlertState.waiting_for_direction)

@router.callback_query(lambda c: c.data in ["alert_above", "alert_below"])
async def process_direction_selection(callback: types.CallbackQuery, state: FSMContext):
    """Выбор направления уведомления"""
    direction = "above" if callback.data == "alert_above" else "below"
    await callback.answer()
    
    await state.update_data(direction=direction)
    
    direction_text = "выше" if direction == "above" else "ниже"
    
    await callback.message.edit_text(
        f"📊 Выбрано: цена будет {direction_text} указанного порога\n\n"
        "Введите ценовой порог в USD (например: 50000):",
        reply_markup=get_back_keyboard(),
        parse_mode=None
    )
    
    await state.set_state(AlertState.waiting_for_threshold)

@router.message(AlertState.waiting_for_threshold)
async def process_threshold_input(message: types.Message, state: FSMContext):
    """Ввод ценового порога"""
    try:
        threshold = float(message.text.strip())
        
        if threshold <= 0:
            await message.answer(
                "❌ Порог должен быть больше 0. Попробуйте снова:",
                reply_markup=get_back_keyboard(),
                parse_mode=None
            )
            return
        
        # Получаем данные из состояния
        data = await state.get_data()
        coin = data.get('coin')
        direction = data.get('direction')
        user_id = message.from_user.id
        
        # Сохраняем алерт в базу
        if db.add_alert(user_id, coin, threshold, direction):
            direction_text = "выше" if direction == "above" else "ниже"
            
            await message.answer(
                f"✅ Уведомление успешно создано\n\n"
                f"📊 Монета: {coin.upper()}\n"
                f"📈 Условие: цена {direction_text} ${threshold:,.2f}\n\n"
                f"Вы получите уведомление, когда цена достигнет этого порога",
                reply_markup=get_back_keyboard(),
                parse_mode=None
            )
            
            logger.info(f"Пользователь {user_id} создал алерт для {coin}: {direction} {threshold}")
        else:
            await message.answer(
                "❌ Не удалось сохранить уведомление. Возможно, такое уведомление уже существует",
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
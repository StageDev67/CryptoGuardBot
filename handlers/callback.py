from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from keyboards import get_main_menu_keyboard, get_back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(lambda c: c.data == "back_to_menu")
async def process_back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await callback.answer()
    
    # Очищаем состояние
    await state.clear()
    
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(lambda c: c.data == "price")
async def process_price_menu(callback: types.CallbackQuery):
    """Переход в меню получения цены"""
    await callback.answer()
    
    await callback.message.edit_text(
        "💰 **Получение цены**\n\n"
        "Используйте команду /price [символ]\n"
        "Например: /price bitcoin\n\n"
        "Или введите символ монеты:",
        reply_markup=get_back_keyboard()
    )

@router.callback_query(lambda c: c.data == "my_alerts")
async def process_my_alerts(callback: types.CallbackQuery):
    """Показать уведомления пользователя"""
    await callback.answer()
    
    from handlers.alerts import cmd_alerts
    await cmd_alerts(callback.message, None)

@router.callback_query(lambda c: c.data == "portfolio")
async def process_portfolio_menu(callback: types.CallbackQuery):
    """Переход в меню портфеля"""
    await callback.answer()
    
    from handlers.portfolio import cmd_portfolio
    await cmd_portfolio(callback.message)

@router.callback_query(lambda c: c.data == "help")
async def process_help_menu(callback: types.CallbackQuery):
    """Показать справку"""
    await callback.answer()
    
    help_text = """
📖 **CryptoGuardBot - Помощь**

**Основные команды:**
/start - Главное меню
/price [символ] - Получить цену
/portfolio - Управление портфелем
/alerts - Управление уведомлениями
/help - Эта справка

**Уведомления:**
Устанавливайте ценовые пороги для отслеживания монет.
Бот пришлет уведомление при достижении цены.

**Портфель:**
Отслеживайте свои инвестиции.
Добавляйте монеты с количеством и ценой покупки.

**Популярные монеты:**
bitcoin, ethereum, binancecoin, cardano, solana, ripple, polkadot, dogecoin
    """
    
    await callback.message.edit_text(help_text, reply_markup=get_back_keyboard())
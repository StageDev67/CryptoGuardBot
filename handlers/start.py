from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from keyboards import get_main_menu_keyboard
import logging
import os

logger = logging.getLogger(__name__)
router = Router()

def get_reply_keyboard() -> ReplyKeyboardMarkup:
    """Обычная клавиатура (Reply Keyboard)"""
    buttons = [
        [
            KeyboardButton(text="💰 Цена монеты"),
            KeyboardButton(text="🔔 Установить уведомление")
        ],
        [
            KeyboardButton(text="📊 Мой портфель"),
            KeyboardButton(text="📋 Мои уведомления")
        ],
        [
            KeyboardButton(text="❓ Помощь")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,  # Автоматически подгонять размер
        one_time_keyboard=False  # Не скрывать после нажатия
    )

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start с картинкой и клавиатурами"""
    user_name = message.from_user.first_name or "Пользователь"
    
    welcome_text = (
        f"🪙 Привет, *{user_name}*\n\n"
        "Добро пожаловать в *CryptoGuardBot* - ваш помощник в мире криптовалют\n\n"
        "• Узнавайте актуальные цены\n"
        "• Устанавливайте уведомления о достижении цен\n"
        "• Ведите свой криптопортфель\n\n"
    )
    
    # Путь к картинке (создайте папку images и положите туда картинку)
    image_path = "images/welcome.png"
    
    # Проверяем, есть ли картинка
    if os.path.exists(image_path):
        # Отправляем картинку с подписью и обычной клавиатурой
        photo = FSInputFile(image_path)
        await message.answer_photo(
            photo=photo,
            caption=welcome_text,
            reply_markup=get_reply_keyboard()  # Обычная клавиатура
        )
        # Дополнительно отправляем инлайн-клавиатуру
        await message.answer(
            "📱 Используй кнопки ниже",
            reply_markup=get_main_menu_keyboard()  # Инлайн клавиатура
        )
    else:
        # Если картинки нет, отправляем только текст с двумя клавиатурами
        await message.answer(
            welcome_text,
            reply_markup=get_reply_keyboard()  # Обычная клавиатура
        )
        await message.answer(
            "📱 Используй кнопки ниже",
            reply_markup=get_main_menu_keyboard()  # Инлайн клавиатура
        )
    
    logger.info(f"Пользователь {message.from_user.id} запустил бота")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 *Справка по командам*\n\n"
        "/start - Главное меню\n"
        "/price [символ] - Получить цену монеты\n"
        "/portfolio - Управление портфелем\n"
        "/alerts - Управление уведомлениями\n"
        "/help - Показать эту справку\n\n"
        "*Примеры:*\n"
        "/price bitcoin\n"
        "/price eth\n\n"
        "*Популярные монеты:*\n"
        "bitcoin, ethereum, binancecoin, cardano, solana, ripple, polkadot, dogecoin"
    )
    
    await message.answer(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )
    
    logger.info(f"Пользователь {message.from_user.id} запросил справку")

# Обработчик для обычных кнопок (Reply Keyboard)
@router.message(lambda message: message.text == "💰 Цена монеты")
async def handle_price_button(message: types.Message):
    """Обработка кнопки 'Цена монеты'"""
    await message.answer(
        "💰 Введите символ криптовалюты (например: bitcoin, ethereum):",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(lambda message: message.text == "🔔 Установить уведомление")
async def handle_alert_button(message: types.Message):
    """Обработка кнопки 'Установить уведомление'"""
    from handlers.alerts import start_alert_creation
    
    # Вызываем функцию создания уведомления без редактирования
    await start_alert_creation(message)

@router.message(lambda message: message.text == "📊 Мой портфель")
async def handle_portfolio_button(message: types.Message):
    """Обработка кнопки 'Мой портфель'"""
    from handlers.portfolio import cmd_portfolio
    await cmd_portfolio(message)

@router.message(lambda message: message.text == "📋 Мои уведомления")
async def handle_my_alerts_button(message: types.Message):
    """Обработка кнопки 'Мои уведомления'"""
    from handlers.alerts import cmd_alerts
    await cmd_alerts(message, None)

@router.message(lambda message: message.text == "❓ Помощь")
async def handle_help_button(message: types.Message):
    """Обработка кнопки 'Помощь'"""
    await cmd_help(message)
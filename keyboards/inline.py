from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню с кнопками"""
    buttons = [
        [InlineKeyboardButton(text="💰 Цена монеты", callback_data="price")],
        [InlineKeyboardButton(text="🔔 Установить уведомление", callback_data="set_alert")],
        [InlineKeyboardButton(text="📊 Мой портфель", callback_data="portfolio")],
        [InlineKeyboardButton(text="📋 Мои уведомления", callback_data="my_alerts")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_alert_actions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для управления уведомлениями"""
    buttons = [
        [InlineKeyboardButton(text="⬆️ Выше", callback_data="alert_above")],
        [InlineKeyboardButton(text="⬇️ Ниже", callback_data="alert_below")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_portfolio_actions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для управления портфелем"""
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить монету", callback_data="portfolio_add")],
        [InlineKeyboardButton(text="➖ Удалить монету", callback_data="portfolio_remove")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_coin_list_keyboard(coins: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура со списком монет"""
    buttons = []
    for coin in coins:
        buttons.append([InlineKeyboardButton(text=coin.upper(), callback_data=f"coin_{coin}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
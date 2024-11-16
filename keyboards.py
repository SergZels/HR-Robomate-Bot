from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

#-------------------start-------------------------------
start_Keyboard = InlineKeyboardBuilder()
start_Keyboard.add(types.InlineKeyboardButton(text="Work UA", callback_data="workua"))
start_Keyboard.add(types.InlineKeyboardButton(text="Robota UA (в розробці)", callback_data="robotaua"))
start_Keyboard.adjust(1)

#----------------experience----------------------------
experience = InlineKeyboardBuilder()
experience.add(types.InlineKeyboardButton(text="Без досвіду", callback_data="Без досвіду"))
experience.add(types.InlineKeyboardButton(text="До 1 року", callback_data="До 1 року"))
experience.add(types.InlineKeyboardButton(text="Від 1 до 2 років", callback_data="Від 1 до 2 років"))
experience.add(types.InlineKeyboardButton(text="Від 2 до 5 років", callback_data="Від 2 до 5 років"))
experience.add(types.InlineKeyboardButton(text="Понад 5 років", callback_data="Понад 5 років"))
experience.add(types.InlineKeyboardButton(text="Усі варіанти", callback_data="Усі варіанти"))
experience.adjust(1)

#------------------location-----------------------------------

location_keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [types.KeyboardButton(text="Вся Україна (віддалено)")]
    ]
)

#------------------age-----------------------------------

age_keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [types.KeyboardButton(text="Будь який")]
    ]
)

#------------------salary-----------------------------------

salary_keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [types.KeyboardButton(text="Будь яка")]
    ]
)

def build_keyboard(url: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Переглянути на сайті", url=url))
    return builder.as_markup()


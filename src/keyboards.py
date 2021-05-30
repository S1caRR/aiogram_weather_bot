from aiogram import types


first_weather_now_kb = types.InlineKeyboardMarkup(row_width=1)

button1 = types.InlineKeyboardButton(text='Выбрать город 🏢', callback_data='change_city')

first_weather_now_kb.add(button1)


weather_now_kb = types.InlineKeyboardMarkup(row_width=1)

button1 = types.InlineKeyboardButton(text='Изменить город 🏢', callback_data='change_city')
button2 = types.InlineKeyboardButton(text='Узнать данные о погоде ⛅', callback_data='weather_now')

weather_now_kb.add(button1, button2)
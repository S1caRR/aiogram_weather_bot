from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import db_worker
from config import BOT_TOKEN, OWM_TOKEN, owm_config
from utils import States
from keyboards import first_weather_now_kb, weather_now_kb

from pyowm import OWM
from pyowm.commons.exceptions import APIResponseError, NotFoundError


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

owm = OWM(OWM_TOKEN, config=owm_config)
mgr = owm.weather_manager()

MESSAGES = {'start': 'Привет 👋🏻! Я простенький бот, который поможет тебе узнать погодную обстановку на улице. Используй'
                     ' /help для того, чтобы посмотреть список команд',
            'help': 'Вот мой скромный функционал: \n\n/weather_info - узнать данные о погоде сейчас',
            'city not found': 'Город не найден. Попробуй ввести название города снова',
            'city changed': 'Отлично! Город изменен на ',
            'response error': 'Что-то пошло не так. Возможно API не отвечает. Попробуй позже',
            'weather info': '☁ Данные о погоде сейчас ☁\nУ тебя выбран город {0}, что ты хочешь сделать?',
            'enter city': 'Введи название города:',
            'no city': '☁ Данные о погоде сейчас ☁\nДля начала работы выбери город',
            'any message': 'Я тебя не понимаю 😔\nИспользуй /help, чтобы узнать список доступных команд',
            'try again': 'Если снова захочешь узнать погоду, используй команду /weather_info'
            }


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply(MESSAGES['start'])


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply(MESSAGES['help'])


@dp.message_handler(commands=['weather_info'])
async def process_weather_info_command(message: types.Message):
    try:
        city = db_worker.get_users_city(message.from_user.id)
        await bot.send_message(message.from_user.id, MESSAGES['weather info'].format(city), reply_markup=weather_now_kb)
    except KeyError:
        await bot.send_message(message.from_user.id, MESSAGES['no city'], reply_markup=first_weather_now_kb)


@dp.callback_query_handler(lambda call: call.data)
async def weather_info_query_handler(callback_query: types.CallbackQuery):
    if callback_query.data == 'weather_now':
        try:
            city = db_worker.get_users_city(callback_query.from_user.id)

            observation = mgr.weather_at_place(city)
            weather = observation.weather

            detailed_status = weather.detailed_status
            temp = f"{weather.temp['temp'] - 273.15:.1f}"
            temp_feels_like = f"{weather.temp['feels_like'] - 273.15:.1f}"
            humidity = weather.humidity
            pressure = f"{weather.pressure['press'] / 1.333:.1f}"

            dirs = ["северный", "северо-восточный", "восточный", "юго-восточный",
                    "южный", "юго-западный", "южный", "северо-западный"]
            wind_dir = dirs[round(weather.wnd['deg'] / 45) % 8]
            wind_speed = f"{weather.wnd['speed']:.1f}"

            weather_message = f'Сейчас в городе {city} {detailed_status}\n' \
                      f'Температура {temp}℃, ощущается как {temp_feels_like}℃\n' \
                      f'Влажность {humidity}%, давление {pressure} мм. рт. ст.\n' \
                      f'Ветер {wind_dir}, скорость ветра {wind_speed} м/с'

            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        text='☁ Данные о погоде сейчас ☁')
            await bot.send_message(callback_query.from_user.id, weather_message)
            await bot.send_message(callback_query.from_user.id, MESSAGES['try again'])
        except APIResponseError:
            await bot.send_message(callback_query.from_user.id, MESSAGES['response error'])

    elif callback_query.data == 'change_city':
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text='Смена города 🏢')
        await States.enter_city_name.set()
        await bot.send_message(callback_query.from_user.id, MESSAGES['enter city'])


@dp.message_handler(state=States.enter_city_name)
async def entry_city(message: types.Message, state: FSMContext):
    city = message.text.title()
    try:
        mgr.weather_at_place(city)

        db_worker.change_users_city(message.from_user.id, city)

        await state.finish()
        await message.reply(MESSAGES['city changed'] + city)
        await bot.send_message(message.from_user.id, MESSAGES['weather info'].format(city), reply_markup=weather_now_kb)
    except NotFoundError:
        await message.reply(MESSAGES['city not found'])
    except APIResponseError:
        await message.reply(MESSAGES['response error'])


@dp.message_handler()
async def entry_city(message: types.Message):
    await bot.send_video(message.from_user.id, 'https://vk.com/doc88969835_596353553?hash=94a78fbc18d2f4cfe2&dl=fd0ac04724ee744d50&wnd=1&module=im&mp4=1')
    await bot.send_message(message.from_user.id, MESSAGES['any message'])


async def shutdown(dp: Dispatcher):
    await dp.storage.close()
    await dp.storage.wait_closed()


if __name__ == "__main__":
    executor.start_polling(dp, on_shutdown=shutdown)

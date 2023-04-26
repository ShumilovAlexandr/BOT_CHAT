# -*- coding: windows-1251 -*-
import os
import requests
import datetime

from aiogram import (types, 
                     executor,
                     Bot, 
                     Dispatcher)
from aiogram.types import (InlineKeyboardMarkup, 
                           InlineKeyboardButton)
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import (StatesGroup, 
                                              State)
from dotenv import load_dotenv


load_dotenv()

# Объект бота и передаваемый токен
bot = Bot(os.getenv('TOKEN'))
# Ключ к API Openweather
API_KEY = os.getenv('WEATHER_API')
# Ключ к Exchange Rates Data API
exchange_key = os.getenv('EXCHANGE')
# Ключ к The Cat API - Cats as a Service.
animal_token = os.getenv('ANIMALS')

# Диспетчер для обработки сообщений, запросов и тп.
dp = Dispatcher(bot, storage=MemoryStorage())


class DataConversion(StatesGroup):
    # Здесь будут храниться состояния пользователя в текущий момент при конвертации
    first_currency = State()
    second_currency = State()
    amount_currency = State()

class DataWeather(StatesGroup):
    # Здесь будут храниться состояния пользователя в текущий момент при выборе города
    # для последующей передаче в функцию получения погоды
    city = State()


@dp.message_handler(commands=['start'])
async def start_bot(message: types.Message):
    """
    Стартовое приветсвие и запуск бота.

    Выводит кнопку, нажав на которую бот выдает в чат приветствие и предлагает на выбор одно из 
    действий в виде кнопок.
    btn1: после нажатия на нее можно выбрать погоду в интересующем городе.
    btn2: после нажатия на нее дает возможность конвертировать валюту.
    btn3: после нажатия на нее просто присылает в чат картику животного
    btn4: создает опрос с вариантами ответа и посылает в определенный чат.
    markup: выводит кнопки на экран бота.
    """
    btn1 = InlineKeyboardButton('Покажи мне погоду в ...', 
                                callback_data='btn1')
    btn2 = InlineKeyboardButton('Мне нужно конвертировать валюту', 
                                callback_data='btn2')
    btn3 = InlineKeyboardButton('Пришли мне картинку животинки', 
                                callback_data='btn3')
    btn4 = InlineKeyboardButton('Я хочу создать опрос', 
                                callback_data='btn4')
    markup = InlineKeyboardMarkup(row_width=1).add(btn1, btn2, btn3, btn4)
    await message.answer('Привет! Выбери одно из интересующих тебя действий.', 
                        reply_markup=markup)


@dp.callback_query_handler(lambda callback: True)
async def process_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Функция обработки результатов выбора той или иной кнопки.
    """
    match callback.data:
        case 'btn1':
            await get_city(callback.message, state=state)
        case 'btn2':
            await check_currency_1(callback.message, state=state)
        case 'btn3':
            await send_cat(callback.message)
        case 'btn4':
            await create_poll(callback.message)


# Функционал, отвечающий за прогноз погоды.
@dp.message_handler()
async def get_city(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, 
                           "Введите название города, в котором хотите узнать погоду: ")
    await state.set_state(DataWeather.city)

@dp.message_handler(state=DataWeather.city)
async def get_weather(message: types.Message, state: FSMContext):
    """Функция отвечает за получение прогноза погоды в интересующем городе."""
    try:
         city_name = message.text
         await state.update_data(city=city_name)
         # Запрос к API Openweathermap
         request = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={API_KEY}&units=metric&lang=ru')
         response = request.json()
         # Интересующие параметры в ответе
         date = datetime.datetime.now().strftime('%d.%m.%y г. %H:%M')
         town = response['name']
         current_temp = response['main']['temp']
         humidity = response['main']['humidity']
         pressure = response['main']['pressure']
         wind_speed = response['wind']['speed']
         res = f"Текущая дата в городе {town}: {date} \n \U0001F3D9  Текущая погода в городе {town} :\n  \U0001F321  Температура: {current_temp} °C,\n  \U0001F4A7 Влажность: {humidity} %,\n  \U0001F300  Давление: {pressure} мм.рт.ст, \n \U0001F32C  Скорость ветра {wind_speed} м/с"
         await bot.send_message(message.chat.id, res)
         await state.finish()
         
    # Обработка исключения в случае некорректного ввода данных
    except:
        await bot.send_message(message.chat.id,'Ошибка в названии города, либо такого города не существует.')


# Далее функционал, отвечающий за конвертацию валюты.
@dp.message_handler()
async def check_currency_1(message: types.Message, state: FSMContext):
    """Хендлер для ввода валюты которую нужно конвертировать."""
    await bot.send_message(message.chat.id, 
                           "Укажите на английском языке трехбуквенный тикер валюты, ИЗ которой хотите конвертировать: ")
    await state.set_state(DataConversion.first_currency)

@dp.message_handler(state=DataConversion.first_currency)
async def check_currency_2(message: types.Message, state: FSMContext):
    """Хендлер для ввода валюты в которую нужно конвертировать."""
    # Сохраняем состояние из прошлого хендлера, где вводили валюту из которой конвертируем.
    first_cur = message.text
    await state.update_data(first_currency=first_cur)
    await bot.send_message(message.chat.id, 
                           "Укажите на английском языке трехбуквенный тикер валюты, В которую хотите конвертировать: ")
    await state.set_state(DataConversion.second_currency)

@dp.message_handler(state=DataConversion.second_currency)
async def check_amount(message: types.Message, state: FSMContext):
    """Хендлер для ввода количества валюты которую нужно конвертировать."""
    # Сохраняем состояние из прошлого хендлера, где вводили валюту в которую конвертируем.
    second_cur = message.text
    await state.update_data(second_currency=second_cur)
    await bot.send_message(message.chat.id, 
                                   "Укажите необходимое количество валюты: ")
    await state.set_state(DataConversion.amount_currency)

async def get_connection(state: FSMContext):
    """Функция для установки соединения."""
    try:
        data = await state.get_data()
        first_cur = data.get('first_currency')
        second_cur = data.get('second_currency')
        amount_cur = data.get('amount_currency')
        if first_cur and second_cur and amount_cur:
            link = f"https://api.apilayer.com/exchangerates_data/convert?to={second_cur}&from={first_cur}&amount={amount_cur}&api_key={exchange_key}"

            # Передаваемые в запросе заголовки, в данном случае - ключ API
            header = {
                "apikey": exchange_key
            }
            resp = requests.get(link, headers=header)
            res = resp.json()
            return res
        else:
            print('Ошибка в аргументах!')
    except:
        print("Ошибка в запросе к API!")

@dp.message_handler(state=DataConversion.amount_currency)
async def get_result(message: types.Message, state: FSMContext):
    """Здесь выводится собственно говоря вся информация о конвертируемой валюте."""
    # Сохраняем состояние из прошлого хендлера, где вводили количество валюты.
    amount_cur = message.text
    await state.update_data(amount_currency=amount_cur)
    conn = await get_connection(state=state)
    date = datetime.datetime.now().strftime('%d.%m.%y г. %H:%M')
    # Тут в переменные сохраняем получаемые из запроса в get_connection данные
    first_cur = conn['query']['from']
    second_cur = conn['query']['to']
    amount = conn['query']['amount']
    total = conn['result']
    # Выводим результат работы
    msg = str(f"Текущая дата и время: {date} \U0001F4C5 \n Валюта, ИЗ которой нужно конвертировать: {first_cur} \U0001F3E6 \n Валюта, В которую нужно конвертировать: {second_cur} \U0001F3E6 \n Количество денежных единиц к конвертации: {amount} \U0001F51F \n Количество {second_cur} при конвертации {amount} {first_cur} в {second_cur} по текущему курсу составляет {total} \U00002705")
    await bot.send_message(message.chat.id, msg)
    await state.finish()


# Далее функционал, отвечающий за получение картинок.
async def get_photo():
    """Получение ссылки на картинки с животными."""
    try:
        link = f'https://api.thecatapi.com/v1/images/search?limit=1&api_key={animal_token}'
        request = requests.get(link)
        res = request.json()
        pict = res[0]['url']
    except:
        print("Ошибка в запросе к API!")
    return pict

@dp.message_handler()
async def send_cat(message: types.Message):
    await bot.send_photo(chat_id=message.chat.id,
                         photo=await get_photo())


# Функционал, отвечающий за создание опроса и отправку его в групповой чат
@dp.message_handler()
async def create_poll(message: types.Message):
    # Здесь нужно передавать список вариантов ответов
    options = ["Вариант 1", "Вариант 2", "Вариант 3"]
    # Здесь создаем объект опроса
    poll = types.Poll(
    question = "Выбери понравившийся вариант ответа",
    options = options,
    is_anonymous = True    
    )
    await bot.send_poll(chat_id=message.chat.id, 
                        question=poll.question, 
                        options=poll.options)


if __name__ == '__main__':
    executor.start_polling(dp)

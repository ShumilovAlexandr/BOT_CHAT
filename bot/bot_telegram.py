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

# Создаем экземпляр бота
bot = Bot(os.getenv('TOKEN'))
# Подключаем API Openweather
API_KEY = os.getenv('WEATHER_API')
# Подключаем Exchange Rates Data API
exchange_key = os.getenv('EXCHANGE')
# Подключаем The Cat API - Cats as a Service.
animal_token = os.getenv('ANIMALS')

# Объект диспетчера.
dp = Dispatcher(bot, storage=MemoryStorage())


class DataConversion(StatesGroup):
    # Здесь будут храниться состояния пользователя при конвертации валюты.
    first_currency = State()
    second_currency = State()
    amount_currency = State()

class DataWeather(StatesGroup):
    # Здесь будут храниться состояния пользователя при выборе города.
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
    btn3 = InlineKeyboardButton('Пришли мне фотографию котейки', 
                                callback_data='btn3')
    btn4 = InlineKeyboardButton('Мне нужно создать опрос', 
                                callback_data='btn4')
    markup = InlineKeyboardMarkup(row_width=1).add(btn1, btn2, btn3, btn4)
    await message.answer('Привет. Выбери интересующее тебя действие.', 
                        reply_markup=markup)


@dp.callback_query_handler(lambda callback: True)
async def process_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработка результата нажатия той или иной кнопки.
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


# Функционал получения прогноза погоды.
@dp.message_handler()
async def get_city(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, 
                           "Введите название города, в котором хотите узнать погоду: ")
    await state.set_state(DataWeather.city)

@dp.message_handler(state=DataWeather.city)
async def get_weather(message: types.Message, state: FSMContext):
    """Функия отвечающая за подключение к API и получение результата."""
    try:
         city_name = message.text
         await state.update_data(city=city_name)
         # Оправляем запрос к API Openweathermap
         request = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={API_KEY}&units=metric&lang=ru')
         response = request.json()
         # Получаем интересующие нас данные.
         date = datetime.datetime.now().strftime('%d.%m.%y ã. %H:%M')
         town = response['name']
         current_temp = response['main']['temp']
         humidity = response['main']['humidity']
         pressure = response['main']['pressure']
         wind_speed = response['wind']['speed']
         res = f"Текущая погода в {town}: {date} \n \U0001F3D9  Вы выбрали город {town} :\n  \U0001F321  Температура воздуха: {current_temp} °C,\n  \U0001F4A7 Влажность: {humidity} %,\n  \U0001F300  Давление: {pressure} мм.рт.ст, \n \U0001F32C  Скорость ветра {wind_speed} м/с"
         await bot.send_message(message.chat.id, res)
         await state.finish()
         
    # Отлавливаем исключание, если введен несуществующий город
    except:
        await bot.send_message(message.chat.id,'Проверьте правильность названия введеного города.')


# Функционал отвечающий за конвертацию.
@dp.message_handler()
async def check_currency_1(message: types.Message, state: FSMContext):
    """Указание курса валюты, из которого нужно конвертировать."""
    await bot.send_message(message.chat.id, 
                           "Укажите 3х символьный тикер валюты (на английском языке), ИЗ которого нужно конвертировать валюту: ")
    await state.set_state(DataConversion.first_currency)

@dp.message_handler(state=DataConversion.first_currency)
async def check_currency_2(message: types.Message, state: FSMContext):
    """Указание курса валюты, в которую нужно конвертировать."""
    # В first_cur сохраняем результат прошлого выбора валюты.
    first_cur = message.text
    await state.update_data(first_currency=first_cur)
    await bot.send_message(message.chat.id, 
                           "Укажите 3х символьный тикер валюты (на английском языке), В который нужно конвертировать валюту: ")
    await state.set_state(DataConversion.second_currency)

@dp.message_handler(state=DataConversion.second_currency)
async def check_amount(message: types.Message, state: FSMContext):
    """Указываем количество валюты к конвертации."""
    # В first_cur сохраняем результат второго выбора валюты.
    second_cur = message.text
    await state.update_data(second_currency=second_cur)
    await bot.send_message(message.chat.id, 
                                   "Укажите, сколько валюты Вы бы хотели конвертировать: ")
    await state.set_state(DataConversion.amount_currency)

async def get_connection(state: FSMContext):
    """Подключаемся к API и отправляем запрос."""
    try:
        data = await state.get_data()
        first_cur = data.get('first_currency')
        second_cur = data.get('second_currency')
        amount_cur = data.get('amount_currency')
        if first_cur and second_cur and amount_cur:
            link = f"https://api.apilayer.com/exchangerates_data/convert?to={second_cur}&from={first_cur}&amount={amount_cur}&api_key={exchange_key}"

            # Сохраняем заголовки, которые нужны для подключения к API
            header = {
                "apikey": exchange_key
            }
            resp = requests.get(link, headers=header)
            res = resp.json()
            return res
        else:
            print('Ошибка в аргументах!')
    except:
        print("Ошибка в подключении к API!")

@dp.message_handler(state=DataConversion.amount_currency)
async def get_result(message: types.Message, state: FSMContext):
    """Функция отвечает за вывод результата конвертации."""
    # В amount_cur сохраняем результат указания количества валюты.
    amount_cur = message.text
    await state.update_data(amount_currency=amount_cur)
    conn = await get_connection(state=state)
    date = datetime.datetime.now().strftime('%d.%m.%y ã. %H:%M')
    # Получаем интересующие результаты
    first_cur = conn['query']['from']
    second_cur = conn['query']['to']
    amount = conn['query']['amount']
    total = conn['result']
    # Âûâîäèì ðåçóëüòàò ðàáîòû
    msg = str(f"Текущая дата: {date} \U0001F4C5 \n Валюта, ИЗ которой Вы хотите конвертировать: {first_cur} \U0001F3E6 \n Валюта, в которой Вы бы хотели получить результат: {second_cur} \U0001F3E6 \n Количество валюты к конвертации: {amount} \U0001F51F \n Количество {second_cur} которое получается при конвертации {amount} {first_cur} в {second_cur} составляет {total} \U00002705")
    await bot.send_message(message.chat.id, msg)
    await state.finish()


# Функционал отвечающий за получение фото
async def get_photo():
    """Подключаемся к API."""
    try:
        link = f'https://api.thecatapi.com/v1/images/search?limit=1&api_key={animal_token}'
        request = requests.get(link)
        res = request.json()
        pict = res[0]['url']
    except:
        print("Ошибка подключения к API!")
    return pict

@dp.message_handler()
async def send_cat(message: types.Message):
    await bot.send_photo(chat_id=message.chat.id,
                         photo=await get_photo())


# Функционал отвечающий за создание опроса
@dp.message_handler()
async def create_poll(message: types.Message):
    # Варианты ответов
    options = ["Вариант 1", "Вариант 2", "Вариант 3"]
    # Создаем сам опрос с вариантами ответов
    poll = types.Poll(
    # question - тут нужно указать вопрос в опросе
    question = "Выберите понравившийся ответ",
    options = options,
    is_anonymous = True    
    )
    await bot.send_poll(chat_id=message.chat.id, 
                        question=poll.question, 
                        options=poll.options)


if __name__ == '__main__':
    executor.start_polling(dp)

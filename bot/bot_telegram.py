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

# ������ ���� � ������������ �����
bot = Bot(os.getenv('TOKEN'))
# ���� � API Openweather
API_KEY = os.getenv('WEATHER_API')
# ���� � Exchange Rates Data API
exchange_key = os.getenv('EXCHANGE')
# ���� � The Cat API - Cats as a Service.
animal_token = os.getenv('ANIMALS')

# ��������� ��� ��������� ���������, �������� � ��.
dp = Dispatcher(bot, storage=MemoryStorage())


class DataConversion(StatesGroup):
    # ����� ����� ��������� ��������� ������������ � ������� ������ ��� �����������
    first_currency = State()
    second_currency = State()
    amount_currency = State()

class DataWeather(StatesGroup):
    # ����� ����� ��������� ��������� ������������ � ������� ������ ��� ������ ������
    # ��� ����������� �������� � ������� ��������� ������
    city = State()


@dp.message_handler(commands=['start'])
async def start_bot(message: types.Message):
    """
    ��������� ���������� � ������ ����.

    ������� ������, ����� �� ������� ��� ������ � ��� ����������� � ���������� �� ����� ���� �� 
    �������� � ���� ������.
    btn1: ����� ������� �� ��� ����� ������� ������ � ������������ ������.
    btn2: ����� ������� �� ��� ���� ����������� �������������� ������.
    btn3: ����� ������� �� ��� ������ ��������� � ��� ������� ���������
    btn4: ������� ����� � ���������� ������ � �������� � ������������ ���.
    markup: ������� ������ �� ����� ����.
    """
    btn1 = InlineKeyboardButton('������ ��� ������ � ...', 
                                callback_data='btn1')
    btn2 = InlineKeyboardButton('��� ����� �������������� ������', 
                                callback_data='btn2')
    btn3 = InlineKeyboardButton('������ ��� �������� ���������', 
                                callback_data='btn3')
    btn4 = InlineKeyboardButton('� ���� ������� �����', 
                                callback_data='btn4')
    markup = InlineKeyboardMarkup(row_width=1).add(btn1, btn2, btn3, btn4)
    await message.answer('������! ������ ���� �� ������������ ���� ��������.', 
                        reply_markup=markup)


@dp.callback_query_handler(lambda callback: True)
async def process_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    ������� ��������� ����������� ������ ��� ��� ���� ������.
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


# ����������, ���������� �� ������� ������.
@dp.message_handler()
async def get_city(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, 
                           "������� �������� ������, � ������� ������ ������ ������: ")
    await state.set_state(DataWeather.city)

@dp.message_handler(state=DataWeather.city)
async def get_weather(message: types.Message, state: FSMContext):
    """������� �������� �� ��������� �������� ������ � ������������ ������."""
    try:
         city_name = message.text
         await state.update_data(city=city_name)
         # ������ � API Openweathermap
         request = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={API_KEY}&units=metric&lang=ru')
         response = request.json()
         # ������������ ��������� � ������
         date = datetime.datetime.now().strftime('%d.%m.%y �. %H:%M')
         town = response['name']
         current_temp = response['main']['temp']
         humidity = response['main']['humidity']
         pressure = response['main']['pressure']
         wind_speed = response['wind']['speed']
         res = f"������� ���� � ������ {town}: {date} \n \U0001F3D9  ������� ������ � ������ {town} :\n  \U0001F321  �����������: {current_temp} �C,\n  \U0001F4A7 ���������: {humidity} %,\n  \U0001F300  ��������: {pressure} ��.��.��, \n \U0001F32C  �������� ����� {wind_speed} �/�"
         await bot.send_message(message.chat.id, res)
         await state.finish()
         
    # ��������� ���������� � ������ ������������� ����� ������
    except:
        await bot.send_message(message.chat.id,'������ � �������� ������, ���� ������ ������ �� ����������.')


# ����� ����������, ���������� �� ����������� ������.
@dp.message_handler()
async def check_currency_1(message: types.Message, state: FSMContext):
    """������� ��� ����� ������ ������� ����� ��������������."""
    await bot.send_message(message.chat.id, 
                           "������� �� ���������� ����� ������������� ����� ������, �� ������� ������ ��������������: ")
    await state.set_state(DataConversion.first_currency)

@dp.message_handler(state=DataConversion.first_currency)
async def check_currency_2(message: types.Message, state: FSMContext):
    """������� ��� ����� ������ � ������� ����� ��������������."""
    # ��������� ��������� �� �������� ��������, ��� ������� ������ �� ������� ������������.
    first_cur = message.text
    await state.update_data(first_currency=first_cur)
    await bot.send_message(message.chat.id, 
                           "������� �� ���������� ����� ������������� ����� ������, � ������� ������ ��������������: ")
    await state.set_state(DataConversion.second_currency)

@dp.message_handler(state=DataConversion.second_currency)
async def check_amount(message: types.Message, state: FSMContext):
    """������� ��� ����� ���������� ������ ������� ����� ��������������."""
    # ��������� ��������� �� �������� ��������, ��� ������� ������ � ������� ������������.
    second_cur = message.text
    await state.update_data(second_currency=second_cur)
    await bot.send_message(message.chat.id, 
                                   "������� ����������� ���������� ������: ")
    await state.set_state(DataConversion.amount_currency)

async def get_connection(state: FSMContext):
    """������� ��� ��������� ����������."""
    try:
        data = await state.get_data()
        first_cur = data.get('first_currency')
        second_cur = data.get('second_currency')
        amount_cur = data.get('amount_currency')
        if first_cur and second_cur and amount_cur:
            link = f"https://api.apilayer.com/exchangerates_data/convert?to={second_cur}&from={first_cur}&amount={amount_cur}&api_key={exchange_key}"

            # ������������ � ������� ���������, � ������ ������ - ���� API
            header = {
                "apikey": exchange_key
            }
            resp = requests.get(link, headers=header)
            res = resp.json()
            return res
        else:
            print('������ � ����������!')
    except:
        print("������ � ������� � API!")

@dp.message_handler(state=DataConversion.amount_currency)
async def get_result(message: types.Message, state: FSMContext):
    """����� ��������� ���������� ������ ��� ���������� � �������������� ������."""
    # ��������� ��������� �� �������� ��������, ��� ������� ���������� ������.
    amount_cur = message.text
    await state.update_data(amount_currency=amount_cur)
    conn = await get_connection(state=state)
    date = datetime.datetime.now().strftime('%d.%m.%y �. %H:%M')
    # ��� � ���������� ��������� ���������� �� ������� � get_connection ������
    first_cur = conn['query']['from']
    second_cur = conn['query']['to']
    amount = conn['query']['amount']
    total = conn['result']
    # ������� ��������� ������
    msg = str(f"������� ���� � �����: {date} \U0001F4C5 \n ������, �� ������� ����� ��������������: {first_cur} \U0001F3E6 \n ������, � ������� ����� ��������������: {second_cur} \U0001F3E6 \n ���������� �������� ������ � �����������: {amount} \U0001F51F \n ���������� {second_cur} ��� ����������� {amount} {first_cur} � {second_cur} �� �������� ����� ���������� {total} \U00002705")
    await bot.send_message(message.chat.id, msg)
    await state.finish()


# ����� ����������, ���������� �� ��������� ��������.
async def get_photo():
    """��������� ������ �� �������� � ���������."""
    try:
        link = f'https://api.thecatapi.com/v1/images/search?limit=1&api_key={animal_token}'
        request = requests.get(link)
        res = request.json()
        pict = res[0]['url']
    except:
        print("������ � ������� � API!")
    return pict

@dp.message_handler()
async def send_cat(message: types.Message):
    await bot.send_photo(chat_id=message.chat.id,
                         photo=await get_photo())


# ����������, ���������� �� �������� ������ � �������� ��� � ��������� ���
@dp.message_handler()
async def create_poll(message: types.Message):
    # ����� ����� ���������� ������ ��������� �������
    options = ["������� 1", "������� 2", "������� 3"]
    # ����� ������� ������ ������
    poll = types.Poll(
    question = "������ ������������� ������� ������",
    options = options,
    is_anonymous = True    
    )
    await bot.send_poll(chat_id=message.chat.id, 
                        question=poll.question, 
                        options=poll.options)


if __name__ == '__main__':
    executor.start_polling(dp)

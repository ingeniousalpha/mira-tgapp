import asyncio
import logging
import os
import pickle
import sys
from base64 import b64decode
from decimal import Decimal
from typing import Union

from aiogram import Dispatcher, Bot, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, ReplyKeyboardRemove
)
from geopy.geocoders import Nominatim
from sqlalchemy import create_engine, sql, Connection
from sqlalchemy.orm import Session

TOKEN = os.getenv("BOT_TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_engine(application_name: str):
    return create_engine("postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}".format(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        pool_recycle=60 * 30,
    ), connect_args={"application_name": application_name})


engine = get_engine(__name__)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class StepForm(StatesGroup):
    initial_language_setting = State()
    initial_name_setting = State()
    initial_phone_number_setting = State()
    initial_address_setting = State()


def get_constance_value(connection: Union[Connection, Session], key: str, default=None):
    b64_value = connection.execute(
        sql.text('select value from constance_config where key = :key'), {'key': key}
    ).scalar()
    if b64_value is None:
        return default
    value = pickle.loads(b64decode(b64_value))
    return value


def build_language_buttons(session, with_back_button=False, language_code='ru'):
    button_list = [
        [
            types.KeyboardButton(text=get_constance_value(session, 'SET_LANGUAGE_BUTTON_TEXT_RU')),
            types.KeyboardButton(text=get_constance_value(session, 'SET_LANGUAGE_BUTTON_TEXT_UZ'))
        ]
    ]
    if with_back_button:
        button_list.append(
            [types.KeyboardButton(text=get_constance_value(session, f'BACK_BUTTON_TEXT_{language_code.upper()}'))]
        )
    return types.ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True, one_time_keyboard=True)


@dp.message(CommandStart())
async def command_start(message: Message, state: FSMContext):
    if message.from_user.is_bot:
        return None
    await state.clear()
    with Session(engine) as session:
        session.execute(sql.text(f"""
            INSERT INTO customers_customer (telegram_user_id, name, language, created_at)
            VALUES ({message.from_user.id}, NULL, 'ru', NOW()) ON CONFLICT (telegram_user_id) DO NOTHING;
        """))
        session.commit()
        # languages = [
        #     [
        #         types.KeyboardButton(text=get_constance_value(session, 'SET_LANGUAGE_BUTTON_TEXT_RU')),
        #         types.KeyboardButton(text=get_constance_value(session, 'SET_LANGUAGE_BUTTON_TEXT_UZ'))
        #     ]
        # ]
        # await message.answer(
        #     text=get_constance_value(session, 'SET_LANGUAGE_TEXT'),
        #     reply_markup=types.ReplyKeyboardMarkup(keyboard=languages, resize_keyboard=True, one_time_keyboard=True)
        # )
        await state.set_state(StepForm.initial_language_setting)


@dp.message(StepForm.initial_language_setting)
async def set_initial_language(message: types.Message, state: FSMContext):
    with (Session(engine) as session):

        languages = [
            [
                types.KeyboardButton(text=get_constance_value(session, 'SET_LANGUAGE_BUTTON_TEXT_RU')),
                types.KeyboardButton(text=get_constance_value(session, 'SET_LANGUAGE_BUTTON_TEXT_UZ'))
            ]
        ]
        await message.answer(
            text=get_constance_value(session, 'SET_LANGUAGE_TEXT'),
            reply_markup=types.ReplyKeyboardMarkup(keyboard=languages, resize_keyboard=True, one_time_keyboard=True)
        )

        if message.text == get_constance_value(session, 'SET_LANGUAGE_BUTTON_TEXT_RU'):
            language_code = 'ru'
        elif message.text == get_constance_value(session, 'SET_LANGUAGE_BUTTON_TEXT_UZ'):
            language_code = 'uz'
        else:
            return
        session.execute(sql.text(f"""
            UPDATE customers_customer
            SET language = '{language_code}'
            WHERE telegram_user_id = {message.from_user.id}
        """))
        session.commit()
        customer = session.execute(sql.text(f"""
            SELECT id, name, phone_number
            FROM customers_customer
            WHERE telegram_user_id = {message.from_user.id}
        """)).fetchone()
        addresses = session.execute(sql.text(f"""
            SELECT *
            FROM customers_address
            WHERE customer_id = {customer[0]}
        """)).fetchall()
        if not customer[1]:
            await message.answer(text=get_constance_value(session, f'SET_NAME_TEXT_{language_code.upper()}'))
            await state.set_state(StepForm.initial_name_setting)
        elif not customer[2]:
            buttons = [
                [types.KeyboardButton(
                    text=get_constance_value(session, f'SET_PHONE_NUMBER_BUTTON_TEXT_{language_code.upper()}'),
                    request_contact=True
                )]
            ]
            await message.answer(
                text=get_constance_value(session, f'SET_PHONE_NUMBER_TEXT_{language_code.upper()}'),
                reply_markup=types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
            )
            await state.set_state(StepForm.initial_phone_number_setting)
        elif not addresses:
            buttons = [
                [types.KeyboardButton(
                    text=get_constance_value(session, f'SET_PHONE_NUMBER_BUTTON_TEXT_{language_code.upper()}'),
                    request_contact=True
                )]
            ]
            await message.answer(
                text=get_constance_value(session, f'SET_PHONE_NUMBER_TEXT_{language_code.upper()}'),
                reply_markup=types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
            )
            await state.set_state(StepForm.initial_phone_number_setting)


@dp.message(StepForm.initial_name_setting)
async def set_initial_name(message: types.Message, state: FSMContext):
    with (Session(engine) as session):
        name = message.text.strip()
        if not name:
            return
        session.execute(sql.text(f"""
            UPDATE customers_customer
            SET name = '{name}'
            WHERE telegram_user_id = {message.from_user.id}
        """))
        session.commit()
        customer = session.execute(sql.text(f"""
            SELECT phone_number, language
            FROM customers_customer
            WHERE telegram_user_id = {message.from_user.id}
        """)).fetchone()
        if not customer[0]:
            buttons = [
                [types.KeyboardButton(
                    text=get_constance_value(session, f'SET_PHONE_NUMBER_BUTTON_TEXT_{customer[1].upper()}'),
                    request_contact=True
                )]
            ]
            await message.answer(
                text=get_constance_value(session, f'SET_PHONE_NUMBER_TEXT_{customer[1].upper()}'),
                reply_markup=types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
            )
            await state.set_state(StepForm.initial_phone_number_setting)


@dp.message(StepForm.initial_phone_number_setting)
async def set_initial_phone_number(message: types.Message, state: FSMContext):
    with (Session(engine) as session):
        print(message.contact)
        if message.contact:
            session.execute(sql.text(f"""
                UPDATE customers_customer
                SET phone_number = '{message.contact.phone_number}'
                WHERE telegram_user_id = {message.from_user.id}
            """))
            session.commit()
            await message.answer('Номер сохранен!', reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer('Нажмите на кнопку "Поделиться"!')


@dp.message(F.location)
async def get_location(message: Message):
    latitude = Decimal(message.location.latitude)
    longitude = Decimal(message.location.longitude)
    with (Session(engine) as session):
        address = session.execute(sql.text(f"""
            SELECT cc.id, ca.id
            FROM customers_address ca
            JOIN customers_customer cc ON ca.customer_id = cc.id
            WHERE cc.telegram_user_id = {message.from_user.id} AND latitude = {latitude} AND latitude = {longitude}
        """)).fetchone()
        if address:
            session.execute(sql.text(f"""
                UPDATE customers_address
                SET is_current = false
                WHERE customer_id = {address[0]}
            """))
            session.execute(sql.text(f"""
                UPDATE customers_address
                SET is_current = true
                WHERE customer_id = {address[0]}
            """))
            session.commit()


    geolocator = Nominatim(user_agent="menu_bot")
    location = geolocator.reverse(f'{latitude}, {longitude}')
    location_items = location.address
    print(location_items)
    location_items = location.address.split(',')
    print(location_items)
    location_items.reverse()
    print(location_items)
    location_items = location_items[2:]
    print(location_items)
    item_count = len(location_items)
    address = ''
    for index, item in enumerate(location_items):
        address = address + item.strip()
        if item_count > index + 1:
            address = address + ', '
    print(address)
    await message.answer('Спасибо!', reply_markup=ReplyKeyboardRemove())


async def main():
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

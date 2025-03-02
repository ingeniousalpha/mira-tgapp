import enum
import os
import pickle
from base64 import b64decode
from decimal import Decimal
from typing import Union

import numpy
from aiogram import Dispatcher, Bot, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from geopy import Nominatim
from matplotlib.path import Path
from sqlalchemy import create_engine, sql, Connection
from sqlalchemy.orm import Session

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = 'https://miraapa.uz/webhook'  # Замените на ваш домен
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_engine(application_name: str):
    return create_engine(
        "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}".format(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
        ),
        connect_args={"application_name": application_name},
        pool_size=30,
        pool_recycle=60 * 30,
        max_overflow=0,
    )

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
engine = get_engine(__name__)
storage = RedisStorage.from_url(f'redis://{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/0')
dp = Dispatcher(storage=storage)



def get_constance_value(connection: Union[Connection, Session], key: str, default=None):
    b64_value = connection.execute(
        sql.text('select value from constance_config where key = :key'), {'key': key}
    ).scalar()
    if b64_value is None:
        return default
    value = pickle.loads(b64decode(b64_value))
    return value


class StepForm(StatesGroup):
    set_initial_language = State()
    set_language = State()
    set_phone = State()
    main_section = State()
    menu_section = State()
    address_section = State()
    settings_section = State()


class KeyboardType(enum.Enum):
    LANGUAGES = 1
    PHONE = 2
    MAIN = 3
    MENU = 4
    ADDRESSES = 5
    SETTINGS = 6


def build_keyboard(session, telegram_user_id, keyboard_type,  language):
    if language:
        language = language.upper()
    customer = session.execute(sql.text(f"""
        SELECT id
        FROM customers_customer
        WHERE telegram_user_id = {telegram_user_id}
    """)).fetchone()
    request_contact = False
    if keyboard_type == KeyboardType.ADDRESSES:
        keyboard = [
            [types.KeyboardButton(
                text=get_constance_value(session, f'SET_ADDRESS_BUTTON_{language}'),
                request_location=True
            )]
        ]
        addresses = session.execute(sql.text(f"""
            SELECT ca.value
            FROM customers_address ca
            JOIN customers_customer cc ON ca.customer_id = cc.id
            WHERE cc.telegram_user_id = {telegram_user_id}
            ORDER BY ca.created_at DESC
        """)).fetchall()
        for address in addresses:
            keyboard.append([types.KeyboardButton(text=address[0])])
        keyboard.append([types.KeyboardButton(text=get_constance_value(session, f'GET_BACK_BUTTON_{language}'))])
        return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    elif keyboard_type == KeyboardType.SETTINGS:
        button_text_list = [
            get_constance_value(session, f'EDIT_LANGUAGE_BUTTON_{language}'),
            get_constance_value(session, f'EDIT_PHONE_BUTTON_{language}'),
            get_constance_value(session, f'GET_BACK_BUTTON_{language}'),
        ]
    elif keyboard_type == KeyboardType.LANGUAGES:
        button_text_list = [
            get_constance_value(session, f'LANGUAGE_BUTTON_RU'),
            get_constance_value(session, f'LANGUAGE_BUTTON_UZ'),
        ]
    elif keyboard_type == KeyboardType.PHONE:
        button_text_list = [
            get_constance_value(session, f'SET_PHONE_{language}'),
        ]
        request_contact = True
    elif keyboard_type == KeyboardType.MENU:
        params= f"?customer_id={customer[0]}&language={language.lower()}"
        full_url = str(get_constance_value(session, f'WEB_APP_URL')) + params
        print(full_url)
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=get_constance_value(session, f'WEB_APP_BUTTON_{language}'),
                        web_app=types.WebAppInfo(url=full_url)
                    )
                ]
            ]
        )
    else:
        button_text_list = [
            get_constance_value(session, f'MENU_BUTTON_{language}'),
            get_constance_value(session, f'SETTINGS_BUTTON_{language}'),
        ]
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=text, request_contact=request_contact)] for text in button_text_list],
        resize_keyboard=True
    )


def get_customer_language(session, telegram_user_id):
    # For existing customers only
    customer = session.execute(sql.text(f"""
        SELECT language
        FROM customers_customer
        WHERE telegram_user_id = {telegram_user_id}
    """)).fetchone()
    return customer[0].upper() if customer[0] else customer[0]


@dp.message(CommandStart())
async def command_start(message: types.Message, state: FSMContext):
    if message.from_user.is_bot:
        return None
    await state.clear()
    with Session(engine) as session:
        created = False
        customer = session.execute(sql.text(f"""
            SELECT language, phone_number
            FROM customers_customer
            WHERE telegram_user_id = {message.from_user.id}
        """)).fetchone()
        if not customer:
            created = True
            session.execute(sql.text(f"""
                INSERT INTO customers_customer (telegram_user_id, chat_id, phone_number, language, created_at)
                VALUES ({message.from_user.id}, {message.chat.id}, NULL, NULL, NOW()) ON CONFLICT (telegram_user_id) DO NOTHING
            """))
            session.commit()
        if created or not customer[0]:
            language = None
            message_text = get_constance_value(session, f'LANGUAGES_MESSAGE')
            keyboard_type = KeyboardType.LANGUAGES
            next_step = StepForm.set_initial_language
        elif created or not customer[1]:
            language = get_customer_language(session, message.from_user.id)
            message_text = get_constance_value(session, f'PHONE_MESSAGE_{language}')
            keyboard_type = KeyboardType.PHONE
            next_step = StepForm.set_phone
        else:
            language = get_customer_language(session, message.from_user.id)
            message_text = get_constance_value(session, f'MAIN_MESSAGE_{language}')
            keyboard_type = KeyboardType.MAIN
            next_step = StepForm.main_section
        await message.answer(
            text=message_text, reply_markup=build_keyboard(session, message.from_user.id, keyboard_type, language)
        )
        await state.set_state(next_step)


@dp.message(StepForm.set_initial_language)
async def process_set_initial_language(message: types.Message, state: FSMContext):
    with (Session(engine) as session):
        if message.text == get_constance_value(session, 'LANGUAGE_BUTTON_RU'):
            language = 'ru'
        elif message.text == get_constance_value(session, 'LANGUAGE_BUTTON_UZ'):
            language = 'uz'
        else:
            return
        session.execute(sql.text(f"""
            UPDATE customers_customer
            SET language = '{language}'
            WHERE telegram_user_id = {message.from_user.id}
        """))
        session.commit()
        await message.answer(
            text=get_constance_value(session, f'PHONE_MESSAGE_{language.upper()}'),
            reply_markup=build_keyboard(session, message.from_user.id, KeyboardType.PHONE, language)
        )
        await state.set_state(StepForm.set_phone)


@dp.message(StepForm.set_language)
async def process_set_language(message: types.Message, state: FSMContext):
    with (Session(engine) as session):
        if message.text == get_constance_value(session, 'LANGUAGE_BUTTON_RU'):
            language = 'ru'
        elif message.text == get_constance_value(session, 'LANGUAGE_BUTTON_UZ'):
            language = 'uz'
        else:
            return
        session.execute(sql.text(f"""
            UPDATE customers_customer
            SET language = '{language}'
            WHERE telegram_user_id = {message.from_user.id}
        """))
        session.commit()
        await message.answer(
            text=get_constance_value(session, f'MAIN_MESSAGE_{language.upper()}'),
            reply_markup=build_keyboard(session, message.from_user.id, KeyboardType.MAIN, language)
        )
        await state.set_state(StepForm.main_section)


@dp.message(StepForm.set_phone)
async def process_set_phone(message: types.Message, state: FSMContext):
    with (Session(engine) as session):
        language = get_customer_language(session, message.from_user.id)
        if message.text == get_constance_value(session, f'GET_BACK_BUTTON_{language}'):
            await message.answer(
                text=get_constance_value(session, f'SETTINGS_MESSAGE_{language}'),
                reply_markup=build_keyboard(session, message.from_user.id, KeyboardType.SETTINGS, language)
            )
            await state.set_state(StepForm.settings_section)
        elif message.contact:
            if message.from_user.id != message.contact.user_id:
                return
            session.execute(sql.text(f"""
                UPDATE customers_customer
                SET phone_number = '{message.contact.phone_number}'
                WHERE telegram_user_id = {message.from_user.id}
            """))
            session.commit()
            await message.answer(
                text=get_constance_value(session, f'MAIN_MESSAGE_{language}'),
                reply_markup=build_keyboard(session, message.from_user.id, KeyboardType.MAIN, language)
            )
            await state.set_state(StepForm.main_section)
        else:
            await message.answer(text=get_constance_value(session, f'PHONE_MESSAGE_{language}'))


@dp.message(StepForm.main_section)
async def process_main_section(message: types.Message, state: FSMContext):
    with (Session(engine) as session):
        language = get_customer_language(session, message.from_user.id)
        if message.text == get_constance_value(session, f'MENU_BUTTON_{language}'):
            message_text = get_constance_value(session, f'ADDRESS_MESSAGE_{language}')
            keyboard_type = KeyboardType.ADDRESSES
            next_step = StepForm.address_section
        elif message.text == get_constance_value(session, f'SETTINGS_BUTTON_{language}'):
            message_text = get_constance_value(session, f'SETTINGS_MESSAGE_{language}')
            keyboard_type = KeyboardType.SETTINGS
            next_step = StepForm.settings_section
        else:
            return
        await message.answer(
            text=message_text, reply_markup=build_keyboard(session, message.from_user.id, keyboard_type, language)
        )
        await state.set_state(next_step)


def check_point(vertices, point):
    return Path(numpy.array(vertices)).contains_point(point)


@dp.message(StepForm.address_section)
async def process_address_section(message: types.Message, state: FSMContext):
    with (Session(engine) as session):
        language = get_customer_language(session, message.from_user.id)
        customer = session.execute(sql.text(f"""
            SELECT id
            FROM customers_customer
            WHERE telegram_user_id = {message.from_user.id}
        """)).fetchone()
        if message.location:
            latitude = Decimal(message.location.latitude).quantize(Decimal('0.00000001'))
            longitude = Decimal(message.location.longitude).quantize(Decimal('0.00000001'))
            is_in_delivery_zone = False
            delivery_zones = session.execute(sql.text(f"""
                SELECT zone_json
                FROM customers_deliveryzone
                WHERE is_active = true
            """)).fetchall()
            for zone in delivery_zones:
                if zone[0]:
                    vertices = zone[0]["features"][0]["geometry"]["coordinates"][0]
                    if check_point(vertices, [longitude, latitude]):
                        is_in_delivery_zone = True
                        break

            if not is_in_delivery_zone:
                await message.answer(text=get_constance_value(session, f'NOT_IN_DELIVERY_ZONE_{language}'))
                return

            geolocator = Nominatim(user_agent="menu_bot")
            location = geolocator.reverse(f'{latitude}, {longitude}')
            location_items = location.address.split(',')
            location_items.reverse()
            location_items = location_items[2:]
            item_count = len(location_items)
            address_str = ''
            for index, item in enumerate(location_items):
                address_str = address_str + item.strip()
                if item_count > index + 1:
                    address_str = address_str + ', '
            address = session.execute(sql.text(f"""
                SELECT id
                FROM customers_address
                WHERE customer_id = {customer[0]} AND value = '{address_str}'
            """)).fetchone()
            session.execute(sql.text(f"""
                UPDATE customers_address
                SET is_current = false
                WHERE customer_id = {customer[0]}
            """))
            session.commit()
            if address:
                session.execute(sql.text(f"""
                    UPDATE customers_address
                    SET is_current = true
                    WHERE id = {address[0]}
                """))
                session.commit()
            else:
                session.execute(sql.text(f"""
                    INSERT INTO customers_address (customer_id, latitude, longitude, value, is_current, created_at)
                    VALUES ({customer[0]}, {latitude}, {longitude}, '{address_str}', true, NOW())
                """))
                session.commit()
            message_text = get_constance_value(session, f'MENU_MESSAGE_{language}')
            keyboard_type = KeyboardType.MENU
            next_step = StepForm.main_section
        elif message.text == get_constance_value(session, f'GET_BACK_BUTTON_{language}'):
            message_text = get_constance_value(session, f'MAIN_MESSAGE_{language}')
            keyboard_type = KeyboardType.MAIN
            next_step = StepForm.main_section
        else:
            addresses = session.execute(sql.text(f"""
                SELECT ca.id, ca.value
                FROM customers_address ca
                JOIN customers_customer cc ON ca.customer_id = cc.id
                WHERE cc.telegram_user_id = {message.from_user.id}
                ORDER BY ca.created_at DESC
            """)).fetchall()
            if addresses:
                session.execute(sql.text(f"""
                    UPDATE customers_address
                    SET is_current = false
                    WHERE customer_id = {customer[0]}
                """))
                session.commit()
            for address in addresses:
                if message.text == address[1]:
                    session.execute(sql.text(f"""
                        UPDATE customers_address
                        SET is_current = true
                        WHERE id = {address[0]}
                    """))
                    session.commit()
                    break
            message_text = get_constance_value(session, f'MENU_MESSAGE_{language}')
            keyboard_type = KeyboardType.MENU
            next_step = StepForm.main_section
        await message.answer(
            text=message_text,
            reply_markup=build_keyboard(session, message.from_user.id, keyboard_type, language)
        )
        if keyboard_type == KeyboardType.MENU:
            await message.answer(
                text=get_constance_value(session, f'USE_MENU_BUTTON_{language}'),
                reply_markup=build_keyboard(session, message.from_user.id, KeyboardType.MAIN, language)
            )
        if next_step:
            await state.set_state(next_step)

@dp.message(StepForm.settings_section)
async def process_settings_section(message: types.Message, state: FSMContext):
    with (Session(engine) as session):
        language = get_customer_language(session, message.from_user.id)
        if message.text == get_constance_value(session, f'EDIT_LANGUAGE_BUTTON_{language}'):
            message_text = get_constance_value(session, f'LANGUAGES_MESSAGE_{language}')
            keyboard_type = KeyboardType.LANGUAGES
            next_step = StepForm.set_language
        elif message.text == get_constance_value(session, f'EDIT_PHONE_BUTTON_{language}'):
            message_text = get_constance_value(session, f'PHONE_MESSAGE_{language}')
            keyboard_type = KeyboardType.PHONE
            next_step = StepForm.set_phone
        elif message.text == get_constance_value(session, f'GET_BACK_BUTTON_{language}'):
            message_text = get_constance_value(session, f'MAIN_MESSAGE_{language}')
            keyboard_type = KeyboardType.MAIN
            next_step = StepForm.main_section
        else:
            return
        await message.answer(
            text=message_text, reply_markup=build_keyboard(session, message.from_user.id, keyboard_type, language)
        )
        await state.set_state(next_step)


# Функция для настройки вебхука при запуске
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)

# Создание aiohttp приложения
app = web.Application()

# Регистрация обработчика вебхука
webhook_requests_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
)
webhook_requests_handler.register(app, path=WEBHOOK_PATH)

# Настройка приложения
setup_application(app, dp, bot=bot)

# Запуск приложения
if __name__ == '__main__':
    # Указываем порт, на котором будет работать бот (HTTP)
    web.run_app(app, host='0.0.0.0', port=8081)

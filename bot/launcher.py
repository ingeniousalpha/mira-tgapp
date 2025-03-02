import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = 'https://miraapa.uz/webhook'  # Замените на ваш домен

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я бот на вебхуках.")

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
    web.run_app(app, host='0.0.0.0', port=8080)

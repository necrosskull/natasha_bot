import os
from dotenv import load_dotenv

command_list = [
    ('start', '✅ Старт'),
    ('roll', '🎲 Рулетка'),
    ('leaderboard', '🏆 Топ рулетки'),
    ('cock', '🍆 Увеличить хуй'),
    ('mycock', '📏 Узнать длину'),
    ('cocktop', '🏆 Топ писек'),
    ('cockantitop', '🏆 Анти топ писек'),
    ('cockreset', '⚡ Сбросить таймер хуя')
]

delete_timer = 30
sleep_secs = 1
cock_price = 40
default_lives = 3

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BANNED = [int(i) for i in os.getenv("BANNED").split(",")] if os.getenv("BANNED") else None
AUTHORIZED_USERS = os.getenv("AUTHORIZED_USERS").split(',')
TZ = os.getenv("TZ")

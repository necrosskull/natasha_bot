import os
from dotenv import load_dotenv

command_list = [
    ('start', '✅ Старт'),
    ('roll', '🎲 Рулетка'),
    ('leaderboard', '🏆 Топ рулетки'),
    ('cock', '🍆 Увеличить хуй'),
    ('mycock', '📏 Узнать длину'),
    ('score', '💰 Узнать счёт'),
    ('cocktop', '🏆 Топ писек'),
    ('cockantitop', '🏆 Анти топ писек'),
    ('cockreset', '⚡ Сбросить таймер хуя')
]

delete_timer = 30
sleep_secs = 1
cock_price = 50
default_lives = 5
roulette_cooldown = 8
roulette_win_score = 15

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BANNED = [int(i) for i in os.getenv("BANNED").split(",")] if os.getenv("BANNED") else None
AUTHORIZED_USERS = os.getenv("AUTHORIZED_USERS").split(',')
TZ = os.getenv("TZ")

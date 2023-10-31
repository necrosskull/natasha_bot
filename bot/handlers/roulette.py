import datetime
import random
import re

from telegram import constants
from telegram.ext import CommandHandler, filters, MessageHandler

import bot.config as config
import bot.db.fetch as fetch
from bot.handlers.handler import send_and_delete_message

from bot.db.sqlite import TgBotGame, db

roulette = re.compile(r'^/ro', re.IGNORECASE)


async def handle_roulette_command(update, context):
    """
    Обрабатывает команду '/roulette' для игры в рулетку.

    Эта функция проверяет, имеет ли пользователь право на игру, и получает данные пользователя (жизни и счёт) из базы
    данных. Если у пользователя закончились жизни, проверяется период охлаждения. Если охлаждение все еще активно,
    отправляется сообщение пользователю с указанием оставшегося времени. В противном случае пользователю разрешается
    начать игру.

    Функция ожидает аргумент с числом, представляющим выбор пользователя (от 1 до 6). Если число совпадает с одним из
    двух случайно сгенерированных чисел, пользователь выигрывает и ему начисляются 10 очков. Если число не совпадает,
    пользователь теряет жизнь. Если все жизни использованы, пользователь получает период охлаждения и может
    разблокироваться, потратив 10 очков.

    Аргументы:
        update (telegram.Update): Входящее обновление от Telegram.
        context (telegram.ext.CallbackContext): Контекст для текущего обновления.

    Возвращает:
        None
    """

    if str(update.message.chat.id) not in config.AUTHORIZED_USERS:
        return

    user_id = update.message.from_user.id
    user_message_id = update.message.message_id
    username = update.message.from_user.username if update.message.from_user.username \
        else update.message.from_user.first_name
    thread_id = update.message.message_thread_id if update.message.is_topic_message else None

    roulette_args = context.args
    number = int(roulette_args[0]) if roulette_args and roulette_args[0].isdigit() else random.randint(1, 6)

    cooldown, time_diff = check_cooldown(user_id)

    if cooldown:
        remain = datetime.timedelta(hours=config.roulette_cooldown) - time_diff

        hours = remain.seconds // 3600
        minutes = (remain.seconds % 3600) // 60
        seconds = remain.seconds % 60

        time_left = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        message_text = f'☠️ Полегче, ты своё отстрелял, пойди пока потрогай траву!\n' \
                       f'🕐 Осталось {time_left}\n'
        await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id,
                                      message_text,
                                      parse_mode=constants.ParseMode.MARKDOWN, reply=True)
        return

    data = fetch.get_values_by_id(user_id, 'lives', 'score')

    if data:
        lives, score = data
    else:
        lives, score = None, None

    if number > 6 or number < 1:
        message_text = 'Неверное число, введите число от 1 до 6'
        await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id,
                                      message_text,
                                      parse_mode=constants.ParseMode.MARKDOWN)
        return

    result = random.sample(range(1, 7), 3)

    if number in result:
        new_score = score + config.roulette_win_score if score is not None else config.roulette_win_score

        if lives is not None:

            db.connect()
            table = TgBotGame.get_by_id(user_id)
            table.score = new_score
            table.username = username
            table.save()
            db.close()

        else:

            db.connect()
            TgBotGame.create(
                id=user_id,
                score=new_score,
                username=username
            )
            db.close()

        message_text = f'Браво, вы выиграли!\n✅ Вам начислено *{config.roulette_win_score}* баллов'

    else:
        if lives is not None:

            new_lives = lives - 1

            db.connect()
            table = TgBotGame.get_by_id(user_id)
            table.lives = new_lives
            table.username = username
            table.save()
            db.close()

            lives = new_lives

        else:
            lives = config.default_lives - 1

            db.connect()
            table = TgBotGame.create(
                id=user_id,
                lives=lives,
                username=username
            )
            table.save()
            db.close()

        if lives == 0 or lives < 0:
            timestamp = datetime.datetime.now()

            db.connect()
            table = TgBotGame.get_by_id(user_id)
            table.cooldown = timestamp
            table.username = username
            table.lives = 0
            table.save()
            db.close()

            message_text = (f"💥 БАМ ТЫ СДОХ\n🚫 Все жизни потрачены, возвращайся через "
                            f"{config.roulette_cooldown} часов!\n")

        else:
            message_text = f"💥 БАМ ТЫ СДОХ\nОсталось жизней: {lives}"

    await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id, message_text,
                                  parse_mode=constants.ParseMode.MARKDOWN, reply=True)


def check_cooldown(user_id):
    """
    Проверяет, есть ли у пользователя активный период охлаждения.

    Эта функция получает временную метку охлаждения для указанного пользователя из базы данных. Если период
    охлаждения обнаружен и разница времени между текущим временем и временной меткой охлаждения меньше одной минуты,
    указывающая, что охлаждение все еще активно, она возвращает True вместе с разницей времени. В противном случае
    она возвращает False и устанавливает период охлаждения на None, тем самым удаляя охлаждение для пользователя.

    Аргументы:
        user_id (int): Идентификатор пользователя, для которого нужно проверить период охлаждения.

    Возвращает: Tuple[bool, Optional[datetime.timedelta]]: Кортеж, где первый элемент - это булево значение,
    указывающее, активно ли охлаждение, а второй элемент - разница времени, если охлаждение активно, или None.
    """

    cooldown = fetch.get_value_by_id(user_id, 'cooldown')

    if cooldown:
        current_time = datetime.datetime.now()
        time_diff = current_time - cooldown

        if time_diff >= datetime.timedelta(hours=config.roulette_cooldown):
            cooldown = None

            db.connect()
            table = TgBotGame.get_by_id(user_id)
            table.cooldown = cooldown
            table.lives = config.default_lives
            table.save()
            db.close()

            return False, None

        else:
            return True, time_diff
    else:
        return False, None


async def handle_score_command(update, context):
    """
    Обрабатывает команду '/score' для отображения счета пользователя.

    Эта функция проверяет, имеет ли пользователь право на просмотр счета, и получает счет пользователя из базы данных.
    Если счет найден, она отправляет пользователю сообщение с его текущим счетом. Если пользователь еще не играл в
    рулетку, она отправляет сообщение, указывая, что он еще не играл.

    Аргументы:
        update (telegram.Update): Входящее обновление от Telegram.
        context (telegram.ext.CallbackContext): Контекст для текущего обновления.

    Возвращает:
        None
    """

    if str(update.message.chat.id) not in config.AUTHORIZED_USERS:
        return

    user_id = update.message.from_user.id
    user_message_id = update.message.message_id

    thread_id = update.message.message_thread_id if update.message.is_topic_message else None

    score = fetch.get_value_by_id(user_id, 'score')

    message_text = f'💰 Ваш счёт: {score}' if score is not None else 'Вы еще не играли в рулетку'

    await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id, message_text,
                                  parse_mode=constants.ParseMode.MARKDOWN, reply=True)


async def handle_leaderboard_command(update, context):
    """
    Обрабатывает команду '/leaderboard' для отображения доски лидеров.

    Эта функция проверяет, имеет ли пользователь право на просмотр доски лидеров, и получает доску лидеров из базы
    данных. Если доска лидеров найдена, она отправляет пользователю сообщение с доской лидеров. Если доска лидеров
    пуста, она отправляет сообщение, указывая, что никто еще не играл в рулетку.

    Аргументы:
        update (telegram.Update): Входящее обновление от Telegram.
        context (telegram.ext.CallbackContext): Контекст для текущего обновления.

    Возвращает:
        None
    """

    if str(update.message.chat.id) not in config.AUTHORIZED_USERS:
        return

    thread_id = update.message.message_thread_id if update.message.is_topic_message else None
    user_message_id = update.message.message_id

    db.connect()
    response = TgBotGame.select().order_by(TgBotGame.score.desc()).limit(10)
    board = [(entry.username, entry.score, entry.id) for entry in response]
    db.close()

    formatted_board = '\n'.join(
        f"{index + 1}) [{username}](https://t.me/{username}) | *{score}*" for index, (username, score, user_id) in
        enumerate(board)) if board else 'Никто еще не играл в рулетку'

    message_text = f'🏆 Топ 10 игроков:\n\n{formatted_board}'

    await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id, message_text,
                                  parse_mode=constants.ParseMode.MARKDOWN, disable_web_page_preview=True)


async def handle_retards(update, context):
    await context.bot.delete_message(update.effective_chat.id, update.message.message_id)


def init_handler(application):
    """
    Инициализирует и добавляет обработчики команд для приложения.

    Эта функция добавляет обработчики команд в приложение: '/roulette', '/score', '/unlock', '/leaderboard'.
    Эти обработчики отвечают за обработку команд и выполнение соответствующих функций.

    Аргументы:
        application (telegram.ext.Application): Приложение Telegram, в которое будут добавлены обработчики.

    Возвращает:
        None
    """

    application.add_handler(CommandHandler(['roulette', 'roll'], handle_roulette_command, block=False))
    application.add_handler(CommandHandler('score', handle_score_command, block=False))
    application.add_handler(CommandHandler('leaderboard', handle_leaderboard_command, block=False))
    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^/(ro|ru)', re.IGNORECASE)), handle_retards, block=False))

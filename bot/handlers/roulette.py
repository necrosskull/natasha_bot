import datetime
import random

from telegram import constants
from telegram.ext import CommandHandler

import bot.config as config
import bot.db.fetch as fetch
from bot.handlers.handler import send_and_delete_message

from bot.db.supabase import supabase


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

    data = fetch.fetch_multiple_params(user_id, 'lives', 'score')

    if data:
        lives, score = data
    else:
        lives, score = None, None

    if lives == 0:
        cooldown, time_diff = check_cooldown(user_id)

        if cooldown:
            remaining_minutes = 60 - time_diff.seconds // 60
            message_text = f'☠️ Полегче, ты своё отстрелял, пойди пока потрогай траву!\n' \
                           f'🕐 Осталось {remaining_minutes} минут\n' \
                           f'ℹ️ Вы можете разблокировать себя за 10 баллов используя /unlock'

            await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id,
                                          message_text,
                                          parse_mode=constants.ParseMode.MARKDOWN, reply=True)
            return

    if number > 6 or number < 1:
        message_text = 'Неверное число, введите число от 1 до 6'
        await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id,
                                      message_text,
                                      parse_mode=constants.ParseMode.MARKDOWN)
        return

    result = random.sample(range(1, 7), 2)

    if number in result:
        new_score = score + 10 if score is not None else 10
        supabase.table('tg_ban_bot_games').update({'username': username,
                                                   'score': new_score}).eq('id', user_id).execute()

        message_text = 'Браво, вы выиграли!\n✅ Вам начислено *10* баллов'

    else:
        if lives is not None:
            new_lives = lives - 1
            supabase.table('tg_ban_bot_games').update({'username': username,
                                                       'lives': new_lives}).eq('id', user_id).execute()
            lives = new_lives

        else:
            lives = config.default_lives - 1
            supabase.table('tg_ban_bot_games').insert(
                {'id': user_id, 'username': username, 'lives': lives}).execute()

        if lives == 0 or lives < 0:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

            supabase.table('tg_ban_bot_games').update({'cooldown': timestamp, 'lives': 0}).eq('id',
                                                                                              user_id).execute()

            message_text = f"💥 БАМ ТЫ СДОХ\n🚫 Все жизни потрачены, возвращайся через час\n" \
                           f"ℹ️ Вы можете разблокировать себя за 10 баллов используя /unlock"

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

    cooldown = fetch.fetch_by_id(user_id, 'cooldown')

    if cooldown:
        current_time = datetime.datetime.now()
        cooldown = datetime.datetime.strptime(cooldown, '%Y-%m-%dT%H:%M:%S')
        time_diff = current_time - cooldown

        if time_diff >= datetime.timedelta(hours=1):
            cooldown = None

            supabase.table('tg_ban_bot_games').update(
                {'lives': config.default_lives, 'cooldown': cooldown}).eq('id', user_id).execute()

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

    score = fetch.fetch_by_id(user_id, 'score')

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

    response = supabase.table('tg_ban_bot_games').select('username, score, id').order('score', desc=True).limit(
        10).execute()

    board = [(entry['username'], entry['score'], entry['id']) for entry in response.data]

    formatted_board = '\n'.join(
        f"{index + 1}) [{username}](https://t.me/{username}) | *{score}*" for index, (username, score, user_id) in
        enumerate(board)) if board else 'Никто еще не играл в рулетку'

    message_text = f'🏆 Топ 10 игроков:\n\n{formatted_board}'

    await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id, message_text,
                                  parse_mode=constants.ParseMode.MARKDOWN, disable_web_page_preview=True)


async def unlock_timer(update, context):
    """
    Обрабатывает команду '/unlock_timer' для разблокировки таймера

    Эта функция проверяет, имеет ли пользователь право на разблокировку таймера, и получает таймер из базы данных.
    Если таймер найден, она отправляет пользователю сообщение с его текущим таймером. Если пользователь еще не играл в
    рулетку, она отправляет сообщение, указывая, что он еще не играл.

    Аргументы:
        update (telegram.Update): Входящее обновление от Telegram.
        context (telegram.ext.CallbackContext): Контекст для текущего обновления.

    Возвращает:
        None
    """
    chat_id = str(update.message.chat.id)
    if chat_id not in config.AUTHORIZED_USERS:
        return

    user_id = update.message.from_user.id
    user_message_id = update.message.message_id
    thread_id = update.message.message_thread_id if update.message.is_topic_message else None

    data = fetch.fetch_multiple_params(user_id, 'lives', 'score')

    if data:
        lives, score = data
    else:
        lives, score = None, None

    check_cooldown(user_id)

    if score is not None:
        if score < 10:
            message_text = f"🚫 У вас недостаточно баллов для разблокировки\n" \
                           f"💵 Стоимость разблокировки: 10 баллов\n" \
                           f"💰 Ваш счёт: *{score}*"
        else:
            if lives > 0:
                message_text = f"⚡ У тебя ещё есть жизни, дурак?\n"
            else:
                new_score = score - 10
                cooldown = None
                supabase.table('tg_ban_bot_games').update({'score': new_score,
                                                           'lives': config.default_lives,
                                                           'cooldown': cooldown}).eq('id', user_id).execute()
                message_text = f"✅ Вы успешно разблокировали себя\n" \
                               f"💰 Ваш счёт: *{new_score}*"
    else:
        message_text = f"🚫 Вы еще не играли в рулетку"

    await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id,
                                  message_text,
                                  parse_mode=constants.ParseMode.MARKDOWN, reply=True)


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

    application.add_handler(CommandHandler('roulette', handle_roulette_command, block=False))
    application.add_handler(CommandHandler('score', handle_score_command, block=False))
    application.add_handler(CommandHandler('leaderboard', handle_leaderboard_command, block=False))
    application.add_handler(CommandHandler('unlock', unlock_timer, block=False))

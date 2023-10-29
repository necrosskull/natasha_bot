import datetime
import random

from telegram import constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler

import bot.config as config
import bot.db.fetch as fetch
from bot.handlers.handler import send_and_delete_message
from bot.handlers.scheduler import delete_message

from bot.db.sqlite import TgBotGame, db

COCKUNLOCK = range(1)


async def cock_game(update, context):
    """
    Эта функция позволяет авторизованным пользователям играть в игру для определения длины их 'хуя' (шутливая игра).
    Пользователь может играть в игру один раз в 24 часа. Игра случайным образом определяет, увеличивается,
    уменьшается или остается ли размер их хуя. Затем новый размер хуя сохраняется в базе данных
    вместе с отметкой времени, когда игра была сыграна.
    """

    if str(update.message.chat.id) not in config.AUTHORIZED_USERS:
        return

    username = update.message.from_user.username if update.message.from_user.username \
        else update.message.from_user.first_name
    thread_id = update.message.message_thread_id if update.message.is_topic_message else None
    user_id = update.message.from_user.id
    user_message_id = update.message.message_id

    cock_time = fetch.get_value_by_id(user_id, 'cock_time')
    cock_time, time_left = check_cock_time(user_id, cock_time)

    if cock_time:
        message_text = f'❌ Узнавать новую длину хуя можно раз в сутки!\n' \
                       f'🕐 Осталось {time_left}'

        await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id,
                                      message_text, reply=True, rm_button=user_id,
                                      parse_mode=constants.ParseMode.MARKDOWN)
        return

    cock_size = fetch.get_value_by_id(user_id, 'cock')

    modes = [cock_multiply(cock_size), cock_plus(cock_size)]
    new_size, msg, num = random.choices(modes, weights=[0.2, 0.8], k=1)[0]

    timestamp = datetime.datetime.now()

    if cock_size is not None:

        db.connect()
        table = TgBotGame.get_by_id(user_id)
        table.username = username
        table.cock = new_size
        table.cock_time = timestamp
        table.save()
        db.close()

    else:

        db.connect()
        TgBotGame.create(
            id=user_id,
            username=username,
            cock=new_size,
            cock_time=timestamp
        )
        db.close()

    if num > 0:
        sign = "📈"
    else:
        sign = "📉"

    if num == 0:
        message_text = f"{sign} Твой хуй {msg}\n☠️ Теперь его размер *{new_size} cм.*" \
                       f"\n😈 Размер отпавшего был *{cock_size} см.*"

        cockdrop = fetch.get_value_by_id(user_id, 'cockdrop')

        if cockdrop is not None:
            if cock_size > cockdrop:
                db.connect()
                table = TgBotGame.get_by_id(user_id)
                table.cockdrop = cock_size
                table.save()
                db.close()

        else:

            db.connect()
            table = TgBotGame.get_by_id(user_id)
            table.cockdrop = cock_size
            table.save()
            db.close()

    else:
        message_text = f"{sign} Твой хуй {msg}\n🍆 Теперь его размер *{new_size} cм.*" \
                       f"\n🕐 Попробуй ещё раз через 24 часа!"

    await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id,
                                  message_text,
                                  parse_mode=constants.ParseMode.MARKDOWN, reply=True, delete=False, rm_button=user_id)


def check_cock_time(user_id, cock_time):
    """
    Проверяет, может ли пользователь сыграть в игру 'cock_game', исходя из времени последней игры.
    Если пользователь уже играл в игру в течение последних 24 часов, функция возвращает оставшееся время
    до следующей возможности игры. Если пользователь еще не играл в игру, функция возвращает None.
    :param cock_time:
    :param user_id: Идентификатор пользователя для проверки времени ожидания игры.
    :return: Кортеж, в котором первый элемент является логическим значением (True, если пользователь не может играть,
             False - в противном случае), а второй элемент - строка с отформатированным временем до следующей игры,
             либо None, если пользователь еще не играл.
    """

    if cock_time is not None:

        current_time = datetime.datetime.now()
        time_diff = current_time - cock_time

        if time_diff >= datetime.timedelta(hours=24):
            cock_time = None

            db.connect()
            table = TgBotGame.get_by_id(user_id)
            table.cock_time = cock_time
            table.save()
            db.close()

            return False, None

        else:
            remain = datetime.timedelta(hours=24) - time_diff

            hours = remain.seconds // 3600
            minutes = (remain.seconds % 3600) // 60
            seconds = remain.seconds % 60

            time_left = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            return True, time_left

    else:
        return False, None


def cock_plus(cock_size):
    """
    Рассчитывает новый размер хуя и соответствующее сообщение, когда размер хуя пользователя увеличивается.
    :param cock_size: Текущий размер хуя пользователя.
    :return: Кортеж, содержащий новый размер хуя, отформатированное сообщение, описывающее изменение размера,
             и число, указывающее изменение (положительное значение, когда размер увеличивается).
    """

    num = random.choices([random.randint(1, 20), random.randint(-20, -1)], weights=[0.8, 0.2], k=1)[0]
    if num < 0:
        if cock_size and cock_size >= 100 and random.random() < 0.2:
            new_size = 0
            msg = f"*отвалился к хуям...*"
            num = 0
            return new_size, msg, num
        msg = f"*уменьшился* на *{abs(num)} см.*"

    else:
        msg = f"*увеличился* на *{num} см.*"
    if cock_size is not None:
        new_size = cock_size + num
    else:
        new_size = num
    return new_size, msg, num


def cock_multiply(cock_size):
    """
    Рассчитывает новый размер хуя и соответствующее сообщение, когда размер хуя пользователя умножается на 2.
    :param cock_size: Текущий размер хуя пользователя.
    :return: Кортеж, содержащий новый размер хуя, отформатированное сообщение, описывающее изменение размера,
             и число, указывающее изменение (всегда равно 2 в данном случае).
    """

    msg = f"*увеличился* в *2 раза*"
    if cock_size is not None:
        if cock_size >= 0:
            new_size = cock_size * 2
        else:
            new_size = 0
            msg = f"*вылез из пизды*"
    else:
        new_size = 0
    num = 2
    return new_size, msg, num


async def my_cock(update, context):
    """
    Эта функция позволяет авторизованным пользователям проверить текущий размер своего хуя в базе данных.
    """

    if str(update.message.chat.id) not in config.AUTHORIZED_USERS:
        return

    thread_id = update.message.message_thread_id if update.message.is_topic_message else None
    user_id = update.message.from_user.id
    user_message_id = update.message.message_id

    cock_size = fetch.get_value_by_id(user_id, 'cock')
    cock_drop = fetch.get_value_by_id(user_id, 'cockdrop')

    if cock_size is None:
        message_text = f"❌ У вас ещё нет хуя!\nИспользуйте /cock чтобы он у вас появился!"

    else:
        if cock_drop:
            drop_msg = f"\n☠️ Максимально отвалившийся хуй *{cock_drop} см.*"
        else:
            drop_msg = ''

        message_text = f"📏 Длина вашего хуя *{cock_size} см.*{drop_msg}"

    await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id,
                                  message_text,
                                  parse_mode=constants.ParseMode.MARKDOWN, reply=True)


async def buy_cock(update, context):
    """
    Позволяет авторизованным пользователям инициировать процесс сброса времени ожидания для игры 'cock_game'.
    Если у пользователя достаточно баллов 'score', он может продолжить сброс времени ожидания,
    подтвердив через встроенную клавиатуру. В противном случае выводится сообщение о необходимом количестве баллов.
    """

    authorized_users = config.AUTHORIZED_USERS
    cock_price = config.cock_price

    chat_id = update.effective_chat.id

    if str(chat_id) not in authorized_users:
        return

    user_id = update.message.from_user.id
    thread_id = update.message.message_thread_id if update.message.is_topic_message else None
    user_message_id = update.message.message_id

    data = fetch.get_values_by_id(user_id, 'score', 'cock_time')

    if data:
        score, cock_time = data
    else:
        score, cock_time = None, None

    cooldown = check_cock_time(user_id, cock_time)

    if cooldown is None:
        message_text = 'У тебя нет таймера, ебанат.'
        await send_and_delete_message(context, chat_id, thread_id, user_message_id, message_text,
                                      parse_mode=constants.ParseMode.MARKDOWN, reply=True)
        return

    if score is None:
        message_text = 'У вас ещё нет счёта, заработайте в рулетке!'

        await send_and_delete_message(context, chat_id, thread_id, user_message_id, message_text,
                                      parse_mode=constants.ParseMode.MARKDOWN, reply=True)
        return

    elif score >= cock_price:
        if 'f' in context.args:
            context.user_data['unlock_message_id'] = user_message_id
            return await reset_cock(update, context, firsttime=True, user_id=user_id)

        keyboard = [
            [InlineKeyboardButton("💰 Купить", callback_data=f'buy {user_id}')],
            [InlineKeyboardButton("❌ Отмена", callback_data=f'cancel {user_id}')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = f'Вы уверены, что хотите сбросить таймер хуя за {cock_price} баллов?'

        message = await context.bot.send_message(chat_id, message_thread_id=thread_id, text=message_text,
                                                 reply_markup=reply_markup)
        context.user_data['unlock_message_id'] = user_message_id
        context.job_queue.run_once(delete_message, 120, data=(message.message_id, user_message_id), chat_id=chat_id)
        return COCKUNLOCK

    else:
        message_text = f'Надо {cock_price} баллов, бомж.'

    await send_and_delete_message(context, chat_id, thread_id, user_message_id, message_text,
                                  parse_mode=constants.ParseMode.MARKDOWN, reply=True)


async def cock_unlock(update, context):
    """
    Обрабатывает ответ пользователя для подтверждения или отмены сброса времени ожидания для игры 'cock_game'.
    Если пользователь подтверждает сброс, время ожидания обнуляется, а соответствующие баллы 'score' уменьшаются.
    """

    cock_price = config.cock_price

    query = update.callback_query
    if str(query.data).startswith('r'):
        return

    user_id = query.from_user.id
    user_message_id = context.user_data['unlock_message_id']
    await query.answer()

    data_args = query.data.split(' ')

    if str(user_id) == data_args[1]:

        score = fetch.get_value_by_id(user_id, 'score')

        if score >= cock_price:
            button = data_args[0]

            if button == 'buy':
                await reset_cock(update, context, user_id=user_id, query=query)
            else:
                await query.delete_message()
                await context.bot.delete_message(update.effective_chat.id, user_message_id)

        else:
            message = await query.edit_message_text(text=f"У тя денег нет, иди нахуй.")
            context.job_queue.run_once(delete_message, config.delete_timer, data=(message.message_id, user_message_id),
                                       chat_id=update.effective_chat.id)
            return


async def reset_cock(update, context, firsttime=None, user_id=None, query=None):
    score = fetch.get_value_by_id(user_id, 'score')
    user_message_id = context.user_data['unlock_message_id']
    cock_price = config.cock_price
    cooldown = None
    new_score = score - cock_price

    db.connect()
    table = TgBotGame.get_by_id(user_id)
    table.cock_time = cooldown
    table.score = new_score
    table.save()
    db.close()

    if firsttime:
        message = await context.bot.send_message(chat_id=update.effective_chat.id,
                                                 text=f"✅ Вы успешно обнулили таймер!\nИспользуй /cock")

    else:
        message = await query.edit_message_text(text=f"✅ Вы успешно обнулили таймер!\nИспользуй /cock")

    context.job_queue.run_once(delete_message, config.delete_timer,
                               data=(message.message_id, user_message_id),
                               chat_id=update.effective_chat.id)


async def send_leaderboard(update, context, desc=False):
    """
    Отправляет сообщение с таблицей лидеров, в которой указаны топ-10 пользователей на основе размера их хуя,
    либо по убыванию, либо по возрастанию.
    :param update: Обновление Telegram.
    :param context: Контекст Telegram.
    :param desc: Логическое значение, указывающее, следует ли отображать таблицу лидеров по убыванию (True)
                 или по возрастанию (False).
    """

    if str(update.message.chat.id) not in config.AUTHORIZED_USERS:
        return

    thread_id = update.message.message_thread_id if update.message.is_topic_message else None
    user_message_id = update.message.message_id

    sort = True if desc else False

    db.connect()
    order_func = TgBotGame.cock.desc() if sort else TgBotGame.cock.asc()
    response = TgBotGame.select().order_by(order_func).limit(10)
    board = [(entry.username, entry.cock, entry.id) for entry in response]
    db.close()

    formatted_board = '\n'.join(
        f"{index + 1}) [{username}](https://t.me/{username}) | *{cock} см.*" for index, (username, cock, user_id) in
        enumerate(board))

    if len(formatted_board) < 1:
        formatted_board = f"Нет писек"

    leaderboard_type = "Топ 10 писек" if desc else "Топ 10 микро писек"

    message_text = f'🏆 {leaderboard_type}!\n\n{formatted_board}'

    await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id,
                                  message_text,
                                  parse_mode=constants.ParseMode.MARKDOWN, disable_web_page_preview=True)


async def cock_leaderboard(update, context):
    """
    Отображает топ-10 пользователей с самым большим размером 'хуя' в порядке убывания (от самого большого к самому
    маленькому).
    """

    await send_leaderboard(update, context, desc=True)


async def anti_cock_leaderboard(update, context):
    """
    Отображает топ-10 пользователей с самым маленьким размером 'хуя' в порядке возрастания (от самого маленького к
    самому большому).
    """

    await send_leaderboard(update, context, desc=False)


def init_handler(application):
    """
    Инициализирует и добавляет обработчики команд для приложения.

    Эта функция добавляет обработчики команд в приложение: '/cock', '/mycock', '/cocktop', '/cockantitop', '/cockreset'
    Эти обработчики отвечают за обработку команд и выполнение соответствующих функций.

    Аргументы:
        application (telegram.ext.Application): Приложение Telegram, в которое будут добавлены обработчики.

    Возвращает:
        None
    """
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('cockreset', buy_cock, block=False)],

        states={
            COCKUNLOCK: [
                CallbackQueryHandler(cock_unlock, block=False)]

        },
        fallbacks=[CommandHandler('cockreset', buy_cock, block=False)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('cock', cock_game, block=False))
    application.add_handler(CommandHandler('mycock', my_cock, block=False))
    application.add_handler(CommandHandler('cocktop', cock_leaderboard, block=False))
    application.add_handler(CommandHandler('cockantitop', anti_cock_leaderboard, block=False))

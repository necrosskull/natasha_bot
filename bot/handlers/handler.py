from telegram import constants, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

import bot.config as config
import bot.handlers.scheduler as scheduler
from bot.db.sqlite import TgBotGame, db


async def start(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.

    Отправляет сообщение с приветствием и списком команд.

    Аргументы:
        update (telegram.Update): Обновление, которое вызвало этот обработчик.
        context (telegram.ext.CallbackContext): Контекст для текущего обновления.

    Возвращает:
        telegram.Message: Отправленное сообщение.
    """

    if str(update.message.chat.id) not in config.AUTHORIZED_USERS:
        return

    thread_id = update.message.message_thread_id if update.message.is_topic_message else None
    user_message_id = update.message.message_id

    commands = '\n'.join(f'/{command[0]} - {command[1]}' for command in config.command_list)

    message_text = f"Список команд:\n\n" \
                   f'{commands}'

    await send_and_delete_message(context, update.effective_chat.id, thread_id, user_message_id,
                                  message_text,
                                  parse_mode=constants.ParseMode.MARKDOWN)


async def set_value_for_id(update, context):
    if str(update.message.from_user.id) not in config.AUTHORIZED_USERS:
        return

    args = context.args

    if len(args) != 3:
        return

    user_id = args[0]
    value = args[1]
    count = args[2]

    if count.isdigit():
        count = int(count)
    elif count == 'None':
        count = None

    db.connect()
    table = TgBotGame.get_by_id(user_id)

    if table is None:
        return

    setattr(table, value, count)
    table.save()
    db.close()

    await update.message.reply_text(f'Значение {count} установлено на {value}')


async def send_and_delete_message(context, chat_id, thread_id, reply_to_message_id, text, reply=False, delete=True,
                                  rm_button=False, **kwargs):
    """
    Отправляет сообщение в указанный чат, планирует его удаление через определенное время и при необходимости
    отвечает на определенное сообщение.

    Эта функция отвечает за отправку сообщения в указанный чат с предоставленным текстом и дополнительными
    аргументами. Если 'reply' равно True, она отвечает на указанное сообщение с помощью 'reply_to_message_id'. Также
    она планирует удаление сообщения через определенное время.

    Аргументы:
        context (telegram.ext.CallbackContext): Контекст для текущего обновления.
        chat_id (int): Идентификатор чата, в который будет отправлено сообщение.
        thread_id (Optional[int]): Идентификатор темы (при наличии).
        reply_to_message_id (Optional[int]): Идентификатор сообщения, на которое будет дан ответ (при наличии).
        text (str): Текст отправляемого сообщения.
        reply (bool): Флаг, указывающий, должно ли сообщение быть ответом на другое сообщение.
        **kwargs: Дополнительные аргументы, которые будут переданы методу 'send_message' бота Telegram.

    Возвращает:
        telegram.Message: Отправленное сообщение.
    """
    if not reply:
        user_message_id = None
    else:
        user_message_id = reply_to_message_id

    if rm_button:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Удалить", callback_data=f"rm {rm_button}")]])
    else:
        keyboard = None

    message = await context.bot.send_message(chat_id, message_thread_id=thread_id,
                                             reply_to_message_id=user_message_id, text=text, reply_markup=keyboard,
                                             **kwargs)
    if delete:
        context.job_queue.run_once(scheduler.delete_message, config.delete_timer,
                                   data=(message.message_id, reply_to_message_id), chat_id=chat_id)
    return message


async def remove(update, context):
    if str(update.message.from_user.id) not in config.AUTHORIZED_USERS:
        return

    user_message_id = update.message.message_id
    replied_message = update.message.reply_to_message.message_id

    messages = [replied_message, user_message_id]

    for message in messages:
        await context.bot.delete_message(update.effective_chat.id, message)


async def remove_button(update, context):
    query = update.callback_query

    if str(query.data).startswith('rm'):
        await query.answer()

        args = query.data.split(' ')
        user_id = query.from_user.id

        if str(user_id) != args[1] and str(user_id) not in config.AUTHORIZED_USERS:
            await update.callback_query.answer('Это не ваше сообщение!')
            return

        await context.bot.delete_message(query.message.chat_id, query.message.message_id)


async def for_banned(update, context):
    return


def init_handler(application):
    """
     Инициализирует и добавляет обработчики команд для приложения.

     Эта функция добавляет обработчики команд в приложение: '/start' и '/help'.
     Эти обработчики отвечают за обработку команд и выполнение соответствующих функций.

     Аргументы:
         application (telegram.ext.Application): Приложение Telegram, в которое будут добавлены обработчики.

     Возвращает:
         None
     """
    application.add_handler(MessageHandler(filters.User(user_id=config.BANNED), for_banned, block=False))
    application.add_handler(CommandHandler('start', start, block=False))
    application.add_handler(CommandHandler('help', start, block=False))
    application.add_handler(CommandHandler('rm', remove, block=False))
    application.add_handler(CommandHandler('set', set_value_for_id, block=False))
    application.add_handler(CallbackQueryHandler(remove_button, pattern='^rm', block=False))

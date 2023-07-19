from telegram import constants
from telegram.ext import CommandHandler, ContextTypes

import bot.config as config
import bot.handlers.scheduler as scheduler


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


async def send_and_delete_message(context, chat_id, thread_id, reply_to_message_id, text, reply=False, delete=True,
                                  **kwargs):
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

    message = await context.bot.send_message(chat_id, message_thread_id=thread_id,
                                             reply_to_message_id=user_message_id, text=text, **kwargs)
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

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', start))

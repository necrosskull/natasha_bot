import telegram


async def delete_message(context):
    chat_id = context.job.chat_id
    msgs = context.job.data

    if isinstance(context.job.data, int):
        msgs = [context.job.data]

    for message in msgs:
        try:
            await context.bot.delete_message(chat_id, message)
        except telegram.error.BadRequest as e:
            pass

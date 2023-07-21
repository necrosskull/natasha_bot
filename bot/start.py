from telegram.ext import Application

import bot.config as config
import bot.handlers.handler as handler
import bot.handlers.roulette as roulette
import bot.handlers.cockgame as cock

import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def main():
    application = Application.builder().token(config.TELEGRAM_TOKEN).post_init(
        post_init=post_init).build()

    roulette.init_handler(application)
    handler.init_handler(application)
    cock.init_handler(application)

    application.run_polling()


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        commands=config.command_list
    )


if __name__ == '__main__':
    main()

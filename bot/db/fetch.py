from peewee import DoesNotExist

from bot.db.sqlite import TgBotGame, db


def get_value_by_id(user_id, key):
    db.connect()
    try:
        game = TgBotGame.get_by_id(user_id)
        return getattr(game, key, None)

    except DoesNotExist:
        return None

    finally:
        db.close()


def get_values_by_id(user_id, *keys):
    db.connect()
    try:
        game = TgBotGame.get_by_id(user_id)
        values = tuple(getattr(game, key, None) for key in keys)
        return values
    except DoesNotExist:
        return None

    finally:
        db.close()

import os

from peewee import *

db = SqliteDatabase(os.path.join(os.path.dirname(__file__), 'tg_bot.db'))


class TgBotGame(Model):
    id = PrimaryKeyField(unique=True)
    username = TextField()
    score = IntegerField(default=0)
    lives = IntegerField(default=3)
    cooldown = TimestampField(null=True, default=None)
    cock = IntegerField(default=0)
    cock_time = TimestampField(null=True, default=None)
    cockdrop = IntegerField(null=True, default=None)
    banned = BooleanField(default=False)

    class Meta:
        database = db

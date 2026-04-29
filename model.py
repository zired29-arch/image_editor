from peewee import *
import datetime

db = SqliteDatabase("users.db")

class User(Model):
    username = CharField(unique=True)
    password = CharField()
    email = CharField(unique=True, null=True)

    class Meta():
        database = db

class Photo(Model):
    url = CharField()
    clone = BooleanField(default=False)
    width = CharField()
    height = CharField()
    date = DateTimeField(default=datetime.datetime.now)
    user = ForeignKeyField(User, backref="photos")

    class Meta():
        database = db

db.connect()
db.create_tables([User, Photo])
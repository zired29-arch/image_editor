import schedule
import datetime
import os
from time import sleep
from model import Photo, db


def delete():
    if db.is_closed():
        db.connect()
    cutoff_date = datetime.datetime.now() - datetime.timedelta(minutes=1)
    all_photos = Photo.select().where(Photo.date < cutoff_date)
    for photo in all_photos:
        if os.path.exists(os.path.join("static/images", photo.url)):
            os.remove(os.path.join("static/images", photo.url))
        photo.delete_instance()
        

schedule.every().monday.at("03:00").do(delete)
while True:
    schedule.run_pending()
    sleep(5)
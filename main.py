from flask import Flask, render_template, request, session, redirect, abort, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
from dotenv import load_dotenv
from model import User, Photo
import os, re, logging
from logging.handlers import SMTPHandler
import utils


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
mail_key = os.getenv("MAILKEY")
email = os.getenv("EMAIL")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - - %(levelname)s - - %(message)s")
peewee_logger = logging.getLogger("peewee")
peewee_logger.setLevel(logging.DEBUG)

mail_handler = SMTPHandler(
    mailhost=("smtp.yandex.ru", 587), 
    fromaddr=email, 
    toaddrs=[email],
    subject="Сообщение об ошибке",
    credentials=(email, mail_key),
    secure=()
)

app.logger.addHandler(mail_handler)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

pattern = r'^[a-zA-Z0-9_!]{6,20}$'

@app.route('/', methods=["GET", "POST"])
def index():
    if session.get("username"):
        return redirect("/redactor")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not re.match(pattern, username) or not re.match(pattern, password):
            return render_template("index.html", logtype="Регистрация", error="Недопустимое имя или пароль!")
        hash = generate_password_hash(password)
        user_exists = User.get_or_none(User.username == username)
        if user_exists:
            return render_template("index.html", logtype="Регистрация", error="Такой пользователь уже существует!")
        user = User.create(username=username, password=hash)
        session["username"] = user.username
        session["user_id"] = user.id
        app.logger.info(f"В базе данных появился новый юзер: {user.id}-{username}")
        return redirect("/redactor")
    return render_template("index.html", logtype="Регистрация")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user_exists = User.get_or_none(User.username == username)
        if user_exists:
            if check_password_hash(user_exists.password, password):
                session["user_id"] = user_exists.id
                session["username"] = user_exists.username
                for photo in user_exists.photos:
                    session["image_id"] = photo.id
                return redirect("/redactor")
        return render_template("index.html", logtype="Войти", error="Неправильный пароль или имя пользователя")
    return render_template("index.html", logtype="Войти")

@app.route("/redactor", methods=["POST", "GET"])
def image_redactor():
    if not session.get("user_id"):
        return redirect("/")
    if request.method == "POST":
        try:
            img = request.files["image"]
            ext = img.filename
            ext = "." + ext.split('.')[1]
            img.save(os.path.join(UPLOAD_FOLDER, session["username"]) + ext)
            img_copy = Image.open(os.path.join(UPLOAD_FOLDER, session["username"]) + ext)
            width, height = utils.get_scale(os.path.join(UPLOAD_FOLDER, session["username"]) + ext)
            if width > 1024 or height > 1024:
                img_copy.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                width, height = img_copy.width, img_copy.height
            img_copy.save(os.path.join(UPLOAD_FOLDER, session["username"]) + "_clone" + ext)
            img_copy.save(os.path.join(UPLOAD_FOLDER, session["username"]) + ext)
            image = Photo.get_or_none(Photo.user == User.get_or_none(User.username == session["username"]))
            if image:
                os.remove(os.path.join("static/images", image.url))
                os.remove(os.path.join("static/images", session["username"] + "_clone" + "." + image.url.split(".")[-1]))
                image.width = width
                image.height = height
                image.url = os.path.join(session["username"]) + ext
                image.save()
            else:
                image = Photo.create(url=os.path.join(session["username"]) + ext, width=width, height=height, user=session["user_id"])
                image_clone = Photo.create(url=os.path.join(session["username"]) + "_clone" + ext, clone=True, width=width, height=height, user=session["user_id"])
            session["image_id"] = image.id
            return redirect("/redactor/" + str(image.id))
        except Exception as e:
            app.logger.error(e)
    return render_template("insert_image.html")

@app.route("/redactor/<int:id>", methods=["POST", "GET"])
def load_image(id):
    image = Photo.get_or_none(Photo.id == id)
    if not image or image.user.username != session.get("username"):
        return abort(403)
    if request.method == "POST":
        ext = "." + image.url.split('.')[1]
        image.clone = False
        image.save()
        button_pressed = request.form.get("action")
        if button_pressed != "return":
            img = Image.open(os.path.join(UPLOAD_FOLDER, session["username"]) + ext)
            img.save(os.path.join(UPLOAD_FOLDER, session["username"]) + "_clone" + ext)
            if button_pressed == "rotate_right":
                utils.rotate_right(os.path.join("static/images", image.url))
            if button_pressed == "rotate_left":
                utils.rotate_left(os.path.join("static/images", image.url))
            if button_pressed == "flip":
                utils.flip_image(os.path.join("static/images", image.url))
            if button_pressed == "make_grey":
                utils.make_grey(os.path.join("static/images", image.url))
            if button_pressed == "make_emboss":
                utils.emboss_image(os.path.join("static/images", image.url))
            if button_pressed == "make_sharp":
                sharp_value = request.form.get("sharp_value")
                utils.sharpen_image(os.path.join("static/images", image.url), value=sharp_value)
            if button_pressed == "make_blur":
                blur_value = request.form.get("blur_value")
                utils.blur_image(os.path.join("static/images", image.url), value=blur_value)
        else:
            user = User.get_or_none(User.username == session["username"])
            for photo in user.photos:
                if photo.clone:
                    img = Image.open(os.path.join(UPLOAD_FOLDER, session["username"]) + "_clone" + ext)
                    img.save(os.path.join(UPLOAD_FOLDER, session["username"]) + ext)
                    image.clone = True
                    image.save()
    return render_template("redactor.html", image_path=image.url, image_scale=f"{image.width}x{image.height}", clone=image.clone)

@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)
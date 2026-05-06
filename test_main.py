import pytest
import io
import os
from main import app
from PIL import Image
from bs4 import BeautifulSoup
from peewee import *
from model import User, Photo


@pytest.fixture
def client():
    test_db = SqliteDatabase(":memory:")
    test_db.bind([User, Photo], bind_refs=False, bind_backrefs=False)
    test_db.connect()
    test_db.create_tables([User, Photo])
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    test_db.drop_tables([User, Photo])
    test_db.close()


def test_client(client):
    response = client.get("/")
    html_content = response.data.decode("UTF-8")
    soup = BeautifulSoup(html_content, "html.parser")
    h1 = soup.find("h1")
    assert h1 is not None
    assert h1.text == " Редактор изображений "
    
def test_redirect(client):
    response = client.get("/redactor")
    assert response.status_code == 302
    
def test_response_code(client):
    response = client.get("/redactor/1")
    assert response.status_code == 403

def test_registration_succes(client):
    form_data = {"username": "qqqwwwerty123",
                 "password": "qqqwwwerty123"
                 }
    response = client.post("/", data=form_data)
    assert response.status_code == 302

def test_registration_fail(client):
    form_data = {"username": "^",
                 "password": "^"
                 }
    response = client.post("/", data=form_data)
    assert response.status_code == 200
    html_content = response.data.decode("UTF-8")
    soup = BeautifulSoup(html_content, "html.parser")
    error_text = soup.find("p")
    assert error_text.text == " Недопустимое имя или пароль! "

def test_registration_fail_user_exists(client):
    form_data = {"username": "qwerty123",
                 "password": "qwerty123"
                 }
    response = client.post("/", data=form_data)
    assert response.status_code == 302
    client.get("/logout")
    response = client.post("/", data=form_data)
    assert response.status_code == 200
    html_content = response.data.decode("UTF-8")
    soup = BeautifulSoup(html_content, "html.parser")
    error_text = soup.find("p")
    assert error_text.text == " Такой пользователь уже существует! "


def test_login_get(client):
    response = client.get("/login")
    html_content = response.data.decode("UTF-8")
    soup = BeautifulSoup(html_content, "html.parser")
    h1 = soup.find("h1")
    assert h1 is not None
    assert h1.text == " Редактор изображений "


def test_login_success(client):
    form_data = {"username": "qwerty123",
                 "password": "qwerty123"}
    response = client.post("/", data=form_data)
    client.get("/logout")
    response = client.post("/login", data=form_data)
    assert response.status_code == 302


def test_login_fail_user_isnt_exists(client):
    form_data = {"username": "^",
                 "password": "^"
                 }
    response = client.post("/", data=form_data)
    client.get("/logout")
    response = client.post("/login", data=form_data)
    assert response.status_code == 200


def test_login_fail_incorrect_password(client):
    form_data = {"username": "qwerty123",
                 "password": "qwerty123"}
    response = client.post("/", data=form_data)
    client.get("/logout")
    form_data["password"] = "a"
    response = client.post("/login", data=form_data)
    assert response.status_code == 200


def test_redactor_get(client):
    form_data = {"username": "qwerty123",
                 "password": "qwerty123"}
    response = client.post("/", data=form_data)
    response = client.get("/redactor")
    html_content = response.data.decode("UTF-8")
    soup = BeautifulSoup(html_content, "html.parser")
    h2 = soup.find("h2")
    assert h2 is not None
    assert h2.text == " Картинка отсутствует! "


def test_redactor_image_db_append(client):
    username = "qwerty123"
    form_data = {"username": username,
                 "password": "qwerty123"}
    response = client.post("/", data=form_data)
    image = Image.new("RGB", (1, 1), color="red")
    io_image = io.BytesIO()
    image.save(io_image, format="JPEG")
    io_image.seek(0)
    form_data = {"image": (io_image, username + ".jpg")}
    response = client.post("/redactor", data=form_data, content_type="multipart/form-data")
    assert response.status_code == 302
    assert Photo.get_or_none(Photo.user == User.get_or_none(User.username == username))
    os.remove(os.path.join("static/images", username + ".jpg"))
    os.remove(os.path.join("static/images", username + "_clone" + ".jpg"))
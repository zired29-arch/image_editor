from PIL import Image, ImageOps, ImageFilter


def get_scale(image_path):
    image = Image.open(image_path)
    width, height = image.width, image.height
    return width, height

def rotate_right(image_path):
    image = Image.open(image_path)
    image = image.rotate(270, expand=True)
    image.save(image_path)

def rotate_left(image_path):
    image = Image.open(image_path)
    image = image.rotate(90, expand=True)
    image.save(image_path)

def flip_image(image_path):
    image = Image.open(image_path)
    image = image.transpose(Image.FLIP_LEFT_RIGHT)
    image.save(image_path)

def make_grey(image_path):
    image = Image.open(image_path)
    image = ImageOps.grayscale(image)
    image.save(image_path)

def emboss_image(image_path):
    image = Image.open(image_path)
    image = image.filter(ImageFilter.EMBOSS)
    image.save(image_path)

def sharpen_image(image_path, value=1):
    if int(value) >= 5:
        value = 5
    image = Image.open(image_path)
    for i in range(int(value)):
        image = image.filter(ImageFilter.SHARPEN)
    image.save(image_path)

def blur_image(image_path, value=1):
    if int(value) >= 5:
        value = 5
    image = Image.open(image_path)
    for i in range(int(value)):
        image = image.filter(ImageFilter.BLUR)
    image.save(image_path)
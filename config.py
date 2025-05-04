import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or "BandaiNamco"
    SQLALCHEMY_DATABASE_URI = (os.environ.get('DATABASE_URL') or \
                               'sqlite:///' + os.path.join(basedir, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'andrew.swartz.cs205@gmail.com'
    MAIL_PASSWORD = 'iaqb jhoy chvi nbqo'
    MAIL_DEFAULT_SENDER = 'andrew.swartz.cs205@gmail.com'
    ADMINS = ["andrew.swartz.cs205@gmail.com"]
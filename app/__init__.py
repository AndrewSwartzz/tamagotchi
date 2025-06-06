from logging.handlers import RotatingFileHandler
import logging


from flask import Flask
from flask_login import LoginManager
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_mail import Mail


app = Flask(__name__)
app.config.from_object(Config)
mail = Mail()
mail.init_app(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from app import routes, models
from flask_mail import Mail


csrf = CSRFProtect(app)
app.jinja_env.globals['csrf_token'] = generate_csrf

handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

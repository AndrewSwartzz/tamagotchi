from flask import Flask
from flask_login import LoginManager
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

# Import routes (and models) after the app/db objects exist
from app import routes, models

csrf = CSRFProtect(app)
# Make {{ csrf_token() }} available in every template
app.jinja_env.globals['csrf_token'] = generate_csrf
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from config import config
from flask_mail import Mail


db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
photos = UploadSet('photos', IMAGES)


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    login_manager.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    configure_uploads(app, photos)
    patch_request_class(app)

    from .views import main, auth
    app.register_blueprint(main.main)
    app.register_blueprint(auth.auth, url_prefix='/auth')
    return app

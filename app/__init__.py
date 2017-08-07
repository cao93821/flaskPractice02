from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from config import config

# app = Flask(__name__)
# app.config.from_object(config['default'])
# db = SQLAlchemy(app)
#
# migrate = Migrate(app, db)
#
# login_manager = LoginManager()
# login_manager.init_app(app)
#
# photos = UploadSet('photos', IMAGES)
# configure_uploads(app, photos)
# patch_request_class(app)
#
# from app import views, models

db = SQLAlchemy()
login_manager = LoginManager()
photos = UploadSet('photos', IMAGES)


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    login_manager.init_app(app)
    db.init_app(app)
    configure_uploads(app, photos)
    patch_request_class(app)

    from .views import main, auth
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    return app

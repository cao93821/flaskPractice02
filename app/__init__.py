from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_mail import Mail
from raven.contrib.flask import Sentry
from flask_pagedown import PageDown

from config import config


db = SQLAlchemy()
email = Mail()
login_manager = LoginManager()
# 注册login_required跳转的端点
login_manager.login_view = 'auth.login'
photos = UploadSet('photos', IMAGES)
pagedown = PageDown()
sentry = Sentry()


def create_app(config_name):
    """Flask app的工厂函数

    :param config_name: 配置名(str)
    :return: WSGI app
    :rtype: Flask
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    login_manager.init_app(app)
    db.init_app(app)
    email.init_app(app)
    pagedown.init_app(app)
    configure_uploads(app, photos)
    patch_request_class(app)
    if config_name != 'test':
        sentry.init_app(app, dsn=app.config['SENTRY_DSN'])
        # 测试的时候不能用，因为测试数据库是create_app之后创建的
        # 而且只有flask-sqlalchemy的执行语句只有应用上下文被push之后才能使用
        app.app_context().push()
        from .models import Role
        Role.insert_role()

    from .views import main, auth
    app.register_blueprint(main.main)
    app.register_blueprint(auth.auth, url_prefix='/auth')
    return app

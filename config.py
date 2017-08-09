import os
basedir = os.path.abspath(os.path.dirname(__file__))

# CSRF_ENABLED = True
# SECRET_KEY = 'you-will-never-guess'
# UPLOADED_PHOTOS_DEST = '/Users/caolei/flaskLearning/flaskPractice02/app/static/img'
#
# SQLALCHEMY_DATABASE_URI = 'mysql://root:yiwen517112@139.196.77.131/flask_test'
# SQLALCHEMY_ECHO = True


class Config:
    CSRF_ENABLED = True
    SECRET_KEY = 'you-will-never-guess'
    SQLALCHEMY_ECHO = True
    UPLOADED_PHOTOS_DEST = os.path.join(basedir, 'app/static/img')
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = '465'
    MAIL_USE_SSL = True
    MAIL_USERNAME = '657391552@qq.com'
    MAIL_PASSWORD = 'turlbwptihpkbebf'
    FLASK_MAIL_SENDER = 'Admin <657391552@qq.com>'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:yiwen517112@139.196.77.131/flask_test'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:yiwen517112@139.196.77.131/flask_unittest'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://root:yiwen517112@139.196.77.131/flask'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestingConfig,
    'default': DevelopmentConfig
}

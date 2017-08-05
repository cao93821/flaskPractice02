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


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:yiwen517112@139.196.77.131/flask_test'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://root:yiwen517112@139.196.77.131/flask'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

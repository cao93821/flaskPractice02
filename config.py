import os

# 永远获取绝对路径
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY最保险的是从环境变量当中获取
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
    SENTRY_DSN = 'http://ea5f8dfcc4be45db8f5b290704b83cdf:095c1899cbda4342bf4fff11b60d3ea3@139.196.77.131:9000/2'


class TestingConfig(Config):
    # 需要在单元测试当中关闭CSRF验证，不然对于表单的测试会比较麻烦，关闭后使用{{ form.hidden_tag() }}会直接为空
    WTF_CSRF_ENABLED = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:yiwen517112@139.196.77.131/flask_unittest'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://root:yiwen517112@139.196.77.131/flask'
    SENTRY_DSN = 'http://962494174ddc4a07b140ad4267321e48:763a4cfad6634a97a5f018d13856f126@139.196.77.131:9000/8'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestingConfig,
    'default': DevelopmentConfig
}

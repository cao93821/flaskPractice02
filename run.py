import os

from flask_migrate import Migrate
from flask_script import Manager, Shell
from flask_migrate import MigrateCommand


# 不得不放在这个位置以使COV先于blueprint等的初始化启动
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

from app import create_app, db


# 默认情况下是应用开发环境的配置，在生产服务器当中配置FLASK_CONFIG环境变量使得能够使用生产环境的配置
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# 这两个东西的初始化在这个层级比较合适，因为其功能是与flask app功能无关的
manager = Manager(app)
migrate = Migrate(app, db)


@manager.command
def test(cover=False):
    """测试命令，运行单元测试

    :param cover: 为避免与导入的coverage包名重复，使用cover作为产出测试报告的参数，使用python run.py test --cover即可
    :return:
    """
    # 结合顶部的COV.start()使用，要产生测试报告的时候重启程序以使COV先于程序的所有初始化过程而启动
    if cover and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        # os.execvp用来开启一个新程序代替现在的程序，sys.executable是指运行程序
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    # 启动单元测试
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        # 下面都是为了print出coverage报告的绝对路径
        print('Coverage Summary:')
        # 这个语句在任何情况下获取绝对路径
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://{}/index.html'.format(covdir))
        COV.erase()


def make_shell_context():
    """用来在shell环境当中提供上下文，app指代当前的Flask对象"""
    return dict(app=app)


# 添加两个基本命令
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()


from app import create_app

# application是用来给uWSGI服务器调用的callable
application = create_app("production")


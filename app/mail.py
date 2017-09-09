from flask import render_template, current_app
from flask_mail import Message

from . import email


def send_email(to, subject, template, **kwargs):
    """用来发送邮件的工具函数

    :param to: 接收者(str)
    :param subject: 发送标题(str)
    :param template: 模板
    :param kwargs: 模板参数
    """
    msg = Message(subject,
                  sender=current_app.config['FLASK_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    email.send(msg)

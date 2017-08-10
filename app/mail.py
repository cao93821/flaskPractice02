from . import mail
from flask import render_template, current_app
from flask_mail import Message


def send_email(to, subject, template, **kwargs):
    msg = Message(subject,
                  sender=current_app.config['FLASK_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    mail.send(msg)
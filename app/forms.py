from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired, equal_to
from flask_wtf.file import FileRequired, FileAllowed
from app import photos


class LoginForm(Form):
    user_name = StringField('user name', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField('Log in')


class SignupFrom(Form):
    email = StringField('email', validators=[DataRequired()])
    user_name = StringField('user name', validators=[DataRequired()])
    password = PasswordField('password', validators=[
        DataRequired(), equal_to('password2', message='passwords must match')])
    password2 = PasswordField('confirm.txt password', validators=[DataRequired()])
    submit = SubmitField('Sign up')


class ReleaseForm(Form):
    title = StringField('title', validators=[DataRequired()])
    body = TextAreaField('body', validators=[DataRequired()])
    photo = FileField('photo', validators=[
        FileAllowed(photos, 'only picture'),
        FileRequired('have not select a picture')
    ])
    submit = SubmitField('submit')


class CommentForm(Form):
    comment = TextAreaField('comment', validators=[DataRequired()])
    submit = SubmitField('Submit')

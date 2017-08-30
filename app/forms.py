from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, equal_to, Length, ValidationError
from flask_wtf.file import FileRequired, FileAllowed
from app import photos, db
from .models import Role, User
from flask_pagedown.fields import PageDownField


class LoginForm(Form):
    user_name = StringField('user name', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField('Log in')


class SignupFrom(Form):
    email = StringField('email', validators=[DataRequired()])
    user_name = StringField('user name', validators=[DataRequired()])
    password = PasswordField('password', validators=[
        DataRequired(), equal_to('password2', message='passwords must match')])
    password2 = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField('Sign up')


class ReleaseForm(Form):
    title = StringField('title', validators=[DataRequired()])
    body = PageDownField('body', validators=[DataRequired()])
    photo = FileField('photo', validators=[
        FileAllowed(photos, 'only picture'),
        FileRequired('have not select a picture')
    ])
    submit = SubmitField('submit')


class CommentForm(Form):
    comment = TextAreaField('comment', validators=[DataRequired()])
    submit = SubmitField('Submit')


class ForgetPasswordForm(Form):
    email = StringField('email', validators=[DataRequired()])
    submit = SubmitField('send email')


class PasswordResetForm(Form):
    new_password = PasswordField('new_password', validators=[
        DataRequired(), equal_to('new_password2', message='passwords must match')
    ])
    new_password2 = PasswordField('new_password2', validators=[DataRequired()])
    submit = SubmitField('reset password')


class SetNewEmailForm(Form):
    new_email = StringField('email', validators=[DataRequired()])
    submit = SubmitField('reset email')


class EditUserProfileForm(Form):
    real_name = StringField('real_name', validators=[Length(0, 64)])
    about_me = TextAreaField('about_me')
    submit = SubmitField('submit')


class EditUserProfileAdminForm(Form):
    email = StringField('email', validators=[DataRequired(), Length(1, 64)])
    user_name = StringField('user_name', validators=[DataRequired(), Length(1, 64)])
    confirmed = BooleanField('confirmed')
    role = SelectField('role', coerce=int)  # 这里是要对data做一个强制类型转换
    real_name = StringField('real_name', validators=[Length(0, 64)])
    about_me = TextAreaField('about_me')
    submit = SubmitField('submit')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in db.session.query(Role).all()]  # choice的前一个是value，后一个label，很简单看看源码就明白了
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and db.session.query(User).filter_by(email=field.data).first():
            raise ValidationError('Email is already used')

    def validate_user_name(self, field):
        if field.data != self.user.user_name and db.session.query(User).filter_by(user_name=field.data).first():
            raise ValidationError('user name is already used')

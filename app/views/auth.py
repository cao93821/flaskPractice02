import logging

from flask import render_template, redirect, flash, url_for, Blueprint
from flask_login import login_required, login_user, logout_user, current_user

from .. import db
from ..models import User
from ..forms import LoginForm, SignupFrom, ForgetPasswordForm, PasswordResetForm, SetNewEmailForm
from ..mail import send_email


auth = Blueprint('auth', __name__)


# 初始化一个logger
logger = logging.Logger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('name: %(name)s\nlevel: %(levelname)s\n%(message)s\n'))
logger.addHandler(handler)


@auth.before_app_request
def before_request():
    """通过before_app_request在用户每次请求的时候更新用户的最近上线时间"""
    if current_user.is_authenticated:
        current_user.update_last_online_time()


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """注册"""
    form = SignupFrom()
    if form.validate_on_submit():
        if db.session.query(User).filter_by(user_name=form.user_name.data).first():
            flash("The user's name already exist", category='error')
            return redirect(url_for('auth.signup'))
        else:
            user = User(email=form.email.data, user_name=form.user_name.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            token = user.generate_confirmation_token()
            send_email(user.email, 'Confirm Your Account', 'auth/confirm', user=user, token=token)
            flash('A confirmation email has been sent to you by email')
            return redirect(url_for('main.index'))
    return render_template('auth/signup.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    """确认注册"""
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    elif current_user.confirm(token):
        flash('You have confirmed your account')
        return redirect(url_for('main.index'))
    else:
        flash('The confirm link is invalid')
    return redirect(url_for('main.index'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(user_name=form.user_name.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user)
            flash('Hello {}'.format(form.user_name.data))
            return redirect(url_for('main.index'))

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/forget-password', methods=['GET', 'POST'])
def forget_password():
    """忘记密码"""
    form = ForgetPasswordForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user:
            token = user.generate_confirmation_token()
            send_email(user.email, 'password reset', 'auth/password-reset', user=user, token=token)
            flash('email has been send')
            return redirect(url_for('auth.forget_password'))
        else:
            flash('email is not exist')
            return redirect(url_for('auth.forget_password'))
    return render_template('auth/forget-password.html', form=form)


@auth.route('/password-reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    """重置密码（忘记密码的情况下使用）"""
    form = PasswordResetForm()
    if form.validate_on_submit():
        if User.password_reset_token_confirm(token, form.new_password.data):
            flash('password reset success')
            if current_user.is_authenticated:
                return redirect(url_for('main.index'))
            else:
                return redirect(url_for('auth.login'))

    return render_template('auth/password-reset.html', form=form, token=token)


@auth.route('/password-change', methods=['GET'])
@login_required
def change_password():
    """修改密码"""
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'change password', 'auth/password-reset', user=current_user, token=token)
    flash('email has been send')
    return redirect(url_for('main.administration'))


@auth.route('/email-change', methods=['GET'])
@login_required
def change_email():
    """修改邮箱，直接向该用户的原邮箱发一封邮件"""
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'change email', 'auth/email-change', user=current_user, token=token)
    flash('email has been send')
    return redirect(url_for('main.administration'))


@auth.route('/set-new-email/<token>', methods=['GET', 'POST'])
@login_required
def set_new_email(token):
    """设置新邮箱，通过收到的邮件进入到新邮箱的设置页面，设置后向该用户的新邮箱发一封邮件"""
    form = SetNewEmailForm()
    if form.validate_on_submit():
        if current_user.email_reset_token_confirm(token):
            confirm_token = current_user.generate_confirmation_token(3600, form.new_email.data)
            send_email(form.new_email.data,
                       'confirm email',
                       'auth/email-confirm',
                       user=current_user,
                       token=confirm_token)
            flash('email has been send')
            return redirect(url_for('main.administration'))
    return render_template('auth/set-new-email.html', form=form, token=token)


@auth.route('/email-confirm/<token>')
@login_required
def email_confirm(token):
    """确认新邮件"""
    if current_user.new_email_token_confirm(token):
        flash('email has been reset')
        return redirect(url_for('main.administration'))

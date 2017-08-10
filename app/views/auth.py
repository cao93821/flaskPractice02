from .. import db
from flask import render_template, redirect, flash, url_for, Blueprint
from ..models import User
from ..forms import LoginForm, SignupFrom
from flask_login import login_required, login_user, logout_user, current_user
from ..mail import send_email

auth = Blueprint('auth', __name__)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
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
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(user_name=form.user_name.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user)
            flash('Hello {}'.format(form.user_name.data))
            return redirect('/index')

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
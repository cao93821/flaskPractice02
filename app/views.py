from . import db, login_manager, photos, mail
from flask import render_template, redirect, flash, url_for, send_from_directory, Blueprint, current_app
from .models import Blog, User, Comment
from .forms import LoginForm, ReleaseForm, CommentForm, SignupFrom
from flask_login import login_required, login_user, logout_user, current_user
from datetime import date
from config import Config
from flask_mail import Message

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)


def date_transform(raw_date):
    month_transform = {1: 'January',
                       2: 'February',
                       3: 'March',
                       4: 'April',
                       5: 'May',
                       6: 'June',
                       7: 'July',
                       8: 'August',
                       9: 'September',
                       10: 'October',
                       11: 'November',
                       12: 'December'}
    return '{} {} {}'.format(raw_date.day, month_transform[raw_date.month], raw_date.year)


def send_email(to, subject, template, **kwargs):
    msg = Message(subject,
                  sender=current_app.config['FLASK_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    mail.send(msg)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).filter_by(id=user_id).first()


@main.route('/index')
@main.route('/')
def index():
    results = Blog.query.order_by(Blog.id.desc())
    blogs = [dict(id=result.id,
                  title=result.title,
                  body=result.body,
                  img=result.img,
                  gmt_create=date_transform(result.gmt_create)
                  ) for result in results]
    recommended_blogs_result = db.session.query(Blog).filter(Blog.is_recommend == 1).order_by(Blog.id.desc())
    recommended_blogs = [dict(id=result.id,
                              title=result.title) for result in recommended_blogs_result]
    return render_template('index.html', blogs=blogs, recommended_blogs=recommended_blogs)


@main.route('/single/<blog_id>')
def single(blog_id):
    comment_form = CommentForm()
    result = db.session.query(Blog).filter_by(id=blog_id).first()
    blog = dict(id=result.id,
                title=result.title,
                body=result.body,
                img=result.img,
                gmt_create=date_transform(result.gmt_create))
    comment_results = db.session.query(Comment).filter(Comment.comment_blog_id == blog_id, Comment.reply_id == None).all()
    comments = [dict(id=result.id,
                     user_name=db.session.query(User).filter_by(id=result.user_id).first().user_name,
                     gmt_create=date_transform(result.gmt_create),
                     comment_content=result.comment_content) for result in comment_results]
    recommended_blogs_result = db.session.query(Blog).filter(Blog.is_recommend == 1).order_by(Blog.id.desc())
    recommended_blogs = [dict(id=result.id,
                              title=result.title) for result in recommended_blogs_result]
    return render_template('single.html',
                           blog=blog,
                           recommended_blogs=recommended_blogs,
                           comment_form=comment_form,
                           comments=comments)


@main.route('/single/<blog_id>/comment', methods=['POST'])
def comment(blog_id):
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        comment = Comment(user_id=current_user.id,
                          gmt_create=date.today(),
                          comment_content=comment_form.comment.data,
                          comment_blog_id=blog_id)
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for('main.single', blog_id=blog_id))


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


@main.route('/administration', methods=['GET', 'POST'])
@login_required
def administration():
    if current_user.is_authenticated:
        results = Blog.query.order_by(Blog.id.desc())
        blogs = [dict(id=result.id,
                      title=result.title,
                      body=result.body,
                      img=result.img,
                      is_recommend=result.is_recommend) for result in results]

        return render_template('administration.html', blogs=blogs)
    return redirect(url_for('auth.login'))


@main.route('/administration/delete/<blog_id>', methods=['POST'])
@login_required
def delete(blog_id):
    blog = Blog.query.filter(Blog.id == blog_id).first()
    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for('main.administration'))


@main.route('/administration/recommend/<blog_id>', methods=['POST'])
@login_required
def recommend(blog_id):
    Blog.query.filter(Blog.id == blog_id).update({Blog.is_recommend: 1})
    db.session.commit()
    return redirect(url_for('main.administration'))


@main.route('/administration/derecommend/<blog_id>', methods=['POST'])
@login_required
def derecommend(blog_id):
    Blog.query.filter(Blog.id == blog_id).update({Blog.is_recommend: 0})
    db.session.commit()
    return redirect(url_for('main.administration'))


@main.route('/release', methods=['GET', 'POST'])
@login_required
def release():
    form = ReleaseForm()
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        file_url = photos.url(filename)
        blog = Blog(title=form.title.data, body=form.body.data, img=file_url, gmt_create=date.today().isoformat())
        db.session.add(blog)
        db.session.commit()
        flash("release succeed")
        return redirect(url_for('main.administration'))
    return render_template('release.html', form=form)


@main.route('/about')
def about():
    return render_template('about.html')


@main.route('/_uploads/photos/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOADED_PHOTOS_DEST, filename)


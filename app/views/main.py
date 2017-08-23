from .. import db, photos
from flask import render_template, redirect, flash, url_for, send_from_directory, Blueprint, current_app, request, Flask, abort
from ..models import Blog, User, Comment, Ip, Permission, Role
from ..forms import ReleaseForm, CommentForm, EditUserProfileForm, EditUserProfileAdminForm
from flask_login import login_required, current_user
from datetime import date
from config import Config
from functools import wraps
from sqlalchemy.sql.expression import distinct

main = Blueprint('main', __name__)


def permission_required(permission):
    def permission_required_closure(func):
        @wraps(func)  # 神来之笔
        def wrappers(*args, **kwargs):
            if not current_user.can(permission):
                abort(444)
            else:
                return func(*args, **kwargs)  # 为什么要return，直接func不行么？？难道和wraps的用法有关系？的确有关系
        return wrappers
    return permission_required_closure


@main.after_request
def pv_statistics(response):
    ip = Ip(ip=request.remote_addr)
    db.session.add(ip)
    db.session.commit()
    return response


@main.route('/index')
@main.route('/')
def index():
    results = Blog.query.order_by(Blog.id.desc())
    blogs = [dict(id=result.id,
                  title=result.title,
                  body=result.body,
                  img=result.img,
                  gmt_create=result.format_date
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
                gmt_create=result.format_date)
    comment_results = db.session.query(Comment).filter(Comment.comment_blog_id == blog_id,
                                                       Comment.reply_id == None).all()
    comments = [dict(id=result.id,
                     user_name=db.session.query(User).filter_by(id=result.user_id).first().user_name,
                     user_id=result.user_id,
                     gmt_create=result.format_date,
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
@login_required
@permission_required(Permission.COMMENT)
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


@main.route('/administration', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADMINISTER)
def administration():
    if current_user.is_authenticated:
        results = Blog.query.order_by(Blog.id.desc())
        blogs = [dict(id=result.id,
                      title=result.title,
                      body=result.body,
                      img=result.img,
                      is_recommend=result.is_recommend) for result in results]
        pv = db.session.query(Ip.ip).count()
        return render_template('administration.html', blogs=blogs, pv=pv)
    return redirect(url_for('auth.login'))


@main.route('/administration/delete/<blog_id>', methods=['POST'])
@login_required
@permission_required(Permission.DELETE)
def delete(blog_id):
    blog = Blog.query.filter(Blog.id == blog_id).first()
    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for('main.administration'))


@main.route('/administration/recommend/<blog_id>', methods=['POST'])
@login_required
@permission_required(Permission.RECOMMEND)
def recommend(blog_id):
    Blog.query.filter(Blog.id == blog_id).update({Blog.is_recommend: 1})
    db.session.commit()
    return redirect(url_for('main.administration'))


@main.route('/administration/derecommend/<blog_id>', methods=['POST'])
@login_required
@permission_required(Permission.RECOMMEND)
def derecommend(blog_id):
    Blog.query.filter(Blog.id == blog_id).update({Blog.is_recommend: 0})
    db.session.commit()
    return redirect(url_for('main.administration'))


@main.route('/release', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADMINISTER)
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


@main.route('/user_profile/<user_id>')
def user_profile(user_id):
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        abort(444)
    return render_template('user_profile.html', user=user)


@main.route('/user_profile/<user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_profile_edit(user_id):
    if current_user.id != int(user_id):  # 这里注意一下，传进来的东西全部是字符串，如果未加申明的话，所以要用int进行类型转换
        abort(444)
    form = EditUserProfileForm()
    if form.validate_on_submit():
        current_user.real_name = form.real_name.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('your profile has been updated')
        return redirect(url_for('main.user_profile_edit', user_id=user_id))

    # 应该通过form.real_name.data去对填充form域的默认值，而非通过placeholder属性去改，后者会导致提交的时候出现空数据
    form.real_name.data = current_user.real_name
    form.about_me.data = current_user.about_me

    return render_template('user_profile_edit.html', form=form)


@main.route('/user_profile/<user_id>/edit_admin', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.SUPERADMIN)
def user_profile_edit_admin(user_id):
    user = db.session.query(User).filter_by(id=user_id).first()
    if user:
        form = EditUserProfileAdminForm(user)
        if form.validate_on_submit():
            user.email = form.email.data
            user.user_name = form.user_name.data
            user.confirmed = form.confirmed.data

            # 这里的get需要的是一个primary key的值，role.data返回的是一个int, 同时应该也会修改user.role_id
            user.role = db.session.query(Role).get(form.role.data)

            user.real_name = form.real_name.data
            user.about_me = form.about_me.data
            db.session.commit()
            flash('profile has been updated')
            return redirect(url_for('main.user_profile_edit_admin', user_id=user_id))
        form.email.data = user.email
        form.user_name.data = user.user_name
        form.confirmed.data = user.confirmed
        form.role.data = user.role_id
        form.real_name.data = user.real_name
        form.about_me.data = user.about_me

        return render_template('user_profile_edit_admin.html', form=form, user=user)


@main.route('/_uploads/photos/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOADED_PHOTOS_DEST, filename)

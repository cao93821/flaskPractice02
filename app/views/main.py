from datetime import date
from functools import wraps
import logging

from .. import db, photos
from flask import render_template, redirect, flash, url_for, send_from_directory, Blueprint, request, abort, make_response
from ..models import Blog, User, Comment, Ip, Permission, Role
from ..forms import ReleaseForm, CommentForm, EditUserProfileForm, EditUserProfileAdminForm
from flask_login import login_required, current_user
from config import Config


main = Blueprint('main', __name__)


# 初始化一个logger
logger = logging.Logger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('name: %(name)s\nlevel: %(levelname)s\n%(message)s\n'))
logger.addHandler(handler)


def permission_required(permission):
    """权限需求装饰器，如果权限不够，返回一个405错误码"""
    def permission_required_closure(func):
        @wraps(func)
        def wrappers(*args, **kwargs):
            if not current_user.can(permission):
                abort(405)
            else:
                return func(*args, **kwargs)
        return wrappers
    return permission_required_closure


@main.after_request
def pv_statistics(response):
    """访问计数，不过dispatch_request层级是否发生异常，都会在full_dispatch_request层级进行调用"""
    ip = Ip(ip=request.remote_addr)
    db.session.add(ip)
    db.session.commit()

    return response


@main.route('/show_followed')
@login_required
def show_followed():
    """仅显示关注的人的blog，使用cookie种植实现"""
    response = make_response(redirect(url_for('.index')))
    response.set_cookie('show_followed', '1', max_age=30*24*60*60)

    return response


@main.route('/index')
@main.route('/')
def index():
    """主页"""
    is_show_followed = False
    if current_user.is_authenticated:
        is_show_followed = bool(request.cookies.get('show_followed', ''))
    # 如果是已登录用户，则只返回他关注的人的Blog
    if is_show_followed:
        blog_query = current_user.followed_blogs
    else:
        blog_query = Blog.query
    # 通过查询参数获取请求的page页数
    page = request.args.get('page', 1, type=int)
    # 获取分页对象pagination
    pagination = blog_query.order_by(Blog.gmt_create.desc()).paginate(
        page,
        per_page=20,
        error_out=False
    )
    blogs = pagination.items
    recommended_blogs = db.session.query(Blog).filter(Blog.is_recommend == 1).order_by(Blog.id.desc())

    return render_template('index.html', blogs=blogs, recommended_blogs=recommended_blogs, pagination=pagination)


@main.route('/single/<blog_id>')
def single(blog_id):
    """blog详情页"""
    comment_form = CommentForm()
    blog = db.session.query(Blog).filter_by(id=blog_id).first()

    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(Comment).filter(
        Comment.comment_blog_id == blog_id,
        Comment.reply_id == None
    ).order_by(Comment.gmt_create.desc()).paginate(
        page,
        per_page=5,
        error_out=False
    )

    comments = pagination.items
    recommended_blogs = db.session.query(Blog).filter(Blog.is_recommend == 1).order_by(Blog.id.desc())

    return render_template(
        'single.html',
        blog=blog,
        recommended_blogs=recommended_blogs,
        comment_form=comment_form,
        pagination=pagination,
        comments=comments
    )


@main.route('/single/<blog_id>/comment', methods=['POST'])
@login_required
@permission_required(Permission.COMMENT)
def comment(blog_id):
    """发评论"""
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
    """管理"""
    if current_user.is_authenticated:
        blogs = Blog.query.order_by(Blog.id.desc())
        pv = db.session.query(Ip.ip).count()
        return render_template('administration.html', blogs=blogs, pv=pv)

    return redirect(url_for('auth.login'))


@main.route('/administration/delete/<blog_id>', methods=['POST'])
@login_required
@permission_required(Permission.DELETE)
def delete(blog_id):
    """删除blog"""
    blog = Blog.query.filter(Blog.id == blog_id).first()
    db.session.delete(blog)
    db.session.commit()

    return redirect(url_for('main.administration'))


@main.route('/administration/recommend/<blog_id>', methods=['POST'])
@login_required
@permission_required(Permission.RECOMMEND)
def recommend(blog_id):
    """推荐blog"""
    Blog.query.filter(Blog.id == blog_id).update({Blog.is_recommend: 1})
    db.session.commit()

    return redirect(url_for('main.administration'))


@main.route('/administration/derecommend/<blog_id>', methods=['POST'])
@login_required
@permission_required(Permission.RECOMMEND)
def derecommend(blog_id):
    """取消推荐blog"""
    Blog.query.filter(Blog.id == blog_id).update({Blog.is_recommend: 0})
    db.session.commit()
    return redirect(url_for('main.administration'))


@main.route('/release', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADMINISTER)
def release():
    """发布blog"""
    form = ReleaseForm()
    if form.validate_on_submit():
        logger.debug('file data: type {}, {}'.format(type(form.photo.data), form.photo.data))
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
    """about页面"""
    return render_template('about.html')


@main.route('/user_profile/<user_id>')
def user_profile(user_id):
    """用户个人信息页面"""
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        abort(405)
    return render_template('user_profile.html', user=user)


@main.route('/user_profile/<user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_profile_edit(user_id):
    """用户个人信息编辑"""
    if current_user.id != int(user_id):  # 这里注意一下，传进来的东西全部是字符串，如果未加申明的话，所以要用int进行类型转换
        abort(405)
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
    """超级用户编辑用户个人信息"""
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


@main.route('/follow/<int:user_id>')
@login_required
def follow(user_id):
    """关注"""
    follow_user = User.query.filter_by(id=user_id).first()
    if follow_user:
        current_user.follow(follow_user)
    return redirect(url_for('.user_profile', user_id=user_id))


@main.route('/unfollow/<int:user_id>')
@login_required
def unfollow(user_id):
    """取消关注"""
    follow_user = User.query.filter_by(id=user_id).first()
    if follow_user:
        current_user.unfollow(follow_user)
    return redirect(url_for('.user_profile', user_id=user_id))


@main.route('/_uploads/photos/<filename>')
def uploaded_file(filename):
    """获取上传的照片"""
    return send_from_directory(Config.UPLOADED_PHOTOS_DEST, filename)

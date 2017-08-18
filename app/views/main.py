from .. import db, photos
from flask import render_template, redirect, flash, url_for, send_from_directory, Blueprint, current_app, request, Flask, abort
from ..models import Blog, User, Comment, Ip, Permission
from ..forms import ReleaseForm, CommentForm
from flask_login import login_required, current_user
from datetime import date
from config import Config
from sqlalchemy.sql.expression import distinct

main = Blueprint('main', __name__)


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
    comment_results = db.session.query(Comment).filter(Comment.comment_blog_id == blog_id, Comment.reply_id == None).all()
    comments = [dict(id=result.id,
                     user_name=db.session.query(User).filter_by(id=result.user_id).first().user_name,
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
def comment(blog_id):
    if not current_user.can(Permission.COMMENT):
        abort(404)
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
def administration():
    if not current_user.can(Permission.ADMINISTER):
        abort(404)
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
def delete(blog_id):
    if not current_user.can(Permission.DELETE):
        abort(404)
    blog = Blog.query.filter(Blog.id == blog_id).first()
    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for('main.administration'))


@main.route('/administration/recommend/<blog_id>', methods=['POST'])
@login_required
def recommend(blog_id):
    if not current_user.can(Permission.RECOMMEND):
        abort(404)
    Blog.query.filter(Blog.id == blog_id).update({Blog.is_recommend: 1})
    db.session.commit()
    return redirect(url_for('main.administration'))


@main.route('/administration/derecommend/<blog_id>', methods=['POST'])
@login_required
def derecommend(blog_id):
    if not current_user.can(Permission.RECOMMEND):
        abort(404)
    Blog.query.filter(Blog.id == blog_id).update({Blog.is_recommend: 0})
    db.session.commit()
    return redirect(url_for('main.administration'))


@main.route('/release', methods=['GET', 'POST'])
@login_required
def release():
    if not current_user.can(Permission.ADMINISTER):
        abort(404)
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

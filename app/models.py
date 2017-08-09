from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer
from flask import current_app


class Blog(db.Model):
    __tablename__ = 'blog'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40))
    body = db.Column(db.Text)
    img = db.Column(db.String(20))
    gmt_create = db.Column(db.Date)
    is_recommend = db.Column(db.Integer)
    author_id = db.Column(db.Integer)
    comment = db.relationship('Comment', backref='comment_blog')

    def __repr__(self):
        return "<Blog> %r" % self.title


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    gmt_create = db.Column(db.Date)
    reply_id = db.Column(db.Integer)
    comment_content = db.Column(db.Text)
    comment_blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))

    def __repr__(self):
        return "<Comment> {}".format(self.id)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40))
    user_name = db.Column(db.String(40))
    hash_password = db.Column(db.Text)
    role = db.Column(db.String(40))
    comment = db.relationship('Comment', backref='author')
    confirmed = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        raise AttributeError('Password is not readable')

    @password.setter
    def password(self, password):
        self.hash_password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.hash_password, password)

    def generate_confirmation_token(self, expiration=3600):
        signature = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        return signature.dumps({'confirm.txt': self.id})

    def confirm(self, token):
        signature = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = signature.loads(token)
        except:
            return False
        if data.get('confirm.txt') != self.id:
            return False
        self.confirmed = True
        db.session.commit()
        return True

    def __repr__(self):
        return "<User> %r" % self.user_name

# db.create_all()



from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer
from flask import current_app


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

    @property
    def format_date(self):
        return date_transform(self.gmt_create)

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

    @property
    def format_date(self):
        return date_transform(self.gmt_create)

    def __repr__(self):
        return "<Comment> {}".format(self.id)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40))
    user_name = db.Column(db.String(40))
    hash_password = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    comment = db.relationship('Comment', backref='author')
    confirmed = db.Column(db.Boolean, default=False)

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administer(self):
        return self.can(Permission.ADMINISTER)

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

    @staticmethod
    def password_reset_token_confirm(token, password):
        signature = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = signature.loads(token)
        except:
            return False
        user = db.session.query(User).filter_by(id=data.get('confirm.txt'))
        user.password = password
        db.session.commit()
        return True

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


class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    ADMINISTER = 0x08


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role')

    @staticmethod
    def insert_role():
        roles = {
            'User': Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES,
            'Administer': Permission.ADMINISTER
        }
        for r in roles:
            role = db.session.query(Role).filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r]
            db.session.add(role)
            db.session.commit()


class Ip(db.Model):
    __tablename__ = 'ip'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(20))


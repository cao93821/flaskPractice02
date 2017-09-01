from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer
from flask import current_app, url_for
from datetime import datetime
import bleach
from markdown import markdown


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
    body_html = db.Column(db.Text)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags,
            strip=True
        ))

    @property
    def format_date(self):
        return date_transform(self.gmt_create)

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            user = User.query.offset(randint(0, user_count - 1)).first()
            blog = Blog(title=forgery_py.lorem_ipsum.word(),
                        body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                        img=url_for('static', filename='img/small_pig.jpg'),
                        gmt_create=forgery_py.date.date(True),
                        author_id=user.id)
            db.session.add(blog)
            db.session.commit()

    def __repr__(self):
        return "<Blog> %r" % self.title

db.event.listen(Blog.body, 'set', Blog.on_changed_body)


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

    @staticmethod
    def generate_fake(count=5000):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = db.session.query(User).count()
        blog_count = db.session.query(Blog).count()
        for i in range(count):
            user = db.session.query(User).offset(randint(0, user_count - 1)).first()
            blog = db.session.query(Blog).offset(randint(0, blog_count - 1)).first()
            comment = Comment(author=user,
                              gmt_create=forgery_py.date.date(True),
                              comment_content=forgery_py.lorem_ipsum.sentence(),
                              comment_blog=blog)
            db.session.add(comment)
            db.session.commit()

    def __repr__(self):
        return "<Comment> {}".format(self.id)


class Follow(db.Model):
    __tablename__ = 'follow'
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    gmt_create = db.Column(db.DateTime(), default=datetime.now)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40))
    user_name = db.Column(db.String(40))
    hash_password = db.Column(db.Text)
    role_id = db.Column(
        db.Integer,
        db.ForeignKey('role.id'),
        default=lambda: db.session.query(Role).filter_by(name='User').first().id
    )
    comment = db.relationship('Comment', backref='author')
    confirmed = db.Column(db.Boolean, default=False)
    real_name = db.Column(db.String(20))
    about_me = db.Column(db.Text)
    gmt_create = db.Column(db.DateTime(), default=datetime.now)
    # 这里对default参数传入了一个函数对象，使之能在User实例化的时候动态变化
    last_online_time = db.Column(db.DateTime(), default=datetime.now)
    # 对于backref使用lazy='joined'模式，因为一个Follow只会有一个对应的follower和followed，所以不需要返回一个Query
    # 对于一个人的followed，在对应的Follow当中，反向来说他就是那个follower
    # 设置cascade='all, delete-orphan'可以使得在删除对象的同时将其此关联的对应的另一个对象一同删除，实验了一下果然可以
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    follower = db.relationship('Follow',
                               foreign_keys=[Follow.followed_id],
                               backref=db.backref('followed', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 不能直接使用self.follow()，会导致无法建立follow，因为user还没有建立获取不到外键的值
        self.followed.append(Follow(followed=self))

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower_id=self.id, followed_id=user.id)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self, user):
        follow = db.session.query(Follow).filter_by(follower_id=self.id, followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def is_following(self, user):
        return db.session.query(Follow).filter_by(follower_id=self.id, followed_id=user.id).first() is not None

    @staticmethod
    def follow_self():
        users = db.session.query(User).all()
        for user in users:
            user.follow(user)
            db.session.commit()

    @property
    def followed_blogs(self):
        """

        :return: 一个已经查询了所有关注的用户的Blog的Query
        """
        # 为增加可重用性，返回的是一个Query而非一个包含Blog对象的list
        return Blog.query.join(Follow, Follow.followed_id==Blog.author_id).filter(Follow.follower_id==self.id)

    def update_last_online_time(self):
        self.last_online_time = datetime.now()
        db.session.commit()

    def can(self, permissions):
        return self.role is not None and (
            (self.role.permissions & permissions) == permissions or self.role.name == 'SuperAdminister')

    @property
    def password(self):
        raise AttributeError('Password is not readable')

    @password.setter
    def password(self, password):
        self.hash_password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.hash_password, password)

    def generate_confirmation_token(self, expiration=3600, email=None):
        signature = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        if email:
            return signature.dumps({'confirm.txt': self.id, 'new_email': email})
        else:
            return signature.dumps({'confirm.txt': self.id})

    @staticmethod
    def password_reset_token_confirm(token, password):
        signature = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = signature.loads(token)
        except:
            return False
        user = db.session.query(User).filter_by(id=data.get('confirm.txt')).first()
        user.password = password
        db.session.commit()
        return True

    def email_reset_token_confirm(self, token):
        signature = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = signature.loads(token)
        except:
            return False
        if data.get('confirm.txt') != self.id:
            return False
        return True

    def new_email_token_confirm(self, token):
        signature = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = signature.loads(token)
        except:
            return False
        if data.get('confirm.txt') != self.id:
            return False
        new_email = data.get('new_email')
        self.email = new_email
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

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            user = User(email=forgery_py.internet.email_address(),
                        user_name=forgery_py.internet.user_name(),
                        password=forgery_py.lorem_ipsum.word(),
                        confirmed=True,
                        real_name=forgery_py.name.full_name(),
                        about_me=forgery_py.lorem_ipsum.sentence(),
                        gmt_create=forgery_py.date.date(True),
                        role=db.session.query(Role).filter_by(name='User').first())
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return "<User> %r" % self.user_name


class Permission:
    COMMENT = 0b00000001
    ADMINISTER = 0b00000010
    DELETE = 0b00000100
    RECOMMEND = 0b00001000
    SUPERADMIN = 0b10000000


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role')

    @staticmethod
    def insert_role():
        roles = {
            'User': Permission.COMMENT,
            'Administer': Permission.COMMENT | Permission.ADMINISTER | Permission.DELETE | Permission.RECOMMEND,
            'SuperAdminister': Permission.SUPERADMIN
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


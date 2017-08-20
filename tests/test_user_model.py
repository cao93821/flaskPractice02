import unittest
from app.models import User, Permission, Role
from app import create_app, db


def user_data_generate():
    u1 = User(user_name='u1', password='cat', role_id=1)
    u2 = User(user_name='u2', password='cat', role_id=2)
    u3 = User(user_name='u3', password='cat', role_id=3)
    db.session.add(u1)
    db.session.add(u2)
    db.session.add(u3)
    db.session.commit()


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('test')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        Role.insert_role()
        user_data_generate()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u1 = db.session.query(User).filter_by(user_name='u1').first()
        self.assertTrue(u1.hash_password is not None)

    def test_no_password_getter(self):
        u1 = db.session.query(User).filter_by(user_name='u1').first()
        with self.assertRaises(AttributeError):
            u1.password

    def test_password_verification(self):
        u1 = db.session.query(User).filter_by(user_name='u1').first()
        self.assertTrue(u1.verify_password('cat'))
        self.assertFalse(u1.verify_password('dog'))

    def test_password_salts_are_random(self):
        u1 = db.session.query(User).filter_by(user_name='u1').first()
        u2 = db.session.query(User).filter_by(user_name='u2').first()
        self.assertTrue(u1.hash_password != u2.hash_password)

    def test_user_can(self):
        u = db.session.query(User).filter_by(role_id=2).first()
        u2 = db.session.query(User).filter_by(role_id=1).first()
        u3 = db.session.query(User).filter_by(role_id=3).first()
        self.assertTrue(u.can(Permission.ADMINISTER))
        self.assertTrue(u.can(Permission.RECOMMEND))
        self.assertFalse(u.can(Permission.SUPERADMIN))
        self.assertTrue(u2.can(Permission.COMMENT))
        self.assertFalse(u2.can(Permission.SUPERADMIN))
        self.assertTrue(u3.can(Permission.SUPERADMIN))
        self.assertTrue(u3.can(Permission.DELETE))

    def test_generate_token(self):
        u = db.session.query(User).first()
        token1 = u.generate_confirmation_token()
        token2 = u.generate_confirmation_token(email='cl93821@163.com')
        self.assertTrue(token1 is not None)
        self.assertTrue(token2 is not None)

    def test_password_reset_token_confirm(self):
        u = db.session.query(User).first()
        token = u.generate_confirmation_token()
        User.password_reset_token_confirm(token, '123456')
        new_u = db.session.query(User).filter_by(id=u.id).first()
        self.assertFalse(new_u.verify_password('cat'))
        self.assertTrue(new_u.verify_password('123456'))

    def test_email_reset_token_confirm(self):
        u = db.session.query(User).first()
        token = u.generate_confirmation_token()
        self.assertTrue(u.email_reset_token_confirm(token))

    def test_new_email_token_confirm(self):
        u = db.session.query(User).first()
        token = u.generate_confirmation_token(email='cl93821@163.com')
        u.new_email_token_confirm(token)
        new_email = db.session.query(User).first().email
        self.assertTrue(new_email == 'cl93821@163.com')

    def test_new_user_confirm(self):
        u = db.session.query(User).first()
        token = u.generate_confirmation_token()
        u.confirm(token)
        self.assertTrue(db.session.query(User).first().confirmed)

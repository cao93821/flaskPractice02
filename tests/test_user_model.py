import unittest
from app.models import User, Permission, Role
from app import create_app, db


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('test')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        Role.insert_role()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.hash_password is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.hash_password != u2.hash_password)

    def test_user_can(self):
        u = User(role_id=2)
        u2 = User(role_id=1)
        u3 = User(role_id=3)
        db.session.add(u)
        db.session.add(u2)
        db.session.add(u3)
        db.session.commit()
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
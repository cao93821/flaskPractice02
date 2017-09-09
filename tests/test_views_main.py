import unittest

from flask import url_for

from app import create_app, db
from app.models import Role


class ViewsMainTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('test')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_role()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_index(self):
        response = self.client.get(url_for('main.index'))
        self.assertTrue('Welcome' in response.get_data(as_text=True))
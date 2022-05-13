import os
import unittest

from config import basedir
from repository import app
from repository.models import User

class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.sqlite')

        self.app = app.test_client()
    
    def tearDown(self):
        print("Testing")

    def test_correct_login(self):
        tester = app.test_client(self)
        response = tester.post(
            '/users/login',
            data = dict(email="PKPRAVEENKUMAR0128@GMAIL.COM", password="praveen123"),
            follow_redirects=True
        )
        self.assertIn(b'Sucessfully logged in', response.data)

if __name__ == '__main__':
    unittest.main()
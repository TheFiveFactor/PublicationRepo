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
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI') or os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.sqlite')

        self.app = app.test_client()
    
    def tearDown(self):
        print()

    def test_correct_login(self):
        tester = app.test_client(self)
        response = tester.post(
            '/users/login',
            data = dict(email="PKPRAVEENKUMAR0128@GMAIL.COM", password="praveen123"),
            follow_redirects=True
        )
        self.assertIn(b'Sucessfully logged in', response.data)
    
    def test_change_password(self):
        # print('test_change_password')
        tester = app.test_client(self)
        response = tester.post(
            '/users/login',
            data = dict(email="balanishabalasubramaniam@gmail.com", password="bala@123"),
            follow_redirects=True
        )
        # self.assertIn(b'Sucessfully logged in', response.data)

        response1 = tester.post(
            '/users/change-password',
            data=dict(old_password='bala@123', new_password='bala@1234'),
            follow_redirects=True
        )
        # self.assertIn(b'The Five Factor', response1.data)
        self.assertIn(b'Password has been Updated!', response1.data)
        

if __name__ == '__main__':
    unittest.main()
from repository import db, login, app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import url_for


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return "<Role '{}'>".format(self.name)


class Institution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    student_email_server = db.Column(db.String(128), unique=True, index=True, nullable=False)
    users = db.relationship('User', backref='institution', lazy=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return "<Institution: '{}', StudentEmailServer: '{}'>".format(self.name, self.student_email_server)

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(64), index=True)
    lname = db.Column(db.String(64), index=True)
    profile_image = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), index=True, unique=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institution.id'), nullable=False)
    password_hash = db.Column(db.String(128))
    by_email = db.Column(db.Boolean, default=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def get_reset_token(self, expires_sec=1200):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def get_profile_image_url(self, img_size=64):
        if self.profile_image:
            return url_for('static', filename='profile_pics/' + self.profile_image)
        else:
            bg_and_color_list = [('0D8ABC', 'fff'), ('a0a0a0', 'ff0'), ('ff0000', 'fff'), ('40e0d0', '000')]
            bg_lis_len = len(bg_and_color_list)
            user_bg = bg_and_color_list[self.id % bg_lis_len]
            return f'https://ui-avatars.com/api/?name={self.fname}+{self.lname}' + f'&background={user_bg[0]}&color={user_bg[1]}&size={img_size}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "<User id: '{}', Name: '{}'>".format(self.id, self.fname + " " + self.lname)

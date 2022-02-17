import os
from flask import Flask, redirect, url_for
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'You need to be logged in to view this page'
login.login_message_category = 'info'

from repository import routes, models

# Admin
"""
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))
"""

# admin = Admin(app, name='Faculty Publication Repo Admin', template_mode='bootstrap3', index_view=AdminIndexView)
admin = Admin(app, name='Faculty Publication Repo Admin', template_mode='bootstrap3')
admin.add_view(ModelView(models.Role, db.session))
admin.add_view(ModelView(models.Institution, db.session))
admin.add_view(ModelView(models.User, db.session))

class AnalyticsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('analytics_index.html')

admin.add_view(AnalyticsView(name='Analytics', endpoint='analytics'))

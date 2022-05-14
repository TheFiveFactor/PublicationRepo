import os
from flask import Flask, flash, redirect, url_for, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose
from flask_admin.contrib import sqla as flask_admin_sqla
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'You need to be logged in to view this page'
login.login_message_category = 'info'

# GitHub Configuration
oauth = OAuth(app)
github = oauth.register(
    name='github',
    client_id=os.environ.get("CLIENT_ID"),
    client_secret=os.environ.get("SECRET_ID"),
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)
# facebook = oauth.register(
#     name='facebook',
#     client_id=os.environ.get('FACEBOOK_CLIENT_ID'),
#     client_secret=os.environ.get('FACEBOOK_CLIENT_SECRET'),
#     access_token_url='https://graph.facebook.com/oauth/access_token',
#     access_token_params=None,
#     authorize_url='https://www.facebook.com/dialog/oauth',
#     authorize_params=None,
#     api_base_url='https://graph.facebook.com/',
#     client_kwargs={'scope': 'email'},
# )

from repository import routes, models

# Admin
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        # print(current_user.is_authenticated)
        # return False
        flash("You need to login", "success")
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        # return redirect(url_for('login'))
        # redirect to login page if user doesn't have access
        print("inaccess")
        return redirect(url_for('login', next=request.url))

    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        return super(MyAdminIndexView, self).index()


class DefaultModelView(flask_admin_sqla.ModelView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def is_accessible(self):
        # print(current_user.is_authenticated)
        # print(current_user.is_authenticated, current_user.role.name, current_user.role.name == "admin")
        is_acc = current_user.is_authenticated and current_user.role.name == "admin"
        if not is_acc:
            flash("You need to login And you chould be admin", "success")
        return is_acc

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        print("inaccess")
        return redirect(url_for('login', next=request.url))


# admin = Admin(app, name='Faculty Publication Repo Admin', template_mode='bootstrap3', index_view=AdminIndexView())
admin = Admin(app, name='Faculty Publication Repo Admin', template_mode='bootstrap3')
admin.add_view(DefaultModelView(models.Role, db.session))
admin.add_view(DefaultModelView(models.Institution, db.session))
admin.add_view(DefaultModelView(models.User, db.session))
admin.add_view(DefaultModelView(models.Faculty, db.session))
admin.add_view(DefaultModelView(models.Department, db.session))
admin.add_view(DefaultModelView(models.DepartmentAreas, db.session))
admin.add_view(DefaultModelView(models.PaperType, db.session))
admin.add_view(DefaultModelView(models.PublishPaper, db.session))

class AnalyticsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('analytics_index.html')

admin.add_view(AnalyticsView(name='Analytics', endpoint='analytics'))

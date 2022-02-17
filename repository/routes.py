import secrets, os
import time
from PIL import Image
from repository import app, db
from flask import url_for, render_template, redirect, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from repository.models import Institution, Role, User
from repository.forms import LoginForm, RegistrationForm, EditProfileForm, ChangePasswordForm, \
    RequestPasswordResetForm, ResetPasswordForm

import smtplib
from email.message import Message

# Utils
def save_profile_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (170, 170)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def send_reset_email(user):
    expire_ex = 1200
    token = user.get_reset_token(expire_ex)

    msg = Message()
    msg['Subject'] = "Password Reset Request"
    msg['From'] = app.config['MAIL_USERNAME']
    msg['To'] = user.email
    msg.add_header('Content-Type','text/html')

    message = """To reset your password, click the following link:
        {}<br> This is valid for <b>{}</b> mins.<br>
        If you didn't make the request then simply ignore this mail
        """.format(url_for('reset_token', token=token, _external=True), expire_ex//60)
    s = smtplib.SMTP("smtp.gmail.com", 587)
    msg.set_payload(message)
    s.starttls()
    s.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
    s.quit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/home', methods=['GET', 'POST'])
# @login_required
# def home():
#     return render_template('home.html', title='Sign In')

@app.route('/users/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm(request.form)
    reg_form = RegistrationForm()
    if request.method=="POST" and form.validate_on_submit():
        print("arrive")
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form, reg_form=reg_form)

@app.route('/users/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    login_form = LoginForm()
    form = RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        user = User(fname=form.fname.data, lname=form.lname.data, email=form.email.data,
            by_email=True, institution_id=form.institution.data)
        user.set_password(form.password.data)
        role = Role.query.filter_by(name=form.role.data).first()
        user.role_id = role.id
        institution = Institution.query.get(form.institution.data)

        if role.name == 'student':
            form_email = form.email.data.split('@')[1]
            if institution.student_email_server != form_email:
                flash('University email does not match', 'danger')
                return render_template('register.html', title='Register', form=form, login_form=login_form)

        if 'picture' in request.files and request.files['picture'].filename != '':
            picture_file = save_profile_picture(request.files['picture'])
            user.profile_image = picture_file
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, login_form=login_form)


@app.route('/users/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.by_email != True:
        return redirect(url_for('index'))
    form = EditProfileForm(request.form)
    if form.validate_on_submit():
        current_user.fname = form.fname.data
        current_user.lname = form.lname.data
        current_user.email = form.email.data

        role = Role.query.filter_by(name=form.role.data).first()
        current_user.role_id = role.id

        if 'picture' in request.files and request.files['picture'].filename != '':
            picture_file = save_profile_picture(request.files['picture'])
            current_user.profile_image = picture_file

        db.session.commit()
        flash('Your account has been Updated!', 'success')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.fname.data = current_user.fname
        form.lname.data = current_user.lname
        form.email.data = current_user.email
        form.role.data = current_user.role.name
    image_file = None
    if current_user.profile_image:
        image_file = url_for('static', filename='profile_pics/' + current_user.profile_image)

    return render_template('edit_profile.html', title='Edit Profile', form=form, image_file=image_file)

@app.route('/users/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm(request.form)
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash('Invalid Old Password!', 'danger')
            return redirect(url_for('change_password'))
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password has been Updated!', 'success')
            return redirect(url_for('index'))
    return render_template('change_password.html', title='Change Password', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/users/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token ', 'warning')
        return redirect(url_for('forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been changed! You can login now", 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@app.route('/users/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        # time.sleep(5)
        flash('An email has been sent with instruction to reset your password', 'info')
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html', title='Reset Password', form=form)

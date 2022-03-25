import secrets, os
import time
from turtle import title
from PIL import Image
from repository import app, db, github
from flask import url_for, render_template, redirect, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from repository.models import Faculty, Institution, PaperType, PublishPaper, Role, User, Department
from repository.forms import LoginForm, RegistrationForm, EditProfileForm, ChangePasswordForm, \
    RequestPasswordResetForm, ResetPasswordForm, PublishPaperForm, EditFacultyProfileForm

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

def save_publish_paper_pdf(form_paper):
    random_hex = secrets.token_hex(32)
    f_name, f_ext = os.path.splitext(form_paper.filename)
    new_fname = "_".join(f_name.split(" "))
    paper_fn = random_hex + "-" + new_fname + f_ext
    paper_path = os.path.join(app.root_path, 'static/publish_papers', paper_fn)
    form_paper.save(paper_path)
    return paper_fn

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

# GitHub Login
@app.route('/users/github-login')
def github_login():
    redirect_url = url_for('github_authorize', _external=True)
    return github.authorize_redirect(redirect_url)

@app.route('/users/github-login/authorized')
def github_authorize():
    token = github.authorize_access_token()
    resp = github.get('user', token=token)

    resp = github.get('user/emails', token=token)
    profile = resp.json()
    # print(profile, token)
    gh_emails = [ gh_email['email'] for gh_email in profile]
    for gh_email in gh_emails:
        user = User.query.filter_by(email=gh_email).first()
        if user is not None:
            login_user(user, remember=True)
            flash("Successfully logged in", "success")
            return redirect('/')
    flash('GitHub email not found in database! Try with Email', "error")
    return redirect(url_for('login'))

@app.route('/users/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm(request.form)
    reg_form = RegistrationForm()
    if request.method=="POST" and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember.data)
        flash('Sucessfully logged in', 'success')
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


# Publish paper
@app.route('/publish-paper', methods=['GET', 'POST'])
@login_required
def publish_paper():
    if current_user.role.name == 'student':
        flash('Students cannot publish papers', 'warning')
        return redirect(url_for('index'))

    departments = Department.query.all()
    form = PublishPaperForm(request.form)
    if request.method == "POST" and form.validate():
        # print(request.form)
        # print(request.files)
        publish_paper_modal = PublishPaper(title=form.title.data,
            abstract=form.abstract.data, paper_type_id=int(form.paper_type.data),
            department_area_id=int(form.department_area.data), publisher=form.publisher.data)
        for author_id in form.authors.data:
            author = User.query.filter_by(id=int(author_id)).first()
            if author:
                publish_paper_modal.authors.append(author)

        if 'paper_file' in request.files and request.files['paper_file'].filename != '':
            _, f_ext = os.path.splitext(request.files['paper_file'].filename)
            # print(f_ext[1:], str(PaperType.query.get(int(form.paper_type.data))).name.lower())
            if PaperType.query.get(int(form.paper_type.data)).name.lower() == 'dataset' and (f_ext[1:] not in ['csv', 'tsv', 'json', 'xlsx']):
                flash("For Dataset extension should be in 'csv', 'tsv', 'json', 'xlsx'", 'danger')
                return redirect(url_for('publish_paper'))
            paper_file = save_publish_paper_pdf(request.files['paper_file'])
            publish_paper_modal.paper_file = paper_file

        db.session.add(publish_paper_modal)
        db.session.commit()
        flash('Your request has been submitted successfully', 'success')
        return redirect(url_for('publish_paper'))
    return render_template('publish_paper.html',form=form, departments=departments)

@app.route('/faculty/all')
def all_faculties():
    page = request.args.get('page', 1, type=int)
    faculties = User.query.join(Role).filter(Role.name=="faculty").paginate(page, app.config['FACULTIES_PER_PAGE'], False)
    # faculties = User.query.join(Role).filter(Role.name=="faculty").paginate(page, 1, False)
    return render_template('all_faculties.html', title='All Faculties', faculties=faculties)

@app.route('/faculty/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def faculty_edit_profile(id):
    if current_user.id != id:
        flash('You are unauthorized to edit that faculty', 'danger')
        return redirect(url_for('index'))
    fedit_form = EditFacultyProfileForm(request.form)
    if fedit_form.validate_on_submit():
        current_user.fname = fedit_form.fname.data
        current_user.lname = fedit_form.lname.data
        current_user.email = fedit_form.email.data
        current_user.institution_id = int(fedit_form.institution.data)

        print(request.files)

        if 'picture' in request.files and request.files['picture'].filename != '':
            print("hi")
            picture_file = save_profile_picture(request.files['picture'])
            current_user.profile_image = picture_file

        if current_user.faculty:
            current_user.faculty.phone_number = fedit_form.phone_number.data
            current_user.faculty.address = fedit_form.address.data
            current_user.faculty.work_exp = fedit_form.work_exp.data
            current_user.faculty.designation = fedit_form.designation.data
            current_user.faculty.department = fedit_form.department.data
            current_user.faculty.about_me = fedit_form.about_me.data
            current_user.faculty.linkedin = fedit_form.linkedin.data
            current_user.faculty.github = fedit_form.github.data
        else:
            newFaculty = Faculty(phone_number=fedit_form.phone_number.data, address=fedit_form.address.data,
                work_exp=fedit_form.work_exp.data, designation=fedit_form.designation.data, department=fedit_form.department.data,
                about_me=fedit_form.about_me.data, user_id=current_user.id, linkedin=fedit_form.linkedin.data,
                github=fedit_form.github.data)

            db.session.add(newFaculty)

        db.session.commit()
        flash('Your account has been Updated!', 'success')
        return redirect(url_for('faculty_profile', id=current_user.id))
    elif request.method == 'GET':
        fedit_form.fname.data = current_user.fname
        fedit_form.lname.data = current_user.lname
        fedit_form.email.data = current_user.email
        # form.role.data = current_user.role.name
        fedit_form.institution.data = current_user.institution

        if current_user.faculty:
            fedit_form.phone_number.data = current_user.faculty.phone_number
            fedit_form.address.data = current_user.faculty.address
            fedit_form.work_exp.data = current_user.faculty.work_exp
            fedit_form.designation.data = current_user.faculty.designation
            fedit_form.department.data = current_user.faculty.department
            fedit_form.about_me.data = current_user.faculty.about_me
            fedit_form.github.data = current_user.faculty.github
            fedit_form.linkedin.data = current_user.faculty.linkedin

    image_file = None
    if current_user.profile_image:
        image_file = url_for('static', filename='profile_pics/' + current_user.profile_image)

    # return render_template('edit_profile.html', title='Edit Profile', form=form, image_file=image_file)
    # fedit_form = EditFacultyProfileForm()
    return render_template('faculty_edit_profile.html', title='Faculty Edit Profile', fedit_form=fedit_form, image_file=image_file)

@app.route('/faculty/<int:id>')
def faculty_profile(id):
    user = User.query.get_or_404(id)
    if Role.query.get(int(user.role_id)).name.lower() not in ['faculty', 'admin', 'panel']:
        flash('This page is allowed only for faculties', 'warning')
        return redirect(url_for('index'))
    return render_template('faculty_profile.html', user=user)

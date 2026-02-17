from flask import Flask, render_template, redirect, url_for, flash, request, g, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from functools import wraps
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateTimeLocalField, BooleanField
from flask import flash, redirect, url_for
from flask_login import current_user
from wtforms import SelectField, PasswordField
from wtforms.validators import DataRequired, Optional
from flask_wtf import FlaskForm
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, BaseView, expose
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateTimeLocalField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, Optional, ValidationError
from flask_babel import Babel, gettext, lazy_gettext as _l
from datetime import datetime, timedelta
from flask import render_template
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask import flash, redirect, url_for
from flask_babel import gettext
from flask import render_template
from flask_login import current_user
from flask import Flask, render_template, url_for
from flask import Flask, render_template, redirect, url_for, flash, request, g, session
import os
from flask import Flask, render_template, redirect, url_for, flash, request, g, session
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateTimeLocalField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, Optional, ValidationError

# Import Flask-Admin and related modules
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm

def get_locale():
    # If a locale is explicitly requested in the URL, use it
    if 'locale' in request.view_args:
        return request.view_args['locale']
    # If a locale is stored in the session, use it
    elif 'locale' in session:
        return session['locale']
    # Otherwise, try to guess the language from the user's accept headers
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LANGUAGES'])

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath("instance/site.db")}'
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
app.config['BABEL_SUPPORTED_LANGUAGES'] = ['en', 'ar']  # Add supported languages
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
babel = Babel(app, locale_selector=get_locale)

# Define User Roles and Permissions
class Role:
    ADMIN = 'admin'
    COUNCIL_MEMBER = 'council_member'
    TRACKER = 'tracker'

class Permission:
    EDIT_PROJECT = 'edit_project'




# Start of Database Models -------------------------------------------------------------------------------------------

# Database Models
class User(db.Model, UserMixin):  # Inherit from UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.COUNCIL_MEMBER)
    contact_details = db.Column(db.Text)
    tracked_projects = db.relationship('Project', backref='tracker', lazy=True, foreign_keys='[Project.tracker_id]')
    created_projects = db.relationship('Project', backref='creator', lazy=True, foreign_keys='[Project.created_by_id]')
    votes = db.relationship('Vote', backref='user', lazy=True)
    permissions = db.Column(db.Text)
    volunteering_projects = db.relationship('ProjectMember', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

    def has_permission(self, permission):
        return self.role == Role.ADMIN or permission in (self.permissions or '').split(',')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tracker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='Pending')
    category = db.Column(db.String(50))
    voting_deadline = db.Column(db.DateTime)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    vote_type = db.Column(db.String(50), default='simple_majority')
    votes = db.relationship('Vote', backref='project', lazy=True)
    volunteers = db.relationship('ProjectMember', backref='project', lazy=True)

    def __repr__(self):
        return f"Project('{self.title}', '{self.status}')"

    def progress(self):
        # --- This is your EXISTING method for overall project progress ---
        if self.start_date and self.end_date:
            today = datetime.utcnow()
            if today < self.start_date:
                return 0
            if today > self.end_date:
                return 100
            # Add check for total_days being zero
            try:
                total_duration = self.end_date - self.start_date
                if total_duration.total_seconds() <= 0:
                    return 100 # If end <= start, consider it 100% done
                elapsed_duration = today - self.start_date
                # Ensure elapsed duration isn't negative if clock sync issues occur
                percentage = max(0, elapsed_duration.total_seconds() / total_duration.total_seconds()) * 100
                return min(100, percentage) # Clamp between 0 and 100
            except TypeError: # Handle potential issues if dates aren't datetimes
                return 0
        return 0

    # --- ADD THIS NEW METHOD ---
    def voting_progress(self):
        """
        Calculates the percentage of time elapsed between the project's
        start date and its voting deadline.
        Returns 0 if deadline/start date not set or voting hasn't started.
        Returns 100 if the deadline has passed.
        """
        now = datetime.utcnow()

        # Prerequisites: Need a start date and a voting deadline
        if not self.start_date or not self.voting_deadline:
            return 0

        # If voting deadline is before the start date (invalid data), show 0 progress
        if self.voting_deadline <= self.start_date:
             return 0 # Or perhaps 100? Let's say 0 for invalid range.

        # If current time is before the project starts, voting hasn't begun
        if now < self.start_date:
            return 0

        # If current time is after or at the deadline, voting period is over (100%)
        if now >= self.voting_deadline:
            return 100

        # --- Calculate percentage based on time elapsed within the voting period ---
        try:
            total_voting_duration = self.voting_deadline - self.start_date
            elapsed_voting_time = now - self.start_date

            if total_voting_duration.total_seconds() <= 0:
                 # Should have been caught by earlier check, but belt-and-suspenders
                 return 100

            percentage = (elapsed_voting_time.total_seconds() / total_voting_duration.total_seconds()) * 100
            # Clamp between 0 and 100
            return max(0, min(100, percentage))

        except TypeError: # Handle potential issues if dates aren't datetimes
             return 0
    
    

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    vote = db.Column(db.Boolean, nullable=False)
    vote_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'project_id', name='unique_vote'),)

    def __repr__(self):
        return f"Vote('{self.user_id}', '{self.project_id}', '{self.vote}')"    

class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    project_name = db.Column(db.String(100), nullable=False)
    additional_info = db.Column(db.Text)

    def __repr__(self):
        return f"Volunteer('{self.name}', '{self.project_name}')"
    

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True) # Use Text for potentially long URLs

    def __repr__(self):
        return f"<Setting {self.key}>"

class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    volunteer_name = db.Column(db.String(100))

    def __repr__(self):
        return f"ProjectMember('{self.user_id}', '{self.project_id}')"




# END of Database Models -------------------------------------------------------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Flask-Admin Views STRART ---------------------------------------------------------------------------------------------------------------
# Customized AuthModelView to restrict access to admins
class AuthModelView(ModelView):
    form_base_class = SecureForm  # Enable CSRF protection
    def is_accessible(self):
        #return current_user.is_authenticated and current_user.role == Role.ADMIN
        return True
    def inaccessible_callback(self, name, **kwargs):
        flash(gettext('You do not have permission to access this page.'), 'danger')
        return redirect(url_for('dashboard', locale=get_locale()))

class UserModelView(AuthModelView):
    column_editable_list = ['contact_details'] # Keep 'role' removed here
    column_searchable_list = ['username', 'email']
    column_filters = ['role']
    form_columns = ['username', 'email', 'password', 'role', 'contact_details', 'permissions']
    column_exclude_list = ['password']
    form_excluded_columns = ['password']

    form_overrides = {
        'role': SelectField
    }
    form_args = {
        'role': {
            'label': 'Role',
            'choices': [
                (Role.ADMIN, 'Admin'),
                (Role.COUNCIL_MEMBER, 'Council Member'),
                (Role.TRACKER, 'Tracker')
            ],
            'validators': [DataRequired()]
        }
    }

    # --- Use the working on_model_change logic ---
    def on_model_change(self, form, model, is_created):
        # Access the password field via form._fields
        password_field_instance = form._fields.get('password')

        # Check if the field exists and has data
        if password_field_instance and password_field_instance.data:
            print("Hashing password via on_model_change...") # Debug message
            # Pass the raw password data to the model's method
            model.set_password(password_field_instance.data)
        else:
            print("Password field empty or not retrieved - Skipping hashing.") # Debug message

    # --- Keep the create_form and edit_form methods as they were ---
    def create_form(self, obj=None):
        form = super(UserModelView, self).create_form(obj)
        # Explicitly add PasswordField for creation
        form.password = PasswordField('Password', validators=[DataRequired()])
        return form

    def edit_form(self, obj=None):
        form = super(UserModelView, self).edit_form(obj)
        # Explicitly add PasswordField for editing (optional)
        form.password = PasswordField('New Password', validators=[Optional()])
        # Role field is handled by overrides/args
        return form

class ProjectModelView(AuthModelView):
    column_editable_list = ['status', 'tracker_id', 'voting_deadline', 'start_date', 'end_date']
    column_searchable_list = ['title', 'description']
    column_filters = ['status', 'category', 'tracker_id']
    column_list = ['id', 'title', 'status', 'category', 'voting_deadline', 'start_date', 'end_date', 'tracker']
    form_excluded_columns = ['created_by'] # Exclude the created_by field from forms

    def on_model_change(self, form, model, is_created):
       if is_created:
           model.created_by_id = current_user.id
       super(ProjectModelView, self).on_model_change(form, model, is_created)

class VoteModelView(AuthModelView):
    column_list = ['id', 'user', 'project', 'vote', 'vote_timestamp']
    column_filters = ['vote', 'vote_timestamp', 'user_id', 'project_id']
    can_create = False  # Prevent creating new votes directly in admin
    can_edit = False    # Prevent editing existing votes directly in admin

class VolunteerModelView(AuthModelView):
    column_list = ['id', 'name', 'project_name', 'additional_info']
    column_searchable_list = ['name', 'project_name']

class ProjectMemberModelView(AuthModelView):
    column_list = ['id', 'user', 'project']
    column_filters = ['user_id', 'project_id']

# Example of a custom admin view (not tied to a model)
class AnalyticsView(BaseView):
    @expose('/')
    def index(self):
        # You can perform calculations or fetch data here
        user_count = User.query.count()
        project_count = Project.query.count()
        return self.render('admin/analytics.html', user_count=user_count, project_count=project_count)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN
    def inaccessible_callback(self, name, **kwargs):
        flash(gettext('You do not have permission to access this page.'), 'danger')
        return redirect(url_for('dashboard', locale=get_locale()))

# Initialize Flask-Admin
admin = Admin(app, name='CouncilTrack Admin', template_mode='bootstrap4')

# Add model views
admin.add_view(UserModelView(User, db.session))
admin.add_view(ProjectModelView(Project, db.session))
admin.add_view(VoteModelView(Vote, db.session))
admin.add_view(VolunteerModelView(Volunteer, db.session))
admin.add_view(ProjectMemberModelView(ProjectMember, db.session))

# Add custom views
admin.add_view(AnalyticsView(name='Analytics', endpoint='analytics'))

# Flask-Admin Views END ---------------------------------------------------------------------------------------------------------------



# Forms
class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField(_l('Email'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    confirm_password = PasswordField(_l('Confirm Password'), validators=[DataRequired(), EqualTo('password')])
    role = SelectField(_l('Role'), choices=[(Role.COUNCIL_MEMBER, _l('Council Member')), (Role.TRACKER, _l('Project Tracker'))], default=Role.COUNCIL_MEMBER)
    submit = SubmitField(_l('Sign Up'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(_l('That email is taken. Please choose a different one.'))

class VolunteerForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired()])
    additional_info = TextAreaField(_l('Additional Info'), validators=[DataRequired()])
    submit = SubmitField(_l('Volunteer'))



class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    submit = SubmitField(_l('Login'))

class CreateProjectForm(FlaskForm):
    title = StringField(_l('Title'), validators=[DataRequired()])
    description = TextAreaField(_l('Description'), validators=[DataRequired()])
    category = StringField(_l('Category'), validators=[Optional()])
    voting_deadline = DateTimeLocalField(_l('Voting Deadline'), format='%Y-%m-%dT%H:%M', validators=[Optional()])
    start_date = DateTimeLocalField(_l('Start Date'), format='%Y-%m-%dT%H:%M', validators=[Optional()])
    end_date = DateTimeLocalField(_l('End Date'), format='%Y-%m-%dT%H:%M', validators=[Optional()])
    submit = SubmitField(_l('Create Project'))

class EditProjectForm(FlaskForm):
    title = StringField(_l('Title'), validators=[DataRequired()])
    description = TextAreaField(_l('Description'), validators=[DataRequired()])
    category = StringField(_l('Category'), validators=[Optional()])
    voting_deadline = DateTimeLocalField(_l('Voting Deadline'), format='%Y-%m-%dT%H:%M', validators=[Optional()])
    start_date = DateTimeLocalField(_l('Start Date'), format='%Y-%m-%dT%H:%M', validators=[Optional()])
    end_date = DateTimeLocalField(_l('End Date'), format='%Y-%m-%dT%H:%M', validators=[Optional()])
    status = SelectField(_l('Status'), choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Completed', 'Completed')], validators=[DataRequired()])
    submit = SubmitField(_l('Update Project'))

class AssignTrackerForm(FlaskForm):
    tracker = SelectField(_l('Assign Tracker'), coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l('Assign Tracker'))

class VoteForm(FlaskForm):
    vote = SelectField(_l('Vote'), choices=[('True', _l('Yes')), ('False', _l('No'))], validators=[DataRequired()])
    submit = SubmitField(_l('Submit Vote'))
class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField(_l('Email'), validators=[DataRequired()])
    contact_details = TextAreaField(_l('Contact Details'), validators=[Optional()])
    submit = SubmitField(_l('Update Profile'))

class SearchFilterForm(FlaskForm):
    search_term = StringField(_l('Search Keywords'), validators=[Optional()])
    status = SelectField(_l('Status'), choices=[('', _l('Any')), ('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Completed', 'Completed')], validators=[Optional()])
    category = StringField(_l('Category'), validators=[Optional()])
    tracker_id = SelectField(_l('Tracker'), coerce=int, choices=[(0, _l('Any'))], validators=[Optional()])
    submit = SubmitField(_l('Apply Filters'))

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.ADMIN:
            flash(gettext('You do not have permission to access this page.'), 'danger')
            return redirect(url_for('dashboard', locale=get_locale()))
        return func(*args, **kwargs)
    return wrapper
def council_member_required(func):
    def wrapper(*args, **kwargs):
        if current_user.role not in [Role.ADMIN, Role.COUNCIL_MEMBER]:
            flash(gettext('You do not have permission to access this page.'), 'danger')
            return redirect(url_for('dashboard', locale=get_locale()))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def tracker_required(func):
    def wrapper(*args, **kwargs):
        if current_user.role not in [Role.ADMIN, Role.TRACKER]:
            flash(gettext('You do not have permission to access this page.'), 'danger')
        wrapper.__name__ = func.__name__
        return redirect(url_for('dashboard', locale=get_locale()))

def permission_required(permission):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not current_user.has_permission(permission):
                flash(gettext('You do not have the required permission to access this page.'), 'danger')
                return redirect(url_for('dashboard', locale=get_locale()))
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator



@app.before_request
def before_request():
    g.search_filter_form = SearchFilterForm(request.args)
    g.search_filter_form.tracker_id.choices.extend([(user.id, user.username) for user in User.query.filter_by(role=Role.TRACKER).all()])
    if current_user.is_authenticated:
        g.projects_to_vote = Project.query.filter(Project.voting_deadline > datetime.utcnow(), Project.id.notin_([vote.project_id for vote in current_user.votes])).order_by(Project.voting_deadline).all()
    else:
        g.projects_to_vote = []

# Routes

@app.route('/<locale>/dashboard')
def dashboard(locale):
    council_members_count = 0  # Replace with your actual data
    total_council_members = 15
    contact_persons_count = 0
    total_contact_persons = 50
    projects_count = 0
    total_projects = 30

    latest_news = [
        {"title": "News Title 1", "content": "Content of news 1..."},
        {"title": "News Title 2", "content": "Content of news 2..."},
        {"title": "News Title 3", "content": "Content of news 3..."},
    ]

    blog_links = [
        {'url': 'https://example-blog1.com', 'text': gettext('Blog Post 1')},
        {'url': 'https://example-blog2.com', 'text': gettext('Blog Post 2')},
        # Add more blog links here
    ]

    governmental_links = [
        {'url': 'https://government-institution1.gov', 'text': gettext('Institution 1')},
        {'url': 'https://government-institution2.gov', 'text': gettext('Institution 2')},
        # Add more governmental links here
    ]

    partners = [
        {'url': 'https://partner1.org', 'name': gettext('Partner One')},
        {'url': 'https://partner2.com', 'name': gettext('Partner Two')},
        # Add more partner links here
    ]

    if current_user.is_authenticated and current_user.role == Role.ADMIN:
        projects = Project.query.order_by(Project.start_date).limit(5).all()
        pending_votes = Project.query.filter(Project.voting_deadline > datetime.utcnow()).order_by(Project.voting_deadline).limit(5).all()
        return render_template('admin_dashboard.html',
                               num_projects=projects_count,
                               num_council_members=council_members_count,
                               contact_persons=contact_persons_count,
                               blog_links=blog_links,
                               governmental_links=governmental_links,
                               partners=partners,
                               projects=projects,
                               pending_votes=pending_votes,
                               latest_news=latest_news)
    elif current_user.is_authenticated and current_user.role == Role.COUNCIL_MEMBER:
        projects_to_vote = Project.query.filter(Project.voting_deadline > datetime.utcnow()).order_by(Project.voting_deadline).limit(5).all()
        return render_template('council_dashboard.html',
                               num_projects=projects_count,
                               num_council_members=council_members_count,
                               contact_persons=contact_persons_count,
                               blog_links=blog_links,
                               governmental_links=governmental_links,
                               partners=partners,
                               projects_to_vote=projects_to_vote,
                               latest_news=latest_news)
    elif current_user.is_authenticated and current_user.role == Role.TRACKER:
        assigned_projects = Project.query.filter_by(tracker_id=current_user.id).order_by(Project.start_date).limit(5).all()
        return render_template('tracker_dashboard.html',
                               num_projects=projects_count,
                               num_council_members=council_members_count,
                               contact_persons=contact_persons_count,
                               blog_links=blog_links,
                               governmental_links=governmental_links,
                               partners=partners,
                               assigned_projects=assigned_projects,
                               latest_news=latest_news)
    return render_template('dashboard.html',
                           council_members_count=council_members_count,
                           total_council_members=total_council_members,
                           contact_persons_count=contact_persons_count,
                           total_contact_persons=total_contact_persons,
                           projects_count=projects_count,
                           total_projects=total_projects,
                           latest_news=latest_news,
                           blog_links=blog_links,
                           governmental_links=governmental_links,
                           partners=partners)



@app.route("/<locale>/project/<int:project_id>/volunteer", methods=['GET', 'POST'])
def volunteer_for_project(locale, project_id):
    project = Project.query.get_or_404(project_id)
    form = VolunteerForm()
    if form.validate_on_submit():
        # Check if the user is logged in. If not, we'll associate the volunteer info
        # with the project directly. You might want to consider allowing non-logged-in
        # users to volunteer or prompting them to log in.
        if current_user.is_authenticated:
            # Create a ProjectMember entry to link the user to the project
            volunteer = Volunteer(name=form.name.data, project_name=project.title, additional_info=form.additional_info.data)
            db.session.add(volunteer)

        else:
            # If the user is not logged in, create a Volunteer entry
            project_member = ProjectMember(user_id=current_user.id, project_id=project_id)
            db.session.add(project_member)



        db.session.commit()
        flash(gettext('Thank you for volunteering for %(project_title)s!', project_title=project.title), 'success')
        return redirect(url_for('project', project_id=project_id, locale=locale))
    return render_template('volunteer_form.html', title=gettext('Volunteer for Project'), form=form, project=project)

@app.route("/", methods=['GET', 'POST'])
def home():
    # Redirect to the dashboard with the default locale
    return redirect(url_for('dashboard', locale=app.config['BABEL_DEFAULT_LOCALE']))

@app.route("/<locale>/projects/", methods=['GET', 'POST'])
def projects_list(locale):
    page = request.args.get('page', 1, type=int)
    projects_query = Project.query

    if g.search_filter_form.validate():
        if g.search_filter_form.search_term.data:
            search_term = f"%{g.search_filter_form.search_term.data}%"
            projects_query = projects_query.filter((Project.title.like(search_term)) | (Project.description.like(search_term)))
        if g.search_filter_form.status.data:
            projects_query = projects_query.filter_by(status=g.search_filter_form.status.data)
        if g.search_filter_form.category.data:
            projects_query = projects_query.filter_by(category=g.search_filter_form.category.data)
        if g.search_filter_form.tracker_id.data and g.search_filter_form.tracker_id.data != 0:
            projects_query = projects_query.filter_by(tracker_id=g.search_filter_form.tracker_id.data)

    projects = projects_query.order_by(Project.start_date).paginate(page=page, per_page=5)
    return render_template('projects_list.html', projects=projects)

@app.route("/<locale>/register", methods=['GET', 'POST'])
@admin_required
def register(locale):
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash(gettext('Account created successfully!'), 'success')
        return redirect(url_for('manage_users', locale=locale))
    return render_template('register.html', title=gettext('Register'), form=form)

@app.route("/<locale>/login", methods=['GET', 'POST'])
def login(locale):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard', locale=locale))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard', locale=locale))
        else:
            flash(gettext('Login Unsuccessful. Please check username and password'), 'danger')
    return render_template('login.html', title=gettext('Login'), form=form)

@app.route("/<locale>/logout")
@login_required
def logout(locale):
    logout_user()
    return redirect(url_for('home'))

@login_manager.unauthorized_handler
def unauthorized():
    flash(gettext('Please log in to access this page.'), 'warning')
    return redirect(url_for('login', locale=get_locale()))

@app.route("/<locale>/project/new", methods=['GET', 'POST'])
@login_required
@admin_required
def new_project(locale):
    form = CreateProjectForm()
    if form.validate_on_submit():
         project = Project(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            voting_deadline=form.voting_deadline.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            created_by_id=current_user.id
            )
         db.session.add(project)
         db.session.commit()
         flash(gettext('New project created successfully!'), 'success')
         return redirect(url_for('projects_list', locale=locale))

    return render_template('create_project.html', title=gettext('New Project'), form=form)

@app.route("/<locale>/project/<int:project_id>", methods=['GET', 'POST'])
def project(locale, project_id):
    project = Project.query.get_or_404(project_id)
    vote_form = VoteForm()
    if current_user.is_authenticated:
        has_voted = Vote.query.filter_by(user_id=current_user.id, project_id=project_id).first() is not None
    else:
        has_voted = False
    can_vote = project.voting_deadline is None or project.voting_deadline > datetime.utcnow()
    return render_template('project.html', title=project.title, project=project, vote_form=vote_form, has_voted=has_voted, can_vote=can_vote)

@app.route("/<locale>/project/<int:project_id>/edit", methods=['GET', 'POST'])
@permission_required(Permission.EDIT_PROJECT)
def edit_project(locale, project_id):
    project = Project.query.get_or_404(project_id)
    form = EditProjectForm(obj=project)
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        project.category = form.category.data
        project.voting_deadline = form.voting_deadline.data
        project.start_date = form.start_date.data
        project.end_date = form.end_date.data
        project.status = form.status.data
        db.session.commit()
        flash(gettext('Project updated successfully!'), 'success')
        return redirect(url_for('project', project_id=project.id, locale=locale))
    return render_template('edit_project.html', title=gettext('Edit Project'), form=form, project=project)

@app.route("/set_language/<locale>")
def set_language(locale):
    session['locale'] = locale
    # Redirect to the dashboard with the new locale
    return redirect(url_for('dashboard', locale=locale))

@app.route("/<locale>/project/<int:project_id>/vote", methods=['POST'])
@login_required
@council_member_required
def vote(locale, project_id):
    project = Project.query.get_or_404(project_id)
    if project.voting_deadline and project.voting_deadline < datetime.utcnow():
        flash(gettext('Voting deadline has passed for this project.'), 'warning')
        return redirect(url_for('project', project_id=project.id, locale=locale))

    form = VoteForm()
    if form.validate_on_submit():
        vote_value = form.vote.data == 'True'
        existing_vote = Vote.query.filter_by(user_id=current_user.id, project_id=project_id).first()
        if existing_vote:
            existing_vote.vote = vote_value
            existing_vote.vote_timestamp = datetime.utcnow()
            flash(gettext('Vote updated successfully!'), 'info')
        else:
            vote = Vote(user_id=current_user.id, project_id=project_id, vote=vote_value, vote_timestamp=datetime.utcnow())
            db.session.add(vote)
            flash(gettext('Vote submitted successfully!'), 'success')
        db.session.commit()
        return redirect(url_for('project', project_id=project.id, locale=locale))
    return render_template('project.html', title=project.title, project=project, vote_form=form)

@app.route("/<locale>/project/<int:project_id>/results")
@login_required
def view_results(locale, project_id):
    project = Project.query.get_or_404(project_id)
    if current_user.role not in [Role.ADMIN, Role.COUNCIL_MEMBER]: # Adjust permissions as needed
        flash(gettext('You do not have permission to view voting results.'), 'danger')
        return redirect(url_for('project', project_id=project.id, locale=locale))
    yes_votes = Vote.query.filter_by(project_id=project_id, vote=True).count()
    no_votes = Vote.query.filter_by(project_id=project_id, vote=False).count()
    return render_template('results.html', project=project, yes_votes=yes_votes, no_votes=no_votes)

@app.route("/<locale>/project/<int:project_id>/assign", methods=['GET', 'POST'])
@admin_required
def assign_tracker(locale, project_id):
    project = Project.query.get_or_404(project_id)
    form = AssignTrackerForm()
    form.tracker.choices = [(user.id, user.username) for user in User.query.filter_by(role=Role.TRACKER).all()]
    if form.validate_on_submit():
        tracker = User.query.get_or_404(form.tracker.data)
        project.tracker = tracker
        db.session.commit()
        flash(gettext('Project assigned to %(tracker_name)s!', tracker_name=tracker.username), 'success')
        return redirect(url_for('project', project_id=project.id, locale=locale))
    return render_template('assign_tracker.html', title=gettext('Assign Tracker'), form=form, project=project)

@app.route("/<locale>/project/<int:project_id>/track")
@login_required
@tracker_required
def track_project(locale, project_id):
    project = Project.query.get_or_404(project_id)
    if current_user.role != Role.ADMIN and project.tracker_id != current_user.id:
        flash(gettext('You do not have permission to track this project.'), 'danger')
        return redirect(url_for('dashboard', locale=locale))
    return render_template('track_project.html', title=gettext('Track Project'), project=project)

@app.route("/<locale>/manage_users")
@login_required
@admin_required
def manage_users(locale):
    users = User.query.all()
    return render_template('manage_users.html', title=gettext('Manage Users'), users=users)

@app.route("/<locale>/profile/edit", methods=['GET', 'POST'])
@login_required
def edit_profile(locale):
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.contact_details = form.contact_details.data
        db.session.commit()
        flash(gettext('Your profile has been updated!'), 'success')
        return redirect(url_for('dashboard', locale=locale))
    return render_template('edit_profile.html', title=gettext('Edit Profile'), form=form)

@app.route("/<locale>/calendar")
def calendar(locale):
    projects = Project.query.all()
    return render_template('calendar.html', projects=projects)

@app.context_processor
def inject_locale():
    return {'get_locale': get_locale}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create initial admin user if not exists
        admin_user = User.query.filter_by(role=Role.ADMIN).first()
        
        if not admin_user:
            hashed_password = generate_password_hash('adminpassword') # Change this!
            admin_user = User(username='admin', email='admin@example.com', password=hashed_password, role=Role.ADMIN)
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Assignment, HomeworkStatus
from forms import LoginForm, AssignmentForm
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def create_tables():
    db.create_all()
    # Create default admin and student for demo
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('adminpass')
        db.session.add(admin)
    if not User.query.filter_by(username='student').first():
        student = User(username='student', role='student')
        student.set_password('studentpass')
        db.session.add(student)
    db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    assignments = Assignment.query.all()
    statuses = {s.assignment_id: s.status for s in HomeworkStatus.query.filter_by(user_id=current_user.id)}
    return render_template('dashboard.html', assignments=assignments, statuses=statuses)

@app.route('/assignments', methods=['GET', 'POST'])
@login_required
def assignments():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    form = AssignmentForm()
    if form.validate_on_submit():
        new_assignment = Assignment(title=form.title.data, deadline=form.deadline.data)
        db.session.add(new_assignment)
        db.session.commit()
        flash('Assignment added!')
    all_assignments = Assignment.query.all()
    return render_template('assignments.html', form=form, assignments=all_assignments)

@app.route('/update_status/<int:assignment_id>/<string:status>')
@login_required
def update_status(assignment_id, status):
    record = HomeworkStatus.query.filter_by(user_id=current_user.id, assignment_id=assignment_id).first()
    if not record:
        record = HomeworkStatus(user_id=current_user.id, assignment_id=assignment_id, status=status)
        db.session.add(record)
    else:
        record.status = status
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/leaderboard')
@login_required
def leaderboard():
    users = User.query.all()
    leaderboard_data = []
    for user in users:
        completed = HomeworkStatus.query.filter_by(user_id=user.id, status='done').count()
        leaderboard_data.append((user.username, completed))
    leaderboard_data.sort(key=lambda x: x[1], reverse=True)
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

if __name__ == '__main__':
    app.run(debug=True)

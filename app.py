from flask import Flask, render_template, redirect, session, flash, url_for, g
from models import db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///feedback_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'superflaskfeedback'

db.init_app(app)

with app.app_context():
    db.create_all()


@app.before_request
def load_logged_in_user():
    """If user is logged in, set g.user to that user."""

    if 'username' in session:
        g.user = User.query.filter_by(username=session['username']).first()
    else:
        g.user = None


@app.route('/')
def homepage():
    return redirect('/register')


@app.route('/register', methods=['GET'])
def show_register_form():
    form = RegisterForm()
    return render_template('register.html', form=form)


@app.route('/register', methods=['POST'])
def process_register_form():
    form = RegisterForm()

    if form.validate_on_submit():
        try:
            user = User.register(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )

            db.session.add(user)
            db.session.commit()

            session['username'] = user.username
            flash(f"Welcome, {user.username}!  Your account has been created.", "success")
            return redirect(url_for('show_user_details', username=user.username))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {e}", "danger")
    
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET'])
def show_login_user_form():
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/login', methods=['POST'])
def process_login_user_form():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data
        )
        if user:
            session['username'] = user.username
            return redirect(url_for('show_user_details', username=user.username))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

# @app.route('/secret')
# def secret():
#     if 'username' not in session:
#         flash('You must be logged in to view this page', 'danger')
#         return redirect('/login')
#     return 'You made it!'

@app.route('/users/<username>')
def show_user_details(username):
    user = User.query.filter_by(username=username).first_or_404()
    feedbacks = Feedback.query.filter_by(username=username).all()

    if not g.user or g.user.username != username:
        flash('You do not have access to this page', 'danger')
        return redirect(url_for('show_login_user_form'))

    return render_template('user_detail.html', user=user, feedbacks=feedbacks)


@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    user = User.query.filter_by(username=username).first_or_404()

    if not g.user or g.user.username != username:
        flash('You do not have permission to remove this user.', 'danger')
        return redirect(url_for('show_login_user_form'))

    db.session.delete(user)
    db.session.commit()

    # Clears session
    session.pop('username', None)
    flash(f"User {username} and all associated feedback deleted.", "success")
    return redirect('/')


@app.route('/users/<username>/feedback/add', methods=['GET'])
def show_feedback_form(username):
    user = User.query.filter_by(username=username).first_or_404()

    if g.user.username != username:
        flash('You do not have permission to add feedback.', 'danger')
        return redirect(url_for('show_login_user_form'))
    
    form = FeedbackForm()
    return render_template('feedback_form.html', form=form, user=user)


@app.route('/users/<username>/feedback/add', methods=['POST'])
def add_feedback(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    if not g.user or g.user.username != username:
        flash('You do not have permission to add feedback.', 'danger')
        return redirect(url_for('show_login_user_form'))

    form = FeedbackForm()

    if form.validate_on_submit():
        feedback = Feedback(
            title=form.title.data,
            content=form.content.data,
            username=user.username
        )
        db.session.add(feedback)
        db.session.commit()

        flash('Feedback added successfully!', 'success')
        return redirect(url_for('show_user_details', username=g.user.username))
    
    flash("Error adding feedback. Please try again.", "danger")
    return render_template('feedback_form.html', form=form, user=user, form_title="Add Feedback")


@app.route('/feedback/<int:feedback_id>/update', methods=['GET'])
def show_update_feedback_form(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)

    if not g.user or g.user.username != feedback.username:
        flash('You do not have permission to edit this feedback.', 'danger')
        return redirect(url_for('show_login_user_form'))
    
    form = FeedbackForm(obj=feedback)
    return render_template('feedback_form.html', form=form, feedback=feedback, form_title="Add Feedback")


@app.route('/feedback/<int:feedback_id>/update', methods=['POST'])
def process_update_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)

    if not g.user or g.user.username != feedback.username:
        flash('You do not have permission to edit this feedback.', 'danger')
        return redirect(url_for('show_login_user_form'))
    
    form = FeedbackForm()

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()

        flash('Feedback updated successfully!', 'success')
        return redirect(url_for('show_user_details', username=feedback.username))
    
    return render_template('feedback_form.html', form=form, feedback=feedback, form_title="Update Feedback")


@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)

    if not g.user or g.user.username != feedback.username:
        flash('You do not have permission to delete this feedback.', 'danger')
        return redirect(url_for('show_login_user_form'))
    
    db.session.delete(feedback)
    db.session.commit()

    flash('Feedback deleted!', 'success')
    return redirect(url_for('show_user_details', username=feedback.username))








from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, session, json
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.sql import select
from functions import login_required

app = Flask(__name__)
app.secret_key = "tttggghhh"
app.permanent_session_lifetime = timedelta(minutes=10)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Users(db.Model):
    """A table to store the user's name and password"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False)
    hash = db.Column(db.String, nullable=False)
    tasks = db.relationship('Todo', backref='user')

    @property
    def password(self):
        raise AttributeError("Password not visible attribute")

    # set the password
    @password.setter
    def password(self, password):
        self.hash = generate_password_hash(password)

    # Verify the password
    def verify_password(self, password):
        return check_password_hash(self.hash, password)

    def __repr__(self):
        return '<username %r>' % self.username


class Todo(db.Model):
    """A table to store tasks for each user)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return '<Task %r>' % self.id


class UsersEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, 'to_json'):
            return o.to_json()
        else:
            return super(UsersEncoder, self).default(o)


app.json_encoder = UsersEncoder


@app.route("/", methods=['POST', 'GET'])
@login_required
def index():
    """Display the user's tasks"""
    current_user_id = session["user_id"]
    if request.method == 'GET':

        # Get username of current user to pass to template
        username = Users.query.filter_by(id=current_user_id).first()

        # Query database for all the tasks of the current user
        user = current_user_id
        tasks = Todo.query.order_by(
            Todo.date_created).filter(Todo.user_id == user).all()

        return render_template("index.html", tasks=tasks, username=username)

    else:
        # Get the data from the form
        task = request.form.get('content')

        # Check for errors
        if not task:
            flash("Please enter a task", "warning")

        # Add new task to database
        user = current_user_id
        new_task = Todo(content=task, user_id=current_user_id)

        try:
            db.session.add(new_task)
            db.session.commit()
            flash("New Task Added!")
            return redirect('/')
        except:
            flash("Sorry could not add task", "warning")
            return redirect('/')


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    """Delete a task"""
    task_to_delete = Todo.query.get_or_404(id)

    # Ensure users can only delete their posts
    current_user_id = session["user_id"]
    if current_user_id == task_to_delete.user.id:
        try:
            db.session.delete(task_to_delete)
            db.session.commit()
            flash("Task deleted!")
            return redirect('/')

        except:
            return "Could not delete task"


@app.route('/update/<int:id>', methods=['POST', 'GET'])
@login_required
def update(id):
    """Update a task"""
    task_to_updt = Todo.query.get_or_404(id)
    if request.method == 'GET':
        return render_template('update.html', task=task_to_updt)

    else:
        task_to_updt.content = request.form.get('content')

        current_user_id = session["user_id"]
        if current_user_id == task_to_updt.user.id:

            # Update task on database
            try:
                db.session.commit()
                flash("Task updated!")
                return redirect('/')
            except:
                return "Could not update task"


@app.route("/login", methods=['POST', 'GET'])
def login():
    """Allow existing users to login"""
    # Forget any other user_ids
    session.clear()

    if request.method == "POST":
        # Get data from the form submitted
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure both fields were filled
        if not username:
            flash("Please enter a username")
            return redirect("/login")
        if not password:
            flash("Please enter a password")
            return redirect("/login")

        # Check if the 2 fields match a user on the database
        user = Users.query.filter_by(username=username).first()

        if not user or not user.verify_password(password):
            flash("Sorry, Invalid username or password!")
            return redirect("/login")

        # Remember this user's id
        session["user_id"] = user.id
        session.permanent = True
        flash("You are Logged In!")
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout any active users"""
    # Forget any user ids
    session.clear()

    flash(f"You have been logged out!", "info")
    return redirect("/login")


@app.route("/register", methods=['POST', 'GET'])
def register():
    """Register new users"""
    if request.method == 'GET':
        return render_template("register.html")

    else:
        # Get the form data
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check for common errors
        if not password or not username or not confirmation:
            flash("Please input all fields")
            return redirect("/register")

        if password != confirmation:
            flash("Passwords do not match!")
            return redirect("/register")

        # Store username and hash on users db
        new_user = Users(username=username,
                         hash=generate_password_hash(password))

        try:
            db.session.add(new_user)
            db.session.commit()

        except:
            flash("Could not register. please try again!")
            return redirect("/register")

        session["user_id"] = new_user.id
        return redirect("/")


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)

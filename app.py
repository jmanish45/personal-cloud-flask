from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
# --- NEW IMPORTS ---
# For database and user management
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- NEW CONFIGURATIONS ---
# This is required by Flask to use the flashing system securely.
app.secret_key = 'a_super_secret_key_12345'
# Configure the database (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- INITIALIZE EXTENSIONS ---
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
# If a user tries to access a page that requires login, redirect them here
login_manager.login_view = 'login'


# --- NEW DATABASE MODEL ---
# This class defines the 'User' table in our database.
# UserMixin provides default implementations for methods that Flask-Login expects user objects to have.
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


# --- FLASK-LOGIN USER LOADER ---
# This function is used by Flask-Login to reload the user object from the user ID stored in the session.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- EXISTING CODE (UNCHANGED FOR NOW) ---
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part in the request.')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected. Please choose a file to upload.')
        return redirect(url_for('index'))
    
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    flash(f"File '{file.filename}' uploaded successfully!")
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"File '{filename}' was successfully deleted.")
    return redirect(url_for("index"))


if __name__ == '__main__':
    # --- NEW: CREATE DATABASE TABLES ---
    # This checks if the database file exists and creates the tables if it doesn't.
    with app.app_context():
        db.create_all()
    app.run(debug=True)


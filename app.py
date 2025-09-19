from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from ai_utils import analyze_file, find_semantic_matches # Import our new analyzer function

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- DATABASE & LOGIN MANAGER SETUP ---
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    files = db.relationship('FileMetadata', backref='owner', lazy=True)

class FileMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    tags = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- FLASK-LOGIN USER LOADER ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- AUTHENTICATION ROUTES ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists. Please choose another one.', 'error')
            return redirect(url_for('signup'))

        new_user = User(
            username=username,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Username not found. Please check your spelling or sign up.', 'error')
            return redirect(url_for('login'))

        if not check_password_hash(user.password, password):
            flash('Incorrect password. Please try again.', 'error')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- CORE APPLICATION ROUTES ---
@app.route('/')
@login_required
def index():
    # --- NEW CATEGORIZATION LOGIC ---
    # 1. Define our smart categories and their keywords
    CATEGORIES = {
        'Receipts & Invoices': ['receipt', 'invoice', 'payment', 'bill'],
        'ID & Documents': ['id card', 'document', 'license', 'passport', 'certificate', 'resume'],
        'Photos & Images': ['photo', 'image', 'picture', 'screenshot', 'selfie', 'portrait'],
    }

    # 2. Fetch all file metadata for the current user
    all_files_metadata = FileMetadata.query.filter_by(user_id=current_user.id).all()

    # 3. Sort files into categories
    categorized_files = {category: [] for category in CATEGORIES}
    categorized_files['Other'] = [] # For files that don't match

    for file_meta in all_files_metadata:
        assigned = False
        for category, keywords in CATEGORIES.items():
            # Check if any of the file's tags match the category's keywords
            if any(keyword in file_meta.tags for keyword in keywords):
                categorized_files[category].append(file_meta)
                assigned = True
                break # Move to the next file once it's assigned
        if not assigned:
            categorized_files['Other'].append(file_meta)

    # Remove empty categories from the final dict
    final_categorized_files = {k: v for k, v in categorized_files.items() if v}

    return render_template('index.html', categorized_files=final_categorized_files, title="Your Smart Dashboard")
# --- ADD THIS ENTIRE FUNCTION ---
@app.route('/search')
@login_required
def search():
    # Get the search term from the URL (e.g., /search?query=receipt)
    query = request.args.get('query', '')

    # If the query is empty, just go back to the main page
    if not query:
        return redirect(url_for('index'))

    # Search the database for metadata where the tags column contains the query
    # The '%' are wildcards, making it a flexible search
    search_term = f"%{query}%"
    results = FileMetadata.query.filter_by(user_id=current_user.id).filter(FileMetadata.tags.like(search_term)).all()

    # Create a dynamic title for the results page
    result_title = f"Search Results for: '{query}'"

    # Reuse the same index.html template to display the filtered results
    return render_template('index.html', files=results, title=result_title)
# ... rest of your code ...
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    file_path = os.path.join(user_folder, file.filename)
    file.save(file_path)

    # --- AI ANALYSIS STEP ---
    tags = analyze_file(file_path)
    if tags:
        existing_metadata = FileMetadata.query.filter_by(filename=file.filename, user_id=current_user.id).first()
        if not existing_metadata:
            new_metadata = FileMetadata(
                filename=file.filename,
                tags=','.join(tags), # Convert list of tags to a single string
                user_id=current_user.id
            )
            db.session.add(new_metadata)
            db.session.commit()

    flash(f"File '{file.filename}' uploaded and analyzed successfully!", 'success')
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
    return send_from_directory(user_folder, filename)

@app.route("/delete/<filename>", methods=["POST"])
@login_required
def delete_file(filename):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
    file_path = os.path.join(user_folder, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

        # --- DELETE METADATA STEP ---
        metadata_to_delete = FileMetadata.query.filter_by(filename=filename, user_id=current_user.id).first()
        if metadata_to_delete:
            db.session.delete(metadata_to_delete)
            db.session.commit()

        flash(f"File '{filename}' was successfully deleted.", 'success')
    else:
        flash('Error: File not found.', 'error')
    return redirect(url_for("index"))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
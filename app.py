from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import secrets
from ai_utils import analyze_file, find_semantic_matches, categorize_files_with_ai

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
    share_token = db.Column(db.String(32), unique=True, nullable=True)

# --- FLASK-LOGIN USER LOADER ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- AUTHENTICATION ROUTES ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please enter both username and password.', 'error')
                return render_template('signup.html')
            
            if len(username) < 3:
                flash('Username must be at least 3 characters long.', 'error')
                return render_template('signup.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
                return render_template('signup.html')
            
            user = User.query.filter_by(username=username).first()
            if user:
                flash('Username already exists. Please choose another one.', 'error')
                return render_template('signup.html')
            
            new_user = User(
                username=username,
                password=generate_password_hash(password, method='pbkdf2:sha256')
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Signup error: {e}")
            flash('An error occurred during signup. Please try again.', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please enter both username and password.', 'error')
                return render_template('login.html')
            
            user = User.query.filter_by(username=username).first()
            
            if not user or not check_password_hash(user.password, password):
                flash('Invalid username or password. Please try again.', 'error')
                return render_template('login.html')
            
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login. Please try again.', 'error')
            return render_template('login.html')
    
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
    # Check if we're viewing a specific folder
    folder_name = request.args.get('folder')
    
    # Get all files for the current user
    all_files_metadata = FileMetadata.query.filter_by(user_id=current_user.id).all()
    
    if folder_name:
        # Show specific folder view
        print(f"DEBUG: Viewing folder: {folder_name}")
        
        # Get categorized files
        categorized_filenames = categorize_files_with_ai(all_files_metadata)
        
        # Get files for the specific folder
        folder_files = []
        if folder_name in categorized_filenames:
            folder_files = [
                meta for meta in all_files_metadata 
                if meta.filename in categorized_filenames[folder_name]
            ]
        
        return render_template('index.html', 
                             viewing_folder=True,
                             folder_name=folder_name,
                             folder_files=folder_files,
                             title=f"Files in {folder_name}")
    else:
        # Show main dashboard with all categorized folders
        print(f"DEBUG: Showing main dashboard with {len(all_files_metadata)} files")
        
        categorized_filenames = categorize_files_with_ai(all_files_metadata)
        final_categorized_files = {}
        
        for category, filenames in categorized_filenames.items():
            final_categorized_files[category] = [
                meta for meta in all_files_metadata if meta.filename in filenames
            ]
        
        return render_template('index.html', 
                             viewing_folder=False,
                             categorized_files=final_categorized_files, 
                             title="Your Smart Dashboard")

@app.route('/search')
@login_required
def search():
    query = request.args.get('query', '')
    if not query:
        return redirect(url_for('index'))
    
    all_files_metadata = FileMetadata.query.filter_by(user_id=current_user.id).all()
    matching_filenames = find_semantic_matches(query, all_files_metadata)
    results = [meta for meta in all_files_metadata if meta.filename in matching_filenames]
    
    categorized_results = {f"Search Results for: '{query}'": results}
    
    return render_template('index.html', 
                         viewing_folder=False,
                         categorized_files=categorized_results, 
                         title="Search Results")

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
    
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    file_path = os.path.join(user_folder, file.filename)
    file.save(file_path)
    
    # Analyze file with AI
    tags = analyze_file(file_path)
    
    if tags:
        # Check if file metadata already exists
        existing_metadata = FileMetadata.query.filter_by(
            filename=file.filename, 
            user_id=current_user.id
        ).first()
        
        if not existing_metadata:
            new_metadata = FileMetadata(
                filename=file.filename,
                tags=','.join(tags),
                user_id=current_user.id
            )
            db.session.add(new_metadata)
            db.session.commit()
        else:
            # Update existing metadata
            existing_metadata.tags = ','.join(tags)
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
        
        # Remove from database
        metadata_to_delete = FileMetadata.query.filter_by(
            filename=filename, 
            user_id=current_user.id
        ).first()
        
        if metadata_to_delete:
            db.session.delete(metadata_to_delete)
            db.session.commit()
        
        flash(f"File '{filename}' was successfully deleted.", 'success')
    else:
        flash('Error: File not found.', 'error')
    
    return redirect(url_for("index"))

# --- FILE SHARING ROUTES ---
@app.route('/share/<int:file_id>', methods=['POST'])
@login_required
def share_file(file_id):
    file_meta = FileMetadata.query.get_or_404(file_id)
    
    if file_meta.user_id != current_user.id:
        flash('You do not have permission to share this file.', 'error')
        return redirect(url_for('index'))
    
    if not file_meta.share_token:
        file_meta.share_token = secrets.token_urlsafe(16)
        db.session.commit()
    
    share_link = url_for('shared_file', token=file_meta.share_token, _external=True)
    flash(f"Shareable Link: {share_link}", 'info')
    return redirect(url_for('index'))

@app.route('/shared/<token>')
def shared_file(token):
    file_meta = FileMetadata.query.filter_by(share_token=token).first_or_404()
    return render_template('shared_file.html', filename=file_meta.filename, token=token)

@app.route('/download_shared/<token>')
def download_shared_file(token):
    file_meta = FileMetadata.query.filter_by(share_token=token).first_or_404()
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(file_meta.user_id))
    return send_from_directory(user_folder, file_meta.filename)

# --- DEBUG AND UTILITY ROUTES ---
@app.route('/debug')
@login_required
def debug():
    files = FileMetadata.query.filter_by(user_id=current_user.id).all()
    debug_info = {
        'user_id': current_user.id,
        'total_files': len(files),
        'files': [{'filename': f.filename, 'tags': f.tags} for f in files]
    }
    return f"<pre>{debug_info}</pre>"

@app.route('/debug-auth')
def debug_auth():
    return f"""
    <h2>Auth Debug Info</h2>
    <p>Current User: {current_user if current_user.is_authenticated else 'Not logged in'}</p>
    <p>Session: {dict(session)}</p>
    <p>Request Method: {request.method}</p>
    <p>Request URL: {request.url}</p>
    <p>User Agent: {request.headers.get('User-Agent')}</p>
    <a href="{url_for('login')}">Go to Login</a><br>
    <a href="{url_for('signup')}">Go to Signup</a>
    """

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': 'Personal Cloud API is running'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
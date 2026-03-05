from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from ai_utils import analyze_file, find_semantic_matches, categorize_by_tags_simple
import os
import secrets
import boto3
from botocore.exceptions import ClientError

# Load environment variables from .env file
load_dotenv()

# --- S3 CONFIGURATION ---
USE_S3 = os.environ.get('USE_S3', 'false').lower() == 'true'
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')

s3_client = None
if USE_S3:
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=AWS_REGION
        )
        print("✅ S3 client initialized successfully for bucket:", S3_BUCKET)
    except Exception as e:
        print("⚠️ S3 client initialization error:", e)
        s3_client = None
else:
    print("💻 S3 disabled — using local storage")

app = Flask(__name__)

# --- CONFIGURATION ---
# Check if running on Render (production) or locally (development)
if os.environ.get('RENDER'):
    # 🚀 PRODUCTION MODE (on Render)
    print("🚀 Running in PRODUCTION mode on Render")
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    
    # Use PostgreSQL database from Render
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Fix for SQLAlchemy compatibility
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    
    # Use /tmp folder for uploads (Render's temporary storage)
    UPLOAD_FOLDER = '/tmp/uploads'
    
else:
    # 💻 DEVELOPMENT MODE (on your computer)
    print("💻 Running in DEVELOPMENT mode")
    
    app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    UPLOAD_FOLDER = 'uploads'

# Common configuration for both environments
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"📁 Created upload folder: {UPLOAD_FOLDER}")

# --- DATABASE & LOGIN MANAGER SETUP ---
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Increased for modern hash lengths
    files = db.relationship('FileMetadata', backref='owner', lazy=True)

class FileMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    s3_key = db.Column(db.String(500), nullable=True)  # NEW: stores S3 path
    tags = db.Column(db.String(500))
    category = db.Column(db.String(100), nullable=True)  # Permanent category storage
    file_size = db.Column(db.Integer, nullable=True, default=0)  # File size in bytes
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
    
    # Calculate storage stats
    total_files = len(all_files_metadata)
    total_size = 0
    
    # Calculate total storage used
    # Calculate storage from database (works with S3)
    total_size = db.session.query(db.func.sum(FileMetadata.file_size)).filter_by(user_id=current_user.id).scalar() or 0
    
    # Format storage size
    def format_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    storage_used = format_size(total_size)
    storage_limit = "50 MB"  # Display limit
    storage_percent = min((total_size / (50 * 1024 * 1024)) * 100, 100)  # 50MB limit for display
    
    # Build categories from stored category column (NO AI CALL!)
    categorized_files = {}
    for file_meta in all_files_metadata:
        category = file_meta.category or "Uncategorized"
        if category not in categorized_files:
            categorized_files[category] = []
        categorized_files[category].append(file_meta)
    
    # Count files per category for stats
    category_stats = {cat: len(files) for cat, files in categorized_files.items()}
    
    if folder_name:
        # Show specific folder view
        print(f"DEBUG: Viewing folder: {folder_name}")
        folder_files = categorized_files.get(folder_name, [])
        
        return render_template('index.html', 
                             viewing_folder=True,
                             folder_name=folder_name,
                             folder_files=folder_files,
                             title=f"Files in {folder_name}",
                             total_files=total_files,
                             storage_used=storage_used,
                             storage_limit=storage_limit,
                             storage_percent=storage_percent,
                             category_stats=category_stats)
    else:
        # Show main dashboard with all categorized folders
        print(f"DEBUG: Showing main dashboard with {len(all_files_metadata)} files")
        
        return render_template('index.html', 
                             viewing_folder=False,
                             categorized_files=categorized_files, 
                             title="Your Smart Dashboard",
                             total_files=total_files,
                             storage_used=storage_used,
                             storage_limit=storage_limit,
                             storage_percent=storage_percent,
                             category_stats=category_stats)

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
    
    # Save to temp local folder for AI analysis
    temp_filename = secrets.token_hex(8) + "_" + file.filename
    temp_path = os.path.join(user_folder, temp_filename)
    file.save(temp_path)
    
    # Get file size
    file_size = os.path.getsize(temp_path)
    
    s3_key = None
    try:
        # If S3 enabled, upload to S3
        if USE_S3 and s3_client and S3_BUCKET:
            s3_key = f"user_{current_user.id}/{secrets.token_hex(12)}_{file.filename}"
            file.seek(0)  # Reset file pointer
            s3_client.upload_fileobj(
                file,
                S3_BUCKET,
                s3_key,
                ExtraArgs={'ContentType': file.content_type}
            )
            print(f"✅ File uploaded to S3: {s3_key}")
        
        # Analyze file with AI (from local temp copy) - returns {tags, category}
        analysis_result = analyze_file(temp_path)
        tags = analysis_result.get('tags') if analysis_result else None
        category = analysis_result.get('category', 'Uncategorized') if analysis_result else 'Uncategorized'
        
        print(f"📦 Saving file: {file.filename}")
        print(f"   Tags: {tags}")
        print(f"   Category: {category}")
        
        # Save metadata
        existing_metadata = FileMetadata.query.filter_by(
            filename=file.filename, 
            user_id=current_user.id
        ).first()
        
        if not existing_metadata:
            new_metadata = FileMetadata(
                filename=file.filename,
                s3_key=s3_key,  # Store S3 key
                tags=','.join(tags) if tags else '',
                category=category,  # Store category permanently
                file_size=file_size,  # Store file size
                user_id=current_user.id
            )
            db.session.add(new_metadata)
        else:
            existing_metadata.tags = ','.join(tags) if tags else existing_metadata.tags
            existing_metadata.category = category  # Update category
            existing_metadata.file_size = file_size  # Update file size
            if s3_key:
                existing_metadata.s3_key = s3_key
        
        db.session.commit()
        flash(f"File '{file.filename}' uploaded and analyzed successfully!", 'success')
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        flash(f'Upload failed: {str(e)}', 'error')
    finally:
        # Clean up temp file with retry (file may be locked)
        import gc
        gc.collect()  # Force garbage collection to release file handles
        import time
        for attempt in range(3):
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                break
            except PermissionError:
                time.sleep(0.5)  # Wait and retry
    
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    file_meta = FileMetadata.query.filter_by(filename=filename, user_id=current_user.id).first_or_404()
    
    # If S3 enabled and file has S3 key, generate presigned URL
    if USE_S3 and file_meta.s3_key and s3_client:
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': file_meta.s3_key},
                ExpiresIn=3600  # URL valid for 1 hour
            )
            return redirect(url)
        except ClientError as e:
            print(f"❌ S3 presign error: {e}")
            flash('Could not retrieve file from storage.', 'error')
            return redirect(url_for('index'))
    else:
        # Fallback to local storage
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
        return send_from_directory(user_folder, filename)

@app.route("/delete/<filename>", methods=["POST"])
@login_required
def delete_file(filename):
    metadata_to_delete = FileMetadata.query.filter_by(
        filename=filename, 
        user_id=current_user.id
    ).first()
    
    if not metadata_to_delete:
        flash('Error: File not found.', 'error')
        return redirect(url_for("index"))
    
    # Delete from S3 if exists
    if USE_S3 and metadata_to_delete.s3_key and s3_client:
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=metadata_to_delete.s3_key)
            print(f"✅ File deleted from S3: {metadata_to_delete.s3_key}")
        except ClientError as e:
            print(f"❌ S3 delete error: {e}")
            flash('Could not delete file from cloud storage.', 'error')
            return redirect(url_for('index'))
    else:
        # Fallback to local delete
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
        file_path = os.path.join(user_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Delete from database
    db.session.delete(metadata_to_delete)
    db.session.commit()
    
    flash(f"File '{filename}' was successfully deleted.", 'success')
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
    
    # If S3 enabled and file has S3 key, generate presigned URL
    if USE_S3 and file_meta.s3_key and s3_client:
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': file_meta.s3_key},
                ExpiresIn=3600
            )
            return redirect(url)
        except ClientError as e:
            print(f"❌ S3 shared presign error: {e}")
            return "Error: Could not retrieve shared file.", 404
    else:
        # Fallback to local storage
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(file_meta.user_id))
        return send_from_directory(user_folder, file_meta.filename)

# --- DEBUG ROUTES ---
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': 'Personal Cloud API is running'}

@app.route('/init-db')
def init_database():
    """Initialize database tables - run this once after deployment"""
    try:
        db.create_all()
        return "✅ Database tables created successfully!", 200
    except Exception as e:
        return f"❌ Error creating tables: {str(e)}", 500

# --- S3 DEBUG ROUTES (temporary, for testing) ---
@app.route('/test-s3-upload', methods=['POST'])
@login_required
def test_s3_upload():
    """Test route to upload a file to S3"""
    if not USE_S3 or not s3_client or not S3_BUCKET:
        return "❌ S3 not enabled or misconfigured", 400
    
    if 'file' not in request.files:
        return "❌ No file provided", 400
    
    file = request.files['file']
    if file.filename == '':
        return "❌ Empty filename", 400
    
    try:
        s3_key = f"user_{current_user.id}/{secrets.token_hex(12)}_{file.filename}"
        
        file.seek(0)
        s3_client.upload_fileobj(
            file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        print(f"✅ File uploaded to S3: {s3_key}")
        return f"✅ File uploaded to S3 successfully!\nS3 Key: {s3_key}", 200
        
    except ClientError as e:
        print(f"❌ S3 upload error: {e}")
        return f"❌ S3 upload failed: {e}", 500

@app.route('/test-s3-list', methods=['GET'])
@login_required
def test_s3_list():
    """Test route to list objects in S3 bucket"""
    if not USE_S3 or not s3_client or not S3_BUCKET:
        return "❌ S3 not enabled or misconfigured", 400
    
    try:
        resp = s3_client.list_objects_v2(Bucket=S3_BUCKET, MaxKeys=100)
        items = resp.get('Contents', [])
        
        if not items:
            return "<pre>✅ S3 bucket is empty (no objects yet)</pre>"
        
        lines = [f"{obj['Key']}  —  {obj['Size']} bytes  —  {obj['LastModified']}" for obj in items]
        html = "<pre>✅ S3 Objects in bucket:\n" + "\n".join(lines) + "</pre>"
        return html
        
    except ClientError as e:
        print(f"❌ S3 list error: {e}")
        return f"❌ S3 list failed: {e}", 500

@app.route('/migrate-add-s3-key')
def migrate_add_s3_key():
    """Add s3_key column to file_metadata table if it doesn't exist"""
    try:
        with db.engine.connect() as conn:
            # SQLite doesn't support IF NOT EXISTS, so try-catch
            try:
                conn.execute(db.text("ALTER TABLE file_metadata ADD COLUMN s3_key VARCHAR(500)"))
                conn.commit()
            except Exception:
                return "✅ s3_key column already exists", 200
        return "✅ Migration successful: s3_key column added to file_metadata table", 200
    except Exception as e:
        return f"❌ Migration failed: {str(e)}", 500


@app.route('/migrate-add-category')
def migrate_add_category():
    """Add category column to file_metadata table if it doesn't exist"""
    try:
        with db.engine.connect() as conn:
            # SQLite doesn't support IF NOT EXISTS, so try-catch
            try:
                conn.execute(db.text("ALTER TABLE file_metadata ADD COLUMN category VARCHAR(100)"))
                conn.commit()
            except Exception:
                return "✅ category column already exists", 200
        return "✅ Migration successful: category column added to file_metadata table", 200
    except Exception as e:
        return f"❌ Migration failed: {str(e)}", 500


@app.route('/migrate-add-filesize')
def migrate_add_filesize():
    """Add file_size column to file_metadata table if it doesn't exist"""
    try:
        with db.engine.connect() as conn:
            try:
                conn.execute(db.text("ALTER TABLE file_metadata ADD COLUMN file_size INTEGER DEFAULT 0"))
                conn.commit()
            except Exception:
                return "✅ file_size column already exists", 200
        return "✅ Migration successful: file_size column added to file_metadata table", 200
    except Exception as e:
        return f"❌ Migration failed: {str(e)}", 500


@app.route('/migrate-categories')
@login_required
def migrate_categories():
    """Assign categories to files that don't have one (based on existing tags)"""
    try:
        # Get all files without a category for current user
        files_without_category = FileMetadata.query.filter_by(user_id=current_user.id).filter(
            (FileMetadata.category == None) | (FileMetadata.category == '')
        ).all()
        
        if not files_without_category:
            return "✅ All files already have categories assigned!", 200
        
        updated_count = 0
        for file_meta in files_without_category:
            # Use simple rule-based categorization from existing tags
            category = categorize_by_tags_simple(file_meta.tags)
            file_meta.category = category
            updated_count += 1
        
        db.session.commit()
        return f"✅ Migration successful! Assigned categories to {updated_count} files.", 200
    except Exception as e:
        return f"❌ Migration failed: {str(e)}", 500


# --- DATABASE INITIALIZATION ---
# This runs for BOTH Gunicorn (production) and direct execution (development)
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created!")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")
        # Re-raise to prevent app from running with broken database
        raise

if __name__ == '__main__':
    app.run(debug=True)
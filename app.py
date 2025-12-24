from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import json
import os
import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import timedelta
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Random secret key for better security
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Email Configuration - UPDATE THESE WITH YOUR ACTUAL EMAIL SETTINGS
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # For Gmail, change for other providers
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vignesh2604.m@gmail.com'  # REPLACE WITH YOUR EMAIL
app.config['MAIL_PASSWORD'] = 'bgit bnbt vdga umse'  # REPLACE WITH YOUR APP PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@arch-ai.com'
app.config['ARCH_AI_ADMIN_EMAIL'] = 'admin@arch-ai.com'  # Admin email for contact form

# Initialize Flask-Mail
mail = Mail(app)

# Data file paths
USERS_FILE = 'data/users.json'
USERLOGS_FILE = 'data/userlogs.json'
PROJECTS_FILE = 'data/projects.json'
CONTACT_FILE = 'data/contact_inquiries.json'
FLOOR_PLANS_FILE = 'data/floor_plans.json'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def init_data_files():
    """Initialize JSON files if they don't exist"""
    for file_path, default_data in [
        (USERS_FILE, []),
        (USERLOGS_FILE, {}),
        (PROJECTS_FILE, {}),
        (CONTACT_FILE, []),
        (FLOOR_PLANS_FILE, {})
    ]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f)

# Initialize data files
init_data_files()

# ========== HELPER FUNCTIONS ==========
def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def load_db():
    """Load database (projects) - for compatibility"""
    return load_projects()

def normalize_email(email):
    """Normalize email to lowercase for case-insensitive comparison"""
    if email:
        return email.strip().lower()
    return email

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_welcome_email(user_email, user_name):
    """Send welcome email to new user"""
    try:
        msg = Message(
            subject='Welcome to ARCH-AI Neural Architecture Studio!',
            recipients=[user_email],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        msg.body = f"""
Dear {user_name},

Welcome to ARCH-AI Neural Architecture Studio!

Your account has been successfully created. You now have access to our complete suite of AI-powered architectural tools:

• Soil Analytics & Geological Intelligence
• Automated Foundation Specifications
• Neural Floor Planning
• Generative 3D Blueprints

Getting Started:
1. Log in to your workspace
2. Create your first project using the Soil Analytics portal
3. Generate AI-powered floor plans
4. Export professional reports

Need help? Our support team is available at support@arch-ai.com

Best regards,
The ARCH-AI Team
        """
        
        msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4A6741; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .footer {{ background-color: #080808; color: #A0A0A0; padding: 20px; text-align: center; font-size: 12px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #4A6741; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to ARCH-AI</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>Your account has been successfully created. Welcome to our neural architecture studio!</p>
            
            <h3>🚀 Getting Started:</h3>
            <ol>
                <li>Log in to your workspace</li>
                <li>Create your first project using Soil Analytics</li>
                <li>Generate AI-powered floor plans</li>
                <li>Export professional reports</li>
            </ol>
            
            <a href="#" class="button">Access Your Workspace</a>
            
            <h3>📞 Need Help?</h3>
            <p>Our support team is available at <a href="mailto:support@arch-ai.com">support@arch-ai.com</a></p>
        </div>
        <div class="footer">
            <p>&copy; 2025 ARCH-AI Systems. All rights reserved.</p>
            <p>This is an automated message, please do not reply directly to this email.</p>
        </div>
    </div>
</body>
</html>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False

def send_contact_notification(user_email, user_name, message_text):
    """Send contact form notification to admin"""
    try:
        msg = Message(
            subject=f'New Contact Inquiry from {user_name}',
            recipients=[app.config['ARCH_AI_ADMIN_EMAIL']],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.body = f"""
New Contact Form Submission:

Name: {user_name}
Email: {user_email}
Message: {message_text}

Timestamp: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        
        msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4A6741; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .info-box {{ background-color: white; border-left: 4px solid #4A6741; padding: 15px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Contact Inquiry</h1>
        </div>
        <div class="content">
            <h2>Contact Form Submission</h2>
            
            <div class="info-box">
                <h3>Contact Details:</h3>
                <p><strong>Name:</strong> {user_name}</p>
                <p><strong>Email:</strong> <a href="mailto:{user_email}">{user_email}</a></p>
                <p><strong>Timestamp:</strong> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            
            <div class="info-box">
                <h3>Message:</h3>
                <p>{message_text}</p>
            </div>
            
            <p>This inquiry was submitted via the ARCH-AI website contact form.</p>
        </div>
    </div>
</body>
</html>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending contact notification: {e}")
        return False

# ========== CUSTOM JINJA2 FILTERS ==========
@app.template_filter('round_coordinate')
def round_coordinate_filter(value, decimals=4):
    """Safely round coordinate values"""
    if value is None:
        return value
    try:
        # Handle both string and float values
        return round(float(value), decimals)
    except (ValueError, TypeError):
        return value

@app.template_filter('format_float')
def format_float_filter(value, decimals=4):
    """Format float with specified decimals"""
    if value is None:
        return value
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return value

# ========== AUTHENTICATION DECORATORS ==========
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Make session permanent and set timeout
@app.before_request
def make_session_permanent():
    session.permanent = True

def load_users():
    """Load users from JSON file"""
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_userlogs():
    """Load user logs from JSON file"""
    try:
        with open(USERLOGS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_userlogs(userlogs):
    """Save user logs to JSON file"""
    with open(USERLOGS_FILE, 'w') as f:
        json.dump(userlogs, f, indent=2)

def load_projects():
    """Load projects from JSON file"""
    try:
        with open(PROJECTS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_projects(projects):
    """Save projects to JSON file"""
    with open(PROJECTS_FILE, 'w') as f:
        json.dump(projects, f, indent=2)

def load_floor_plans():
    """Load floor plans from JSON file"""
    try:
        with open(FLOOR_PLANS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_floor_plans(floor_plans):
    """Save floor plans to JSON file"""
    with open(FLOOR_PLANS_FILE, 'w') as f:
        json.dump(floor_plans, f, indent=2)

def load_contact_inquiries():
    """Load contact inquiries from JSON file"""
    try:
        with open(CONTACT_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_contact_inquiries(inquiries):
    """Save contact inquiries to JSON file"""
    with open(CONTACT_FILE, 'w') as f:
        json.dump(inquiries, f, indent=2)

def log_user_activity(user_email, action, project_name=None, details=None):
    """Log user activity to userlogs.json"""
    userlogs = load_userlogs()
    
    if user_email not in userlogs:
        userlogs[user_email] = []
    
    log_entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'action': action,
        'project_name': project_name,
        'details': details
    }
    
    userlogs[user_email].append(log_entry)
    
    # Keep only last 100 logs per user
    if len(userlogs[user_email]) > 100:
        userlogs[user_email] = userlogs[user_email][-100:]
    
    save_userlogs(userlogs)

def generate_floor_plan_description(project_data):
    """Generate floor plan description based on project data"""
    typology = project_data.get('typology', 'Residential').lower()
    storeys = project_data.get('storeys', 2)
    units = project_data.get('units', 5)
    
    descriptions = {
        'residential': [
            f"Residential floor plan optimized for {units} units across {storeys} storeys. Features open-concept living areas with efficient circulation.",
            f"Modern residential layout with {units} units per floor. Includes private balconies and shared amenity spaces.",
            f"Functional residential design maximizing natural light. Each unit features private outdoor space and flexible room configurations."
        ],
        'commercial': [
            f"Commercial office layout for {storeys} storeys with open-plan workspaces, meeting rooms, and collaborative zones.",
            f"Retail-commercial mixed-use design with ground-floor retail and upper-floor offices.",
            f"Corporate office layout featuring centralized core services and perimeter offices with views."
        ],
        'industrial': [
            f"Industrial facility design with clear-span spaces, loading docks, and administrative offices.",
            f"Warehouse layout optimized for logistics with high ceilings and efficient material flow.",
            f"Manufacturing facility with production zones, quality control areas, and staff amenities."
        ]
    }
    
    # Select appropriate description based on typology
    typology_key = 'residential'  # default
    for key in descriptions:
        if key in typology:
            typology_key = key
            break
    
    import random
    desc_list = descriptions.get(typology_key, descriptions['residential'])
    return desc_list[0]  # Return first description for consistency

def check_duplicate_project(user_email, project_name, project_id=None):
    """Check if project with same name already exists for user"""
    projects_data = load_projects()
    user_projects = projects_data.get(user_email, [])
    
    for project in user_projects:
        # Skip the current project if we're checking for updates
        if project_id and project.get('id') == project_id:
            continue
            
        if project.get('name') == project_name:
            return True, project.get('id')
    
    return False, None

# ========== ROUTES ==========
@app.route('/')
def index():
    # If user is logged in, redirect to workspace
    if 'user_email' in session:
        return redirect(url_for('workspace'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing session when accessing login page
    if request.method == 'GET':
        # Clear session to force fresh login
        if 'user_email' in session:
            session.clear()
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Normalize email for case-insensitive comparison
        normalized_email = normalize_email(email)
        
        users = load_users()
        user = next((u for u in users if normalize_email(u['email']) == normalized_email), None)
        
        if user and check_password_hash(user['password'], password):
            session['user_email'] = user['email']  # Use stored email (preserves case)
            session['user_name'] = user['name']
            session['user_id'] = user['id']
            
            log_user_activity(user['email'], 'login')
            flash('Login successful!', 'success')
            return redirect(url_for('workspace'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Validate input
    if not name or not email or not password:
        flash('All fields are required', 'error')
        return redirect(url_for('login'))
    
    if len(password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('login'))
    
    # Validate email format
    if not is_valid_email(email):
        flash('Please enter a valid email address', 'error')
        return redirect(url_for('login'))
    
    # Normalize email for case-insensitive comparison
    normalized_email = normalize_email(email)
    
    users = load_users()
    
    # Check if user already exists (case-insensitive)
    if any(normalize_email(u['email']) == normalized_email for u in users):
        flash('Email already registered. Please use a different email or log in.', 'error')
        return redirect(url_for('login'))
    
    # Create new user
    new_user = {
        'id': str(uuid.uuid4()),
        'name': name,
        'email': email,  # Store as entered (preserves case for display)
        'password': generate_password_hash(password),
        'created_at': datetime.datetime.now().isoformat(),
        'firm_name': '',  # Can be updated later
        'subscription': 'free'
    }
    
    users.append(new_user)
    save_users(users)
    
    # Initialize user logs
    log_user_activity(email, 'account_created')
    
    # Send welcome email
    if send_welcome_email(email, name):
        flash('Account created successfully! Welcome email sent.', 'success')
    else:
        flash('Account created successfully! (Welcome email could not be sent)', 'warning')
    
    return redirect(url_for('login'))

@app.route('/contact-submit', methods=['POST'])
def contact_submit():
    """Handle contact form submissions from homepage"""
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    message = request.form.get('message')
    
    # Validate inputs
    if not full_name or not email or not message:
        flash('All fields are required', 'error')
        return redirect(url_for('index'))
    
    if not is_valid_email(email):
        flash('Please enter a valid email address', 'error')
        return redirect(url_for('index'))
    
    # Load existing inquiries
    inquiries = load_contact_inquiries()
    
    # Create new inquiry
    new_inquiry = {
        'id': str(uuid.uuid4()),
        'full_name': full_name,
        'email': email,
        'message': message,
        'timestamp': datetime.datetime.now().isoformat(),
        'status': 'new'
    }
    
    inquiries.append(new_inquiry)
    save_contact_inquiries(inquiries)
    
    # Send notification to admin
    if send_contact_notification(email, full_name, message):
        flash('Thank you for your inquiry! We have received your message and will contact you soon.', 'success')
    else:
        flash('Thank you for your inquiry! Your message has been saved.', 'success')
    
    return redirect(url_for('index'))

@app.route('/workspace')
@login_required
def workspace():
    # Load user's projects
    projects_data = load_projects()
    user_email = session['user_email']
    
    user_projects = projects_data.get(user_email, [])
    
    # Log access
    log_user_activity(user_email, 'accessed_workspace')
    
    return render_template('workspace.html', 
                         user_name=session['user_name'],
                         projects=user_projects)

@app.route('/soil-analyze', methods=['GET', 'POST'])
@login_required
def soil_analyze():
    project_id = request.args.get('edit')
    project = None
    
    # If editing existing project
    if project_id:
        projects_data = load_projects()
        user_email = session['user_email']
        user_projects = projects_data.get(user_email, [])
        project = next((p for p in user_projects if p['id'] == project_id), None)
    
    if request.method == 'POST':
        # Check for duplicate project name
        user_email = session['user_email']
        project_name = request.form.get('project_name')
        existing_project_id = request.form.get('project_id')
        
        is_duplicate, duplicate_id = check_duplicate_project(user_email, project_name, existing_project_id)
        
        if is_duplicate:
            flash(f'Project "{project_name}" already exists!', 'error')
            return render_template('soil_analyze.html', project=project)
        
        # Use existing project ID or create new
        if existing_project_id:
            project_id = existing_project_id
            is_new = False
        else:
            project_id = str(uuid.uuid4())
            is_new = True
        
        # Collect all form data - convert coordinates to float
        project_data = {
            'id': project_id,
            'name': project_name,
            'typology': request.form.get('structural_typology'),
            'storeys': int(request.form.get('storey_count', 0)) if request.form.get('storey_count') else 0,
            'width': safe_float(request.form.get('width')),
            'height': safe_float(request.form.get('height')),
            'material': request.form.get('primary_materiality'),
            'units': int(request.form.get('internal_units', 0)) if request.form.get('internal_units') else 0,
            'latitude': safe_float(request.form.get('latitude')),
            'longitude': safe_float(request.form.get('longitude')),
            'updated_at': datetime.datetime.now().isoformat(),
            'status': 'In Analysis',
            'soil_composition': {},
            'recommendations': {},
            'blueprints': []
        }
        
        if is_new:
            project_data['created_at'] = datetime.datetime.now().isoformat()
        
        # Handle file upload
        if 'schematic_file' in request.files:
            file = request.files['schematic_file']
            if file.filename:
                # Save file (in production, use secure_filename and proper storage)
                filename = f"{project_id}_{file.filename}"
                os.makedirs('uploads', exist_ok=True)
                file.save(f"uploads/{filename}")
                project_data['schematic_file'] = filename
        
        # Save project to database
        projects_data = load_projects()
        user_email = session['user_email']
        
        if user_email not in projects_data:
            projects_data[user_email] = []
        
        if is_new:
            projects_data[user_email].append(project_data)
            action_msg = 'created'
        else:
            # Update existing project
            for i, p in enumerate(projects_data[user_email]):
                if p['id'] == project_id:
                    projects_data[user_email][i] = project_data
                    break
            action_msg = 'updated'
        
        save_projects(projects_data)
        
        # Store current project in session
        session['current_project_id'] = project_id
        session['current_project_name'] = project_name
        
        # Log activity
        log_user_activity(user_email, f'{action_msg}_project', 
                         project_name, 
                         f"Typology: {project_data['typology']}")
        
        flash(f'Project {action_msg} successfully!', 'success')
        return redirect(url_for('report', project_id=project_id))
    
    return render_template('soil_analyze.html', project=project)

@app.route('/report/<project_id>')
@login_required
def report(project_id):
    # Load project data
    projects_data = load_projects()
    user_email = session['user_email']
    
    user_projects = projects_data.get(user_email, [])
    project = next((p for p in user_projects if p['id'] == project_id), None)
    
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('workspace'))
    
    # Generate analysis if not already done
    if not project.get('soil_composition'):
        project['soil_composition'] = {
            'primary_layer': 'Dense Silty Sand (SM Type)',
            'water_table': '14.5 feet below finished grade',
            'bearing_capacity': '3,500 PSF',
            'seismic_category': 'D - High Risk'
        }
        
        project['recommendations'] = {
            'foundation_type': 'Deep Raft (Mat) Foundation',
            'reasons': [
                'Differential Settlement Mitigation',
                'Seismic Resilience',
                'Hydrostatic Load Balance'
            ]
        }
        
        # Update in database
        projects_data[user_email] = user_projects
        save_projects(projects_data)
    
    # Log activity
    log_user_activity(user_email, 'viewed_report', project['name'])
    
    # Add current date for report
    current_date = datetime.datetime.now().strftime("%b %d, %Y")
    
    return render_template('report.html', project=project, report_date=current_date)

@app.route('/floorplanner')
@login_required
def floorplanner():
    # Get project_id from query parameter or session
    project_id = request.args.get('project_id') or session.get('current_project_id')
    
    if not project_id:
        flash('No active project. Please create one first.', 'error')
        return redirect(url_for('soil_analyze'))
    
    # Set current project in session
    session['current_project_id'] = project_id
    
    # Load project data
    projects_data = load_projects()
    user_email = session['user_email']
    user_projects = projects_data.get(user_email, [])
    project = next((p for p in user_projects if p['id'] == project_id), None)
    
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('workspace'))
    
    # Generate floor plan description
    floor_plans = load_floor_plans()
    floor_plan_id = f"{project_id}_floor_plan"
    
    if floor_plan_id not in floor_plans:
        # Generate floor plan description based on project data
        floor_plan_description = generate_floor_plan_description(project)
        
        # Store the generated floor plan
        floor_plans[floor_plan_id] = {
            'project_id': project_id,
            'project_name': project.get('name', 'Unnamed Project'),
            'description': floor_plan_description,
            'generated_at': datetime.datetime.now().isoformat(),
            'ai_model': 'Static Generator'
        }
        
        save_floor_plans(floor_plans)
        
        # Update project with floor plan reference
        for i, p in enumerate(user_projects):
            if p['id'] == project_id:
                if 'floor_plans' not in p:
                    p['floor_plans'] = []
                p['floor_plans'].append({
                    'id': floor_plan_id,
                    'generated_at': datetime.datetime.now().isoformat()
                })
                projects_data[user_email][i] = p
                break
        
        save_projects(projects_data)
        
        # Log activity
        log_user_activity(user_email, 'generated_floor_plan', 
                         project.get('name'), 
                         'Static floor plan generated')
    
    # Get the floor plan
    floor_plan = floor_plans.get(floor_plan_id, {})
    
    # Log activity
    log_user_activity(session['user_email'], 'accessed_floorplanner')
    
    return render_template('floorplanner.html', project=project, floor_plan=floor_plan)

@app.route('/api/save-floor-plan', methods=['POST'])
@login_required
def save_floor_plan():
    """Save floor plan image to project data"""
    data = request.json
    image_url = data.get('image_url')
    
    if not image_url:
        return jsonify({'success': False, 'error': 'No image URL provided'})
    
    # Get current project ID from session
    project_id = session.get('current_project_id')
    if not project_id:
        return jsonify({'success': False, 'error': 'No active project'})
    
    # Load project data
    projects_data = load_projects()
    user_email = session['user_email']
    user_projects = projects_data.get(user_email, [])
    
    # Find and update project
    for i, project in enumerate(user_projects):
        if project['id'] == project_id:
            # Store the image URL in the project
            if 'floor_plan_images' not in project:
                project['floor_plan_images'] = []
            
            project['floor_plan_images'].append({
                'url': image_url,
                'generated_at': datetime.datetime.now().isoformat(),
                'type': 'ai_generated'
            })
            
            # Also store the latest image URL separately for easy access
            project['latest_floor_plan'] = image_url
            
            projects_data[user_email][i] = project
            break
    
    save_projects(projects_data)
    
    # Log activity
    log_user_activity(user_email, 'saved_floor_plan_image', 
                     project.get('name', 'Unknown Project'))
    
    return jsonify({'success': True, 'message': 'Floor plan saved successfully'})

@app.route('/final-report')
@login_required
def generate_final_report():
    project_id = session.get('current_project_id')
    if not project_id:
        flash('No active project.', 'error')
        return redirect(url_for('workspace'))
    
    # Load project data
    projects_data = load_projects()
    user_email = session['user_email']
    
    user_projects = projects_data.get(user_email, [])
    project = next((p for p in user_projects if p['id'] == project_id), None)
    
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('workspace'))
    
    # Update project status to completed
    for i, p in enumerate(user_projects):
        if p['id'] == project_id:
            user_projects[i]['status'] = 'Completed'
            user_projects[i]['completed_at'] = datetime.datetime.now().isoformat()
            break
    
    projects_data[user_email] = user_projects
    save_projects(projects_data)
    
    # Log activity
    log_user_activity(user_email, 'generated_final_report', project.get('name', 'Unknown Project'))
    
    # Add current date for report
    current_date = datetime.datetime.now().strftime("%b %d, %Y")
    
    return render_template('final_report.html', 
                         project=project, 
                         current_date=current_date)

@app.route('/final_report.html')
@login_required
def final_report_view():
    """Retrieve the latest project data to show in the report"""
    # Load database (projects)
    projects_data = load_projects()
    
    # Get user projects
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('login'))
    
    # Get projects for this user
    user_projects = projects_data.get(user_email, [])
    
    # Get the latest project
    latest_project = {}
    if user_projects:
        # Sort projects by created_at date, newest first
        sorted_projects = sorted(
            user_projects,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        latest_project = sorted_projects[0] if sorted_projects else {}
    
    # Add current date for report
    current_date = datetime.datetime.now().strftime("%b %d, %Y")
    
    return render_template('final_report.html', 
                         project=latest_project, 
                         current_date=current_date)

@app.route('/api/project/<project_id>/chat', methods=['POST'])
@login_required
def process_chat(project_id):
    """Handle chat interactions for floor planning"""
    data = request.json
    message = data.get('message', '')
    
    # Generate response based on message
    if 'kitchen' in message.lower():
        response = "Kitchen layout optimized for workflow efficiency with island counter and ample storage."
    elif 'bedroom' in message.lower():
        response = "Bedroom spaces designed for privacy and relaxation, with ensuite bathrooms where applicable."
    elif 'layout' in message.lower():
        response = "Open-concept layout maximizes natural light and facilitates seamless movement between spaces."
    elif 'modify' in message.lower() or 'change' in message.lower():
        response = "I'll adjust the floor plan based on your requirements while maintaining structural integrity."
    else:
        response = f"Processing your request: '{message}'. The design will be optimized for functionality and aesthetics."
    
    # Log chat interaction
    log_user_activity(session['user_email'], 'floorplanner_chat', 
                     project_name=project_id, 
                     details={'user_message': message[:100]})
    
    return jsonify({
        'response': response,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/project/<project_id>/delete', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """Delete a project"""
    projects_data = load_projects()
    user_email = session['user_email']
    
    if user_email in projects_data:
        # Find and remove the project
        user_projects = projects_data[user_email]
        project_to_delete = None
        
        for i, project in enumerate(user_projects):
            if project['id'] == project_id:
                project_to_delete = project
                user_projects.pop(i)
                break
        
        if project_to_delete:
            # Save updated projects
            projects_data[user_email] = user_projects
            save_projects(projects_data)
            
            # Log activity
            log_user_activity(user_email, 'deleted_project', project_to_delete['name'])
            
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Project not found'}), 404

@app.route('/api/project/<project_id>/update-status', methods=['POST'])
@login_required
def update_project_status(project_id):
    """Update project status"""
    data = request.json
    status = data.get('status')
    
    projects_data = load_projects()
    user_email = session['user_email']
    
    user_projects = projects_data.get(user_email, [])
    for i, project in enumerate(user_projects):
        if project['id'] == project_id:
            old_status = project.get('status', '')
            user_projects[i]['status'] = status
            
            projects_data[user_email] = user_projects
            save_projects(projects_data)
            
            log_user_activity(user_email, 'updated_project_status', 
                             project['name'], 
                             f"From {old_status} to {status}")
            
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Project not found'}), 404

@app.route('/api/project/<project_id>/generate-image', methods=['POST'])
@login_required
def generate_project_image(project_id):
    """Generate image for project"""
    # Load project data
    projects_data = load_projects()
    user_email = session['user_email']
    
    user_projects = projects_data.get(user_email, [])
    project = next((p for p in user_projects if p['id'] == project_id), None)
    
    if not project:
        return jsonify({'success': False, 'error': 'Project not found'}), 404
    
    # Use placeholder image URL
    image_url = "https://images.unsplash.com/photo-1574362848149-11496d93a7c7?auto=format&fit=crop&q=80&w=1000"
    
    # Store image reference in project
    for i, p in enumerate(user_projects):
        if p['id'] == project_id:
            if 'images' not in p:
                p['images'] = []
            p['images'].append({
                'url': image_url,
                'generated_at': datetime.datetime.now().isoformat(),
                'type': 'placeholder'
            })
            projects_data[user_email][i] = p
            break
    
    save_projects(projects_data)
    
    # Log activity
    log_user_activity(user_email, 'generated_project_image', project['name'])
    
    return jsonify({
        'success': True,
        'image_url': image_url,
        'message': 'Image placeholder generated'
    })

@app.route('/logout')
def logout():
    if 'user_email' in session:
        log_user_activity(session['user_email'], 'logout')
        session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/api/user/logs')
@login_required
def get_user_logs():
    """Get user activity logs (for dashboard)"""
    userlogs = load_userlogs()
    user_email = session['user_email']
    
    return jsonify({
        'logs': userlogs.get(user_email, [])[-20:]  # Last 20 activities
    })

# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create uploads directory
    os.makedirs('uploads', exist_ok=True)
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    app.run(debug=True, port=5000)
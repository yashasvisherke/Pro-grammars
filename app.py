from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import random

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Custom Jinja2 filters
@app.template_filter('avg')
def avg_filter(lst, attribute=None):
    if not lst:
        return 0
    if attribute:
        lst = [getattr(x, attribute) for x in lst]
    return sum(lst) / len(lst)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Question model
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)

# Interviewer model
class Interviewer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    personality = db.Column(db.String(50), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    model_path = db.Column(db.String(200), nullable=False)

# Interview model
class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    interviewer_id = db.Column(db.Integer, db.ForeignKey('interviewer.id'), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Float, default=0)  # in hours
    confidence_score = db.Column(db.Float, default=0)  # 0 to 1

    # Relationships
    user = db.relationship('User', backref='interviews')
    interviewer = db.relationship('Interviewer', backref='interviews')

# Create tables and initial data
with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    
    # Add default interviewers if none exist
    if not Interviewer.query.first():
        interviewers = [
            {
                'name': 'Dr. Alex Kumar',
                'personality': 'analytical',
                'specialization': 'data_structures_algorithms',
                'description': 'Algorithm Specialist with 10+ years at top tech companies',
                'model_path': 'interviewers/dsa_expert.jpg'
            },
            {
                'name': 'Emily Chen',
                'personality': 'systematic',
                'specialization': 'system_design',
                'description': 'Senior Software Engineer specializing in system architecture',
                'model_path': 'interviewers/system_design.jpg'
            },
            {
                'name': 'Sarah Wilson',
                'personality': 'empathetic',
                'specialization': 'behavioral',
                'description': 'HR Director with expertise in behavioral interviews',
                'model_path': 'interviewers/behavioral.jpg'
            },
            {
                'name': 'Dr. James Miller',
                'personality': 'analytical',
                'specialization': 'aptitude',
                'description': 'Mathematics Professor specializing in problem-solving',
                'model_path': 'interviewers/aptitude.jpg'
            }
        ]
        
        for interviewer_data in interviewers:
            interviewer = Interviewer(**interviewer_data)
            db.session.add(interviewer)
        
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
            
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # TODO: Handle contact form submission
        flash('Thank you for your message. We will get back to you soon!')
        return redirect(url_for('contact'))
    return render_template('contact.html')

class InterviewForm(FlaskForm):
    topic = SelectField('Select Topic', validators=[DataRequired()], choices=[
        ('data_structures_algorithms', 'Data Structures & Algorithms'),
        ('system_design', 'System Design'),
        ('behavioral', 'Behavioral'),
        ('aptitude', 'Aptitude')
    ])
    difficulty = SelectField('Select Difficulty', validators=[DataRequired()], choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ])
    num_interviewers = SelectField('Number of Interviewers', validators=[DataRequired()], choices=[
        ('1', '1 Interviewer'),
        ('2', '2 Interviewers'),
        ('3', '3 Interviewers')
    ])
    submit = SubmitField('Start Interview')

@app.route('/start-interview', methods=['GET', 'POST'])
def start_interview():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    form = InterviewForm()
    # Get interviewers for the selected topic
    interviewers = Interviewer.query.filter_by(specialization=form.topic.data).all()
    if not interviewers:
        # If no specialized interviewer found, get any interviewer
        interviewers = Interviewer.query.all()
    
    if form.validate_on_submit():
        # Select a random interviewer
        interviewer = random.choice(interviewers)
        
        # Create a new interview session
        interview = Interview(
            user_id=session['user_id'],
            interviewer_id=interviewer.id,
            topic=form.topic.data,
            difficulty=form.difficulty.data,
            start_time=datetime.now(),
            duration=0,
            confidence_score=0
        )
        db.session.add(interview)
        db.session.commit()
        
        return redirect(url_for('interview_room', interview_id=interview.id))
    
    return render_template('start_interview.html', form=form)

@app.route('/interview-room/<int:interview_id>')
def interview_room(interview_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != session['user_id']:
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
        
    return render_template('interview_room.html', interview=interview, interviewer=interview.interviewer)

if __name__ == '__main__':
    app.run(debug=True)

def allowed_video_file(filename):
    ALLOWED_EXTENSIONS = {'mp4', 'webm', 'mov'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize database
db.init_app(app)

with app.app_context():
    db.create_all()

# Initialize facial analyzer
from facial_analysis import FacialExpressionAnalyzer
facial_analyzer = FacialExpressionAnalyzer()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add session to template context
@app.context_processor
def inject_session():
    return dict(session=session)

# Add current year to template context
@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

# Create all tables and initial data
with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Clear existing data
    Question.query.delete()
    InterviewerAvatar.query.delete()
    
    # Add interviewer avatars
    avatars = [
        # Data Structures & Algorithms Specialists
        {
            'name': 'Dr. Alex Kumar',
            'personality': 'analytical',
            'model_path': 'dsa_expert1.png',
            'avatar_type': 'dsa_expert',
            'specialization': 'data_structures_algorithms',
            'description': 'Algorithm Specialist with 10+ years at top tech companies'
        },
        {
            'name': 'Emily Chen',
            'personality': 'systematic',
            'model_path': 'dsa_expert2.png',
            'avatar_type': 'dsa_expert',
            'specialization': 'data_structures_algorithms',
            'description': 'Senior Software Engineer specializing in optimization'
        },
        # Data Science Experts
        {
            'name': 'Dr. Sarah Chen',
            'personality': 'analytical',
            'model_path': 'data_scientist1.png',
            'avatar_type': 'data_scientist',
            'specialization': 'data_science',
            'description': 'Lead Data Scientist with focus on ML/AI'
        },
        {
            'name': 'Dr. Michael Ross',
            'personality': 'analytical',
            'model_path': 'data_scientist2.png',
            'avatar_type': 'data_scientist',
            'specialization': 'data_science',
            'description': 'AI Research Scientist with expertise in Deep Learning'
        },
        # Data Analysis Professionals
        {
            'name': 'Lisa Thompson',
            'personality': 'detail-oriented',
            'model_path': 'data_analyst1.png',
            'avatar_type': 'data_analyst',
            'specialization': 'data_analysis',
            'description': 'Senior Data Analyst specializing in Business Intelligence'
        },
        {
            'name': 'David Martinez',
            'personality': 'analytical',
            'model_path': 'data_analyst2.png',
            'avatar_type': 'data_analyst',
            'specialization': 'data_analysis',
            'description': 'Data Analytics Manager with focus on Statistical Analysis'
        },
        # QA/Testing Experts
        {
            'name': 'Maria Garcia',
            'personality': 'detail-oriented',
            'model_path': 'qa_engineer1.png',
            'avatar_type': 'qa_engineer',
            'specialization': 'software_testing',
            'description': 'Senior QA Engineer specializing in Automation Testing'
        },
        {
            'name': 'James Wilson',
            'personality': 'methodical',
            'model_path': 'qa_engineer2.png',
            'avatar_type': 'qa_engineer',
            'specialization': 'software_testing',
            'description': 'Test Architect with expertise in Security Testing'
        },
        # Aptitude Assessment Specialists
        {
            'name': 'Dr. Rachel Adams',
            'personality': 'encouraging',
            'model_path': 'aptitude_expert1.png',
            'avatar_type': 'aptitude_expert',
            'specialization': 'aptitude',
            'description': 'Cognitive Assessment Specialist'
        },
        {
            'name': 'Prof. Robert Clark',
            'personality': 'analytical',
            'model_path': 'aptitude_expert2.png',
            'avatar_type': 'aptitude_expert',
            'specialization': 'aptitude',
            'description': 'Quantitative Reasoning Expert'
        }
    ]
    
    for avatar_data in avatars:
        avatar = InterviewerAvatar(**avatar_data)
        db.session.add(avatar)
    
    # Define technical interview topics
    topics = {
        'data_structures_algorithms': {
            'easy': [
                'Explain the difference between an array and a linked list.',
                'What is a stack data structure and what are its basic operations?',
                'How does a queue differ from a stack?',
                'Explain what is a binary search and when would you use it?',
                'What is the time complexity of bubble sort?'
            ],
            'medium': [
                'Explain how a hash table works and discuss collision resolution strategies.',
                'What is a binary search tree and what are its properties?',
                'Explain the quicksort algorithm and its time complexity.',
                'What is dynamic programming and when would you use it?',
                'Describe the difference between DFS and BFS traversal.'
            ],
            'hard': [
                'Explain the A* pathfinding algorithm and its applications.',
                'What is a red-black tree and how does it maintain balance?',
                'Describe how you would implement a concurrent hash map.',
                'Explain the Dijkstra\'s algorithm and its time complexity.',
                'What are B-trees and how are they used in databases?'
            ]
        },
        'data_science': {
            'easy': [
                'What is the difference between supervised and unsupervised learning?',
                'Explain what a confusion matrix is.',
                'What is the difference between correlation and causation?',
                'Explain what feature scaling is and why it\'s important.',
                'What is the purpose of train-test split in machine learning?'
            ],
            'medium': [
                'Explain the bias-variance tradeoff in machine learning.',
                'What is regularization and when should you use it?',
                'Explain the differences between L1 and L2 regularization.',
                'What is cross-validation and why is it important?',
                'Explain how decision trees work and their advantages/disadvantages.'
            ],
            'hard': [
                'Explain how LSTM networks work and their advantages over RNNs.',
                'What is the mathematics behind Support Vector Machines?',
                'Explain the concept of ensemble learning and various ensemble methods.',
                'How does the backpropagation algorithm work in neural networks?',
                'Explain the mathematics behind Principal Component Analysis (PCA).'
            ]
        },
        'data_analysis': {
            'easy': [
                'What is the difference between mean, median, and mode?',
                'Explain what a p-value is in statistics.',
                'What is the purpose of data cleaning?',
                'Explain what a box plot tells you about your data.',
                'What is the difference between qualitative and quantitative data?'
            ],
            'medium': [
                'Explain the concept of statistical significance.',
                'What are different types of sampling methods?',
                'How do you handle missing data in a dataset?',
                'Explain the concept of A/B testing.',
                'What is the difference between correlation and regression?'
            ],
            'hard': [
                'Explain various time series analysis techniques.',
                'What is the mathematics behind logistic regression?',
                'Explain different hypothesis testing methods.',
                'How would you analyze multivariate data?',
                'Explain the concept of survival analysis.'
            ]
        },
        'software_testing': {
            'easy': [
                'What is the difference between unit testing and integration testing?',
                'Explain what test-driven development (TDD) is.',
                'What is regression testing?',
                'Explain the difference between black box and white box testing.',
                'What is the purpose of smoke testing?'
            ],
            'medium': [
                'Explain different test automation frameworks.',
                'What are mocks and stubs in testing?',
                'How do you approach API testing?',
                'Explain the concept of test coverage.',
                'What are different types of performance testing?'
            ],
            'hard': [
                'How would you design a test automation framework from scratch?',
                'Explain strategies for testing microservices architecture.',
                'How do you approach security testing?',
                'What are different strategies for load testing?',
                'How would you test AI/ML models?'
            ]
        },
        'aptitude': {
            'easy': [
                'If a train travels 360 kilometers in 4 hours, what is its speed in kilometers per hour?',
                'What comes next in the sequence: 2, 4, 8, 16, __?',
                'If 5 workers can complete a task in 10 days, how many days will it take 2 workers?',
                'What is 15% of 200?',
                'If A is twice as old as B, and B is 15 years old, how old is A?'
            ],
            'medium': [
                'A car depreciates 20% annually. If it costs $10,000 now, what will be its value after 2 years?',
                'If 8 machines can produce 96 items in 12 hours, how many machines are needed to produce 144 items in 8 hours?',
                'Find the next number in the series: 3, 8, 15, 24, __',
                'A mixture of 60 liters has water and milk in ratio 2:1. How many liters of milk should be added to make the ratio 1:1?',
                'If the probability of an event occurring is 0.4, what is the probability of it not occurring?'
            ],
            'hard': [
                'Two trains start at the same time from stations A and B, 400 km apart. If train 1 travels at 80 km/h and train 2 at 70 km/h, after how many hours will they meet?',
                'In how many ways can 7 people be seated around a circular table?',
                'If log(x) + log(y) = log(xy), prove that log(x^n) = n*log(x)',
                'A boat travels 24 km upstream in 6 hours and the same distance downstream in 4 hours. Find the speed of the stream.',
                'Three unbiased coins are tossed simultaneously. What is the probability of getting at least two heads?'
            ]
        }
    }
    
    # Add questions to database
    for topic, difficulties in topics.items():
        for difficulty, questions in difficulties.items():
            for content in questions:
                question = Question(
                    topic=topic,
                    difficulty=difficulty,
                    content=content,
                    category='technical' if topic != 'aptitude' else 'aptitude'
                )
                db.session.add(question)
                db.session.commit()
    
    db.session.commit()
    print("Database initialized with technical interview topics and avatars!")

# Login required decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Context processors
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return dict(user=user)
    return dict(user=None)

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# Form Classes
class InterviewForm(FlaskForm):
    topic = SelectField('Select Topic', validators=[DataRequired()])
    difficulty = SelectField('Select Difficulty', validators=[DataRequired()], choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ])
    num_interviewers = SelectField('Number of Interviewers', validators=[DataRequired()], choices=[
        ('1', '1 Interviewer'),
        ('2', '2 Interviewers'),
        ('3', '3 Interviewers')
    ])
    submit = SubmitField('Start Interview')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically save the contact form data or send an email
        # For now, we'll just show a success message
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/upload-video', methods=['GET', 'POST'])
def upload_video():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No video file uploaded', 'error')
            return redirect(request.url)
            
        video = request.files['video']
        question_id = request.form.get('question_id')
        
        if video.filename == '':
            flash('No video selected', 'error')
            return redirect(request.url)
            
        if not question_id:
            flash('Please select a question', 'error')
            return redirect(request.url)
            
        if video and allowed_video_file(video.filename):
            filename = secure_filename(video.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video.save(video_path)
            
            # Save video details to database
            video_url = url_for('static', filename=f'uploads/{filename}')
            new_video = InterviewVideo(
                user_id=session['user_id'],
                question_id=question_id,
                video_url=video_url
            )
            db.session.add(new_video)
            db.session.commit()
            
            flash('Video uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid video format. Supported formats: MP4, WebM, MOV', 'error')
            return redirect(request.url)
    
    # GET request - show upload form
    questions = Question.query.all()
    return render_template('upload_video.html', questions=questions)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        education = request.form.get('education')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            phone=phone,
            education=education
        )
        
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    interviews = Interview.query.filter_by(user_id=session['user_id']).order_by(Interview.start_time.desc()).all()
    return render_template('dashboard.html', interviews=interviews, user=user)

@app.route('/start-interview', methods=['GET', 'POST'])
@login_required
def start_interview():
    form = InterviewForm()
    
    # Get available topics for dropdown
    topics = db.session.query(Question.topic).distinct().all()
    form.topic.choices = [(topic[0], topic[0].replace('_', ' ').title()) for topic in topics]
    
    if request.method == 'POST':
        topic = request.form.get('topic')
        difficulty = request.form.get('difficulty')
        num_interviewers = int(request.form.get('num_interviewers', 1))
        
        if not all([topic, difficulty]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('start_interview'))
        
        # Create new interview
        interview = Interview(
            user_id=session['user_id'],
            topic=topic,
            difficulty=difficulty,
            num_interviewers=num_interviewers,
            start_time=datetime.now(),
            current_question=0  # Start with the first question
        )
        
        # Get questions for this topic and difficulty
        questions = Question.query.filter_by(
            topic=topic,
            difficulty=difficulty
        ).all()
        
        if not questions:
            flash('No questions available for this topic and difficulty', 'error')
            return redirect(url_for('start_interview'))
        
        # Assign questions to interview
        for i, question in enumerate(questions, 1):
            question.question_order = i
            interview.questions.append(question)
        
        db.session.add(interview)
        db.session.commit()
        
        return redirect(url_for('interview_room', interview_id=interview.id))
    
    return render_template('start_interview.html', form=form)

@app.route('/interview-room/<int:interview_id>')
@login_required
def interview_room(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    
    # Ensure the interview belongs to the current user
    if interview.user_id != session['user_id']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    # Get an interviewer avatar specialized in the interview topic
    interviewer = InterviewerAvatar.query.filter_by(specialization=interview.topic).first()
    if not interviewer:
        # Fallback to any available interviewer if no specialist is found
        interviewer = InterviewerAvatar.query.first()
    
    # Get the current question
    current_question = None
    if interview.questions:
        # Get question by order number
        current_question = Question.query.filter_by(
            topic=interview.topic,
            difficulty=interview.difficulty
        ).filter(Question.question_order == (interview.current_question + 1)).first()
    
    if not current_question and interview.questions:
        # Fallback: get the first question if no current question
        current_question = interview.questions[0]
    
    return render_template('interview_room.html',
                           interview=interview,
                           interviewer=interviewer,
                           current_question=current_question)

@app.route('/upload-video/<int:question_id>', methods=['POST'])
@login_required
def upload_video_endpoint(question_id):
    question = Question.query.get_or_404(question_id)
    
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    video = request.files['video']
    if video.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if video:
        # Create upload directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save video with unique filename
        filename = f"{session['user_id']}_{question_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video.save(video_path)
        
        # Update question with video path
        question.video_path = filename
        db.session.commit()
        
        return jsonify({'success': True, 'video_path': filename})
    
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/delete-video/<int:question_id>', methods=['POST'])
@login_required
def delete_video_endpoint(question_id):
    question = Question.query.get_or_404(question_id)
    
    if question.video_path:
        # Delete video file
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], question.video_path)
        if os.path.exists(video_path):
            os.remove(video_path)
        
        # Clear video path in database
        question.video_path = None
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'error': 'No video found'}), 404

@app.route('/test-interview-room')
def test_interview_room():
    try:
        print("Creating test interview...")  # Debug print
        
        # Create a test user if needed
        test_user = User.query.filter_by(username='test_user').first()
        if not test_user:
            test_user = User(
                username='test_user',
                email='test@example.com',
                full_name='Test User',
                password_hash=generate_password_hash('test123')  # Hash the password
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"Created test user with ID: {test_user.id}")  # Debug print
        
        # Create a test interview
        interview = Interview(
            user_id=test_user.id,
            topic='technology',
            difficulty='beginner',
            num_interviewers=1,
            confidence_score=0.0,
            stress_level=0.0,
            engagement_score=0.0,
            status='in_progress',
            start_time=datetime.utcnow()
        )
        
        db.session.add(interview)
        db.session.commit()
        print(f"Created interview with ID: {interview.id}")  # Debug print
        
        # Get or create a test interviewer
        interviewer = InterviewerAvatar.query.filter_by(specialization='technology').first()
        if not interviewer:
            interviewer = InterviewerAvatar(
                name='Technical Expert',
                avatar_type='technical',
                specialization='technology',
                personality='professional',
                model_path='interviewer1.jpg',
                voice_id='en-US-Neural2-D',
                description='General Technical Interviewer'
            )
            db.session.add(interviewer)
            db.session.commit()
            print(f"Created interviewer with ID: {interviewer.id}")  # Debug print
        
        # Get first question
        first_question = Question.query.filter_by(topic='technology', difficulty='beginner').filter_by(question_order=1).first()
        if not first_question:
            print("No questions found in database!")  # Debug print
            first_question = Question(
                topic='technology',
                difficulty='beginner',
                content='Tell me about your experience with Python programming.',
                category='technical',
                keywords='python, programming, experience',
                video_path='static/videos/tech_beginner_1.mp4',
                question_order=1
            )
            db.session.add(first_question)
            db.session.commit()
            print(f"Created default question with ID: {first_question.id}")  # Debug print
        else:
            print(f"Found first question: {first_question.content}")  # Debug print
        
        # Store interview ID in session
        session['interview_id'] = interview.id
        print(f"Stored interview_id in session: {session['interview_id']}")  # Debug print
        
        print("Rendering interview room template...")  # Debug print
        return render_template('interview_room.html',
                            interview=interview,
                            interviewer=interviewer,
                            topic='technology',
                            difficulty='beginner',
                            current_question=first_question)  # Pass first question to template

    except Exception as e:
        print(f"Error in test_interview_room: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()  # Print full traceback
        return f"Error: {str(e)}", 500

# API endpoint for getting next question
@app.route('/api/next-question/<int:interview_id>')
@login_required
def next_question(interview_id):
    try:
        interview = Interview.query.get_or_404(interview_id)
        
        # Check if user owns this interview
        if interview.user_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get the current question number from the interview
        current_question_num = interview.current_question or 0
        next_question_num = current_question_num + 1
        
        # Get next question based on topic, difficulty, and order
        question = Question.query.filter_by(
            topic=interview.topic,
            difficulty=interview.difficulty
        ).filter(Question.question_order == next_question_num).first()
        
        if not question:
            # If no more questions, return completion message
            return jsonify({
                'completed': True,
                'message': 'Interview completed!'
            })
        
        # Update interview's current question
        interview.current_question = next_question_num
        db.session.commit()
        
        return jsonify({
            'id': question.id,
            'content': question.content,
            'video_path': question.video_path,
            'order': question.question_order
        })
        
    except Exception as e:
        print(f"Error in next_question: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# API endpoint for updating metrics
@app.route('/api/update-metrics', methods=['POST'])
def update_metrics():
    try:
        data = request.get_json()
        interview_id = session.get('interview_id')
        
        if not interview_id:
            return jsonify({'error': 'No active interview'}), 400
            
        interview = Interview.query.get_or_404(interview_id)
        
        # Update interview metrics
        interview.confidence_score = data.get('confidence', interview.confidence_score)
        interview.stress_level = data.get('stress', interview.stress_level)
        interview.engagement_score = data.get('engagement', interview.engagement_score)
        
        db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"Error updating metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-expression', methods=['POST'])
@login_required
def analyze_expression():
    if 'frame' not in request.files:
        return jsonify({'error': 'No frame provided'}), 400
        
    frame_file = request.files['frame']
    frame_data = frame_file.read()
    
    # Convert frame data to numpy array
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    analyzer = FacialExpressionAnalyzer()
    expressions = analyzer.detect_expression(frame)
    metrics = analyzer.get_interview_metrics(expressions)
    
    return jsonify({
        'expressions': expressions,
        'metrics': metrics
    })

@app.route('/api/synthesize-speech', methods=['POST'])
@login_required
def synthesize_speech():
    if not request.json or 'text' not in request.json:
        return jsonify({'error': 'No text provided'}), 400
    
    text = request.json['text']
    voice_id = request.json.get('voice_id', 'en-US-Standard-F')
    
    try:
        # Here we would use a text-to-speech service
        # For now, return a mock audio URL
        return jsonify({
            'audio_url': url_for('static', filename='audio/question.mp3')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-interview-metrics', methods=['POST'])
@login_required
def save_interview_metrics():
    data = request.get_json()
    interview_id = session.get('interview_id')
    
    if not interview_id:
        return jsonify({'error': 'No active interview'}), 400
    
    interview = Interview.query.get_or_404(interview_id)
    interview.confidence_score = data.get('confidence')
    interview.stress_level = data.get('stress_level')
    interview.engagement_score = data.get('engagement')
    
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/end-interview', methods=['POST'])
@login_required
def end_interview():
    interview_id = session.get('interview_id')
    if not interview_id:
        return jsonify({'error': 'No active interview'}), 400
    
    interview = Interview.query.get_or_404(interview_id)
    interview.end_time = datetime.utcnow()
    
    db.session.commit()
    session.pop('interview_id', None)
    
    return jsonify({
        'status': 'success',
        'redirect': url_for('dashboard')
    })

@app.route('/save_recording', methods=['POST'])
@login_required
def save_recording():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    video = request.files['video']
    question_id = request.form.get('question_id', '0')
    interview_id = session.get('interview_id')
    
    if not interview_id:
        return jsonify({'error': 'No active interview'}), 400
    
    # Create recordings directory if it doesn't exist
    recordings_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(session['user_id']))
    os.makedirs(recordings_dir, exist_ok=True)
    
    # Save video file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'response_{timestamp}.webm'
    filepath = os.path.join(recordings_dir, filename)
    video.save(filepath)
    
    try:
        # Create interview response
        response = InterviewResponse(
            interview_id=interview_id,
            question_id=question_id,
            video_path=os.path.join(str(session['user_id']), filename),
            confidence_score=0.8,
            technical_score=0.75,
            communication_score=0.85,
            emotional_state='neutral',
            response_time=30  # This would be calculated from actual recording duration
        )
        db.session.add(response)
        
        # Update interview metrics
        interview = Interview.query.get(interview_id)
        if interview:
            # Update average scores
            responses = interview.responses
            if responses:
                interview.confidence_score = sum(r.confidence_score for r in responses) / len(responses)
                interview.engagement_score = sum(r.technical_score + r.communication_score for r in responses) / (2 * len(responses))
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'analysis': {
                'technical_score': response.technical_score,
                'communication_score': response.communication_score,
                'confidence': response.confidence_score,
                'stress_level': 0.3
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/manage-questions')
@login_required
def manage_questions():
    questions = Question.query.all()
    return render_template('manage_questions.html', questions=questions)

@app.route('/add-question', methods=['GET', 'POST'])
@login_required
def add_question():
    if request.method == 'POST':
        topic = request.form.get('topic')
        difficulty = request.form.get('difficulty')
        content = request.form.get('content')
        category = request.form.get('category')
        video = request.files.get('video')
        
        if not all([topic, difficulty, content, category, video]):
            flash('All fields are required', 'error')
            return redirect(url_for('add_question'))
        
        if video and video.filename:
            # Check if filename is secure
            if not secure_filename(video.filename):
                flash('Invalid video filename', 'error')
                return redirect(url_for('add_question'))
            
            # Create directory if it doesn't exist
            interviewer_videos_dir = os.path.join('static', 'interviewer_videos')
            os.makedirs(interviewer_videos_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'interviewer_{timestamp}_{secure_filename(video.filename)}'
            video_path = os.path.join(interviewer_videos_dir, filename)
            
            try:
                # Save the video file
                video.save(video_path)
                
                # Create question with video path
                question = Question(
                    topic=topic,
                    difficulty=difficulty,
                    content=content,
                    category=category,
                    interviewer_video_path=os.path.join('interviewer_videos', filename)
                )
                
                db.session.add(question)
                db.session.commit()
                
                flash('Question added successfully with video', 'success')
                return redirect(url_for('manage_questions'))
                
            except Exception as e:
                # Clean up video file if it was saved
                if os.path.exists(video_path):
                    os.remove(video_path)
                flash(f'Error saving video: {str(e)}', 'error')
                return redirect(url_for('add_question'))
        else:
            flash('Please upload a video file', 'error')
            return redirect(url_for('add_question'))
    
    return render_template('add_question.html')

@app.route('/upload-interviewer-video/<int:question_id>', methods=['POST'])
@login_required
def upload_interviewer_video(question_id):
    question = Question.query.get_or_404(question_id)

    if 'video' not in request.files:
        flash('No video file uploaded', 'error')
        return redirect(url_for('manage_questions'))

    video = request.files['video']
    if video.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('manage_questions'))

    if video:
        # Create upload directory if it doesn't exist
        interviewer_videos_dir = os.path.join('static', 'interviewer_videos')
        os.makedirs(interviewer_videos_dir, exist_ok=True)

        # Save video with unique filename
        filename = f"interviewer_{question_id}_{secure_filename(video.filename)}"
        video_path = os.path.join(interviewer_videos_dir, filename)
        video.save(video_path)

        # Update question with video path
        question.interviewer_video_path = os.path.join('interviewer_videos', filename)
        db.session.commit()

        flash('Video uploaded successfully', 'success')
    else:
        flash('Invalid file format', 'error')

    return redirect(url_for('manage_questions'))

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_file(os.path.join('static', filename))

@app.template_filter('avg')
def avg_filter(lst, attribute=None):
    if not lst:
        return 0
    if attribute:
        values = [getattr(x, attribute) for x in lst if getattr(x, attribute) is not None]
    else:
        values = [x for x in lst if x is not None]
    return sum(values) / len(values) if values else 0

if __name__ == '__main__':
    print('Starting application in dry-run mode...')
    print('Configuration:')
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print('\nAvailable routes:')
    for rule in app.url_map.iter_rules():
        print(f"- {rule.endpoint}: {rule.methods} {rule}")
    print('\nDry run completed successfully.')
    
    # Start the application
    app.run(debug=True)

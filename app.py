from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import json
from facial_analysis import FacialExpressionAnalyzer
import cv2
import numpy as np
import base64
from models import db, User, Interview, InterviewResponse, Question, QuestionFollowUps, InterviewerAvatar

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'recordings'

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize facial analyzer
facial_analyzer = FacialExpressionAnalyzer()

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
            
        return render_template('login.html', error="Invalid username or password")
    
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
            return render_template('signup.html', error="Username already exists")
            
        if User.query.filter_by(email=email).first():
            return render_template('signup.html', error="Email already registered")
        
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
        
        login_user(user)
        return redirect(url_for('dashboard'))
        
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.start_time.desc()).all()
    return render_template('dashboard.html', interviews=interviews)

@app.route('/start-interview', methods=['GET', 'POST'])
@login_required
def start_interview():
    if request.method == 'POST':
        topic = request.form.get('topic')
        difficulty = request.form.get('difficulty')
        num_interviewers = int(request.form.get('interviewers', 1))
        
        interview = Interview(
            user_id=current_user.id,
            topic=topic,
            difficulty=difficulty,
            num_interviewers=num_interviewers,
            confidence_score=0.0,
            stress_level=0.0,
            engagement_score=0.0
        )
        
        db.session.add(interview)
        db.session.commit()
        
        session['interview_id'] = interview.id
        return redirect(url_for('interview_room'))
    
    return render_template('start_interview.html')

@app.route('/interview-room')
@login_required
def interview_room():
    interview_id = session.get('interview_id')
    if not interview_id:
        return redirect(url_for('start_interview'))
    
    interview = Interview.query.get_or_404(interview_id)
    return render_template('interview_room.html', interview=interview)

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
    
    # Save video file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'interview_{current_user.id}_{question_id}_{timestamp}.webm'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video.save(filepath)
    
    # Update interview record or response with video path
    if 'interview_id' in session:
        interview = Interview.query.get(session['interview_id'])
        if interview:
            interview.video_path = filename
            db.session.commit()
    
    # Create interview response if question_id is provided
    if question_id != '0':
        response = InterviewResponse(
            interview_id=session.get('interview_id'),
            question_id=question_id,
            video_path=filename,
            confidence_score=0.7,  # These would be calculated based on actual analysis
            technical_score=0.75,
            communication_score=0.8,
            emotional_state='neutral',
            response_time=0
        )
        db.session.add(response)
        db.session.commit()
    
    return jsonify({
        'success': True,
        'filename': filename,
        'analysis': {
            'technical_score': 0.75,
            'communication_score': 0.8,
            'confidence': 0.7,
            'stress_level': 0.3
        }
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_file(f'static/{filename}')

@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

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
    app.run(debug=True)

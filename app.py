from datetime import datetime
import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Interview, InterviewerAvatar, Question, InterviewResponse
from facial_analysis import FacialExpressionAnalyzer
from sqlalchemy import func
import json
import cv2
import numpy as np
import base64
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField
from wtforms.validators import InputRequired as DataRequired

# Simple auth decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF

# Initialize extensions
db.init_app(app)

# Initialize facial analyzer
facial_analyzer = FacialExpressionAnalyzer()

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
    db.create_all()
    print("Database tables created")
    
    # Add test questions if they don't exist
    if Question.query.count() == 0:
        print("Adding test questions...")
        test_questions = [
            Question(
                topic='technology',
                difficulty='beginner',
                content='Tell me about your experience with Python programming.',
                category='technical',
                keywords='python, programming, experience',
                video_path='static/videos/tech_beginner_1.mp4',
                question_order=1
            ),
            Question(
                topic='technology',
                difficulty='beginner',
                content='What are the key differences between Python 2 and Python 3?',
                category='technical',
                keywords='python2, python3, differences',
                video_path='static/videos/tech_beginner_2.mp4',
                question_order=2
            ),
            Question(
                topic='technology',
                difficulty='beginner',
                content='Explain object-oriented programming concepts.',
                category='technical',
                keywords='oop, classes, objects, inheritance',
                video_path='static/videos/tech_beginner_3.mp4',
                question_order=3
            )
        ]
        try:
            for question in test_questions:
                db.session.add(question)
            db.session.commit()
            print("Successfully added test questions")
        except Exception as e:
            print(f"Error adding test questions: {str(e)}")
            db.session.rollback()

# Form classes
class InterviewForm(FlaskForm):
    topic = SelectField('Topic', choices=[
        ('technology', 'Technology'),
        ('behavioral', 'Behavioral'),
        ('leadership', 'Leadership')
    ], validators=[DataRequired()])
    
    difficulty = SelectField('Difficulty', choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ], validators=[DataRequired()])
    
    num_interviewers = SelectField('Number of Interviewers', 
        choices=[(1, '1'), (2, '2'), (3, '3')],
        coerce=int,
        validators=[DataRequired()])
    
    submit = SubmitField('Start Interview')

app.config['UPLOAD_FOLDER'] = 'recordings'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'videos')
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'mov'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            session['user_id'] = user.id
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
        
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
        
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
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
    try:
        form = InterviewForm()
        
        if request.method == 'GET':
            return render_template('start_interview.html', form=form)
        
        if request.method == 'POST':
            if form.validate_on_submit():
                # Create new interview
                interview = Interview(
                    user_id=session['user_id'],
                    topic=form.topic.data,
                    difficulty=form.difficulty.data,
                    num_interviewers=form.num_interviewers.data,
                    status='pending',
                    start_time=datetime.utcnow()
                )
                
                db.session.add(interview)
                db.session.commit()
                
                # Store interview ID in session
                session['interview_id'] = interview.id
                
                flash('Interview created successfully!', 'success')
                return redirect(url_for('interview_room', interview_id=interview.id))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{getattr(form, field).label.text}: {error}', 'danger')
                return render_template('start_interview.html', form=form)
            
    except Exception as e:
        print(f"Error in start_interview: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while creating the interview.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/interview-room/<int:interview_id>')
@login_required
def interview_room(interview_id):
    try:
        # Get the interview
        interview = Interview.query.get_or_404(interview_id)
        
        # Check if the user owns this interview
        if interview.user_id != session['user_id']:
            flash('You do not have permission to access this interview.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Update interview status if needed
        if interview.status == 'pending':
            interview.status = 'in_progress'
            interview.start_time = datetime.utcnow()
            db.session.commit()
        
        # Get or create interviewer based on topic
        interviewer = InterviewerAvatar.query.filter_by(specialization=interview.topic).first()
        if not interviewer:
            interviewer = InterviewerAvatar(
                name=f'{interview.topic.title()} Expert',
                avatar_type='professional',
                specialization=interview.topic,
                personality='professional',
                model_path='interviewer1.jpg',
                voice_id='en-US-Neural2-D',
                description=f'Expert {interview.topic.title()} Interviewer'
            )
            db.session.add(interviewer)
            db.session.commit()
        
        # Get first question
        question = Question.query.filter_by(
            topic=interview.topic,
            difficulty=interview.difficulty
        ).filter_by(question_order=1).first()
        
        if not question:
            question = Question(
                topic=interview.topic,
                difficulty=interview.difficulty,
                content=f'Tell me about your experience with {interview.topic}.',
                category='general',
                keywords=f'{interview.topic}, experience',
                video_path='static/videos/default.mp4',
                question_order=1
            )
            db.session.add(question)
            db.session.commit()
        
        return render_template('interview_room.html', 
                             interview=interview,
                             interviewer=interviewer,
                             topic=interview.topic,
                             difficulty=interview.difficulty,
                             current_question=question)
                             
    except Exception as e:
        print(f"Error in interview_room: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while loading the interview room.', 'danger')
        return redirect(url_for('dashboard'))

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

@app.route('/upload-video', methods=['GET', 'POST'])
@login_required
def upload_video():
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No video file uploaded', 'danger')
            return redirect(request.url)
            
        video = request.files['video']
        question_id = request.form.get('question_id')
        
        if video.filename == '':
            flash('No video selected', 'danger')
            return redirect(request.url)
            
        if not question_id:
            flash('No question selected', 'danger')
            return redirect(request.url)
            
        if video and allowed_file(video.filename):
            try:
                # Secure the filename and save the file
                filename = secure_filename(video.filename)
                video_path = os.path.join('videos', filename)
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                video.save(full_path)
                
                # Update the question with the video path
                question = Question.query.get(question_id)
                if question:
                    question.video_path = video_path
                    db.session.commit()
                    flash('Video uploaded successfully!', 'success')
                else:
                    flash('Question not found', 'danger')
                
                return jsonify({
                    'success': True,
                    'message': 'Video uploaded successfully',
                    'video_path': video_path
                })
                
            except Exception as e:
                print(f"Error uploading video: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Error uploading video'
                }), 500
                
        return jsonify({
            'success': False,
            'message': 'Invalid file type'
        }), 400
        
    # GET request - render upload form
    questions = Question.query.all()
    return render_template('upload_video.html', questions=questions)

@app.route('/delete-video/<int:question_id>', methods=['POST'])
@login_required
def delete_video(question_id):
    try:
        question = Question.query.get_or_404(question_id)
        
        if question.video_path:
            # Delete the video file
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(question.video_path))
            if os.path.exists(video_path):
                os.remove(video_path)
            
            # Clear the video path in the database
            question.video_path = None
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Video deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No video found for this question'
            }), 404
            
    except Exception as e:
        print(f"Error deleting video: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error deleting video'
        }), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_file(f'static/{filename}')

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

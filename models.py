from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    education = db.Column(db.String(200))
    interviews = db.relationship('Interview', backref='user', lazy=True)

class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(50))
    difficulty = db.Column(db.String(20))
    num_interviewers = db.Column(db.Integer)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    feedback = db.Column(db.Text)
    score = db.Column(db.Float)
    status = db.Column(db.String(20), default='in_progress')
    current_question = db.Column(db.Integer, default=0)  
    confidence_score = db.Column(db.Float, default=0.0)
    technical_score = db.Column(db.Float, default=0.0)
    communication_score = db.Column(db.Float, default=0.0)
    stress_level = db.Column(db.Float, default=0.0)
    engagement_score = db.Column(db.Float, default=0.0)
    duration = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')
    questions = db.relationship('Question', secondary='interview_questions')
    responses = db.relationship('InterviewResponse', backref='interview', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(50))
    difficulty = db.Column(db.String(20))
    content = db.Column(db.Text)
    category = db.Column(db.String(20))
    video_path = db.Column(db.String(200))  # For candidate's recorded response
    interviewer_video_path = db.Column(db.String(200))  # For interviewer's question video
    question_order = db.Column(db.Integer)  # Order in which question appears in interview

class InterviewerAvatar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    personality = db.Column(db.String(50))
    model_path = db.Column(db.String(200))
    avatar_type = db.Column(db.String(50))
    specialization = db.Column(db.String(50))
    description = db.Column(db.Text)

class InterviewResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    video_path = db.Column(db.String(200))
    confidence_score = db.Column(db.Float)
    technical_score = db.Column(db.Float)
    communication_score = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    question = db.relationship('Question', backref='responses')

# Association table for Interview-Question relationship
interview_questions = db.Table('interview_questions',
    db.Column('interview_id', db.Integer, db.ForeignKey('interview.id'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True)
)

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    education = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    interviews = db.relationship('Interview', backref='user', lazy=True)

class Interview(db.Model):
    __tablename__ = 'interviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    num_interviewers = db.Column(db.Integer, default=1)
    video_path = db.Column(db.String(200))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    confidence_score = db.Column(db.Float, default=0.0)
    stress_level = db.Column(db.Float, default=0.0)
    engagement_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    feedback = db.Column(db.Text)
    current_question = db.Column(db.Integer, default=0)  # Track current question number
    responses = db.relationship('InterviewResponse', backref='interview', lazy=True)

    @property
    def duration(self):
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return round(delta.total_seconds() / 3600, 2)  # Convert to hours
        return 0.0

class InterviewResponse(db.Model):
    __tablename__ = 'interview_responses'
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    video_path = db.Column(db.String(200))
    confidence_score = db.Column(db.Float, default=0.0)
    technical_score = db.Column(db.Float, default=0.0)
    communication_score = db.Column(db.Float, default=0.0)
    emotional_state = db.Column(db.String(50), default='neutral')
    response_time = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    keywords = db.Column(db.Text)
    video_path = db.Column(db.String(200))  # Path to the question video
    question_order = db.Column(db.Integer)  # Order of questions in the interview
    follow_up_questions = db.relationship('Question',
                                        secondary='question_follow_ups',
                                        primaryjoin='Question.id==QuestionFollowUps.question_id',
                                        secondaryjoin='Question.id==QuestionFollowUps.follow_up_id',
                                        backref='parent_questions')

class QuestionFollowUps(db.Model):
    __tablename__ = 'question_follow_ups'
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), primary_key=True)
    follow_up_id = db.Column(db.Integer, db.ForeignKey('questions.id'), primary_key=True)
    difficulty_increase = db.Column(db.Float, default=0.5)

class InterviewerAvatar(db.Model):
    __tablename__ = 'interviewer_avatars'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    avatar_type = db.Column(db.String(50))
    model_path = db.Column(db.String(200))
    personality = db.Column(db.String(50))
    voice_id = db.Column(db.String(50))
    specialization = db.Column(db.String(50))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

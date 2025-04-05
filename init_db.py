from app import app, db
from models import User, Interview, Question, InterviewerAvatar
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        print("Database tables created")
        
        # Create a test user
        test_user = User(
            username='test_user',
            email='test@example.com',
            password_hash=generate_password_hash('password'),
            full_name='Test User',
            phone='1234567890',
            education='Bachelor in Computer Science'
        )
        
        # Create some sample questions
        questions = [
            Question(
                topic='technology',
                difficulty='beginner',
                content='Tell me about your experience with Python programming.',
                category='technical',
                keywords='python, programming, experience',
                video_path=None,
                question_order=1
            ),
            Question(
                topic='technology',
                difficulty='beginner',
                content='What are the key differences between Python 2 and Python 3?',
                category='technical',
                keywords='python2, python3, differences',
                video_path=None,
                question_order=2
            ),
            Question(
                topic='technology',
                difficulty='beginner',
                content='Explain object-oriented programming concepts.',
                category='technical',
                keywords='oop, classes, objects, inheritance',
                video_path=None,
                question_order=3
            ),
            Question(
                topic='leadership',
                difficulty='beginner',
                content='Tell me about a time you led a team.',
                category='behavioral',
                keywords='leadership, team, experience',
                video_path=None,
                question_order=1
            ),
            Question(
                topic='leadership',
                difficulty='beginner',
                content='How do you handle conflicts in a team?',
                category='behavioral',
                keywords='conflict, resolution, team',
                video_path=None,
                question_order=2
            )
        ]
        
        # Create some interviewer avatars
        avatars = [
            InterviewerAvatar(
                name='Tech Expert',
                avatar_type='professional',
                model_path='videos/tech_expert.mp4',
                personality='analytical',
                voice_id='en-US-Neural2-A',
                specialization='technology',
                description='Expert in technical interviews with 10+ years experience'
            ),
            InterviewerAvatar(
                name='Leadership Coach',
                avatar_type='friendly',
                model_path='videos/leadership_coach.mp4',
                personality='supportive',
                voice_id='en-US-Neural2-C',
                specialization='leadership',
                description='Specialized in assessing leadership and soft skills'
            )
        ]
        
        try:
            # Add test user
            db.session.add(test_user)
            db.session.commit()
            print(f"Created test user with ID: {test_user.id}")
            
            # Add questions
            for question in questions:
                db.session.add(question)
            db.session.commit()
            print("Added sample questions")
            
            # Add avatars
            for avatar in avatars:
                db.session.add(avatar)
            db.session.commit()
            print("Added interviewer avatars")
            
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    init_db()

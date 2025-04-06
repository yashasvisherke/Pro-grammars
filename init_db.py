from app import app, db
from models import User, Interview, Question, InterviewerAvatar, InterviewResponse
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create tables
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

if __name__ == '__main__':
    init_db()
import random

class InterviewManager:
    def __init__(self):
        self.questions = {
            'technology': {
                'beginner': [
                    "What is your favorite programming language and why?",
                    "Explain what version control is and why it's important.",
                    "What is the difference between front-end and back-end development?",
                    "What is Object-Oriented Programming?",
                    "Explain what a database is and its importance.",
                    "What is the software development life cycle?",
                    "What are arrays and how do they work?",
                    "Explain what HTML and CSS are used for.",
                    "What is debugging and why is it important?",
                    "What is the difference between a compiler and an interpreter?"
                ],
                'intermediate': [
                    "Explain the concept of dependency injection.",
                    "How would you handle race conditions in a multi-threaded application?",
                    "Describe the differences between REST and GraphQL.",
                    "Explain SOLID principles in software development.",
                    "What are design patterns and why are they important?",
                    "How do you ensure code quality in a project?",
                    "Explain the concept of microservices architecture.",
                    "What is containerization and how does Docker work?",
                    "How do you handle database transactions?",
                    "Explain the concept of CI/CD pipelines."
                ],
                'advanced': [
                    "Design a distributed system for handling millions of concurrent users.",
                    "How would you implement a real-time collaboration feature?",
                    "Explain your approach to microservices architecture.",
                    "How would you design a scalable message queue system?",
                    "Explain the implementation of a distributed cache.",
                    "How would you handle eventual consistency in a distributed system?",
                    "Design a system for real-time analytics processing.",
                    "How would you implement a recommendation engine?",
                    "Explain blockchain technology and its implementation.",
                    "How would you design a fault-tolerant system?"
                ]
            },
            'hr': {
                'beginner': [
                    "Tell me about yourself.",
                    "Why are you interested in this position?",
                    "What are your greatest strengths and weaknesses?",
                    "Where do you see yourself in 5 years?",
                    "What motivates you at work?",
                    "How do you handle stress and pressure?",
                    "What is your ideal work environment?",
                    "How do you prioritize your work?",
                    "What are your salary expectations?",
                    "Why should we hire you?"
                ],
                'intermediate': [
                    "Describe a challenging situation at work and how you handled it.",
                    "How do you handle conflict in the workplace?",
                    "Tell me about a time you failed and what you learned.",
                    "How do you adapt to change?",
                    "What's your approach to problem-solving?",
                    "How do you handle feedback?",
                    "Describe your leadership style.",
                    "How do you maintain work-life balance?",
                    "What are your long-term career goals?",
                    "How do you stay updated in your field?"
                ],
                'advanced': [
                    "Tell me about a time you had to lead a major organizational change.",
                    "How would you improve our company culture?",
                    "Describe your experience with strategic planning.",
                    "How do you handle ethical dilemmas at work?",
                    "Describe a situation where you had to make an unpopular decision.",
                    "How do you build and maintain stakeholder relationships?",
                    "What's your approach to diversity and inclusion?",
                    "How do you measure success in your role?",
                    "Describe a time you had to pivot strategy mid-project.",
                    "How do you develop your team members?"
                ]
            },
            'management': {
                'beginner': [
                    "What's your management style?",
                    "How do you motivate your team?",
                    "How do you prioritize tasks?",
                    "How do you delegate responsibilities?",
                    "What's your approach to team building?",
                    "How do you handle team conflicts?",
                    "What's your communication style?",
                    "How do you set goals for your team?",
                    "How do you handle poor performance?",
                    "What's your approach to recognition and rewards?"
                ],
                'intermediate': [
                    "How do you handle underperforming team members?",
                    "Describe your experience with budget management.",
                    "How do you ensure project deadlines are met?",
                    "How do you manage remote teams?",
                    "What's your approach to risk management?",
                    "How do you handle crisis situations?",
                    "How do you develop team strategies?",
                    "What's your approach to change management?",
                    "How do you measure team performance?",
                    "How do you handle resource allocation?"
                ],
                'advanced': [
                    "How would you manage a department through a major digital transformation?",
                    "Describe your experience with change management.",
                    "How do you align team goals with organizational strategy?",
                    "How do you handle mergers and acquisitions?",
                    "What's your approach to organizational restructuring?",
                    "How do you manage multiple stakeholders?",
                    "How do you handle strategic partnerships?",
                    "What's your approach to innovation management?",
                    "How do you handle global team management?",
                    "How do you develop succession plans?"
                ]
            }
        }
        self.current_question_index = 0
        self.current_topic = None
        self.current_difficulty = None
        self.used_questions = set()
        self.is_interview_complete = False
        
    def start_interview(self, topic, difficulty):
        """Initialize a new interview session."""
        self.current_topic = topic
        self.current_difficulty = difficulty
        self.current_question_index = 0
        self.used_questions = set()
        self.is_interview_complete = False
        return self.get_next_question()
    
    def get_next_question(self):
        """Get the next question based on emotions and difficulty."""
        if self.is_interview_complete:
            return None
            
        available_questions = [
            q for q in self.questions[self.current_topic][self.current_difficulty]
            if q not in self.used_questions
        ]
        
        if not available_questions:
            self.is_interview_complete = True
            return None
            
        question = random.choice(available_questions)
        self.used_questions.add(question)
        return question
    
    def adjust_difficulty(self, stress_level, confidence_level):
        """Adjust difficulty based on candidate's stress and confidence levels."""
        if stress_level > 0.7 and confidence_level < 0.4:
            difficulties = ['beginner', 'intermediate', 'advanced']
            current_index = difficulties.index(self.current_difficulty)
            if current_index > 0:
                self.current_difficulty = difficulties[current_index - 1]
        elif stress_level < 0.3 and confidence_level > 0.7:
            difficulties = ['beginner', 'intermediate', 'advanced']
            current_index = difficulties.index(self.current_difficulty)
            if current_index < len(difficulties) - 1:
                self.current_difficulty = difficulties[current_index + 1]
        
        return self.current_difficulty

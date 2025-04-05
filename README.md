# AI Interview System

A modern technical interview platform with real-time facial analysis and interview recording capabilities.

## Features

- Real-time facial expression analysis
- Technical interview questions
- Video recording of responses
- Live confidence and stress level monitoring
- Modern dark-themed UI
- Secure user authentication

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the application:
- Open http://localhost:5000 in your browser
- Login with test credentials:
  - Username: test
  - Password: test

## Project Structure

```
ai-interview-system/
├── app.py                 # Main Flask application
├── facial_analysis.py     # Facial expression analysis module
├── requirements.txt       # Project dependencies
├── static/               # Static files
│   ├── images/          # Interviewer photos
│   ├── interview.js     # Interview page JavaScript
│   └── style.css        # Global styles
├── templates/           # HTML templates
│   ├── interview.html   # Interview page
│   └── login.html       # Login page
└── recordings/         # Saved interview recordings

## Technical Requirements

- Python 3.8+
- Webcam access
- Modern web browser (Chrome/Firefox recommended)
- Microphone access (for recording)

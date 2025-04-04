import cv2
import numpy as np
from typing import Dict, Tuple, Optional

class FacialExpressionAnalyzer:
    def __init__(self):
        # Load pre-trained models
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
        
        # Expression thresholds and parameters
        self.expression_params = {
            'happy': {'smile_threshold': 1.2, 'eye_aspect_ratio': 0.25},
            'surprised': {'eye_aspect_ratio': 0.35},
            'confused': {'eyebrow_height': 0.2, 'asymmetry': 0.15},
            'neutral': {'smile_threshold': 0.8, 'eye_aspect_ratio': 0.22},
            'stressed': {'eye_movement': 0.3, 'blink_rate': 0.4},
            'confident': {'posture_straight': 0.8, 'eye_contact': 0.7}
        }
        
        # Initialize state variables
        self.prev_eye_positions = []
        self.blink_count = 0
        self.last_blink_time = 0
        self.expression_history = []
        self.confidence_baseline = 0.5

    def detect_face(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) > 0:
            # Return the largest face
            return max(faces, key=lambda f: f[2] * f[3])
        return None

    def detect_eyes(self, frame: np.ndarray, face_roi: Tuple[int, int, int, int]) -> list:
        x, y, w, h = face_roi
        roi_gray = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
        
        eyes = self.eye_cascade.detectMultiScale(
            roi_gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(20, 20)
        )
        
        return [(ex+x, ey+y, ew, eh) for ex, ey, ew, eh in eyes]

    def detect_smile(self, frame: np.ndarray, face_roi: Tuple[int, int, int, int]) -> Optional[float]:
        x, y, w, h = face_roi
        roi_gray = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
        
        smiles = self.smile_cascade.detectMultiScale(
            roi_gray,
            scaleFactor=1.7,
            minNeighbors=22,
            minSize=(25, 25)
        )
        
        if len(smiles) > 0:
            # Calculate smile intensity based on size and position
            sx, sy, sw, sh = max(smiles, key=lambda s: s[2] * s[3])
            smile_ratio = (sw * sh) / (w * h)
            return smile_ratio
        return 0.0

    def calculate_eye_aspect_ratio(self, eye_roi: Tuple[int, int, int, int]) -> float:
        # Simplified EAR calculation
        _, _, w, h = eye_roi
        return h / w if w > 0 else 0

    def detect_expression(self, frame: np.ndarray) -> Dict[str, float]:
        face_roi = self.detect_face(frame)
        if face_roi is None:
            return {
                'happy': 0.0,
                'surprised': 0.0,
                'confused': 0.0,
                'neutral': 1.0,
                'stressed': 0.0,
                'confident': 0.0
            }

        eyes = self.detect_eyes(frame, face_roi)
        smile_ratio = self.detect_smile(frame, face_roi)
        
        # Calculate expression probabilities
        expressions = {}
        
        # Happy expression
        expressions['happy'] = min(1.0, smile_ratio * 2.0) if smile_ratio > self.expression_params['happy']['smile_threshold'] else 0.0
        
        # Surprised expression
        if len(eyes) >= 2:
            eye_ratios = [self.calculate_eye_aspect_ratio(eye) for eye in eyes]
            avg_eye_ratio = sum(eye_ratios) / len(eye_ratios)
            expressions['surprised'] = min(1.0, avg_eye_ratio * 3.0) if avg_eye_ratio > self.expression_params['surprised']['eye_aspect_ratio'] else 0.0
        else:
            expressions['surprised'] = 0.0
        
        # Confused expression (based on asymmetry and eyebrow position)
        if len(eyes) >= 2:
            eye_heights = [ey for _, ey, _, _ in eyes]
            height_diff = abs(eye_heights[0] - eye_heights[1])
            asymmetry = height_diff / face_roi[3]
            expressions['confused'] = min(1.0, asymmetry * 5.0) if asymmetry > self.expression_params['confused']['asymmetry'] else 0.0
        else:
            expressions['confused'] = 0.0
        
        # Stressed expression (based on eye movement and blink rate)
        if len(self.prev_eye_positions) > 0 and len(eyes) >= 2:
            eye_movement = sum(abs(curr - prev) for curr, prev in zip(eyes[0], self.prev_eye_positions[0])) / face_roi[2]
            expressions['stressed'] = min(1.0, eye_movement * 2.0) if eye_movement > self.expression_params['stressed']['eye_movement'] else 0.0
        else:
            expressions['stressed'] = 0.0
        
        # Update eye positions for next frame
        if len(eyes) >= 2:
            self.prev_eye_positions = eyes[:2]
        
        # Confident expression (based on face position and eye contact)
        face_center_y = face_roi[1] + face_roi[3] // 2
        frame_center_y = frame.shape[0] // 2
        posture_score = 1.0 - abs(face_center_y - frame_center_y) / (frame.shape[0] // 4)
        expressions['confident'] = max(0.0, min(1.0, posture_score))
        
        # Neutral expression (inverse of other expressions)
        other_expressions = sum(v for k, v in expressions.items() if k != 'neutral')
        expressions['neutral'] = max(0.0, 1.0 - other_expressions)
        
        # Smooth expressions using history
        self.expression_history.append(expressions)
        if len(self.expression_history) > 10:
            self.expression_history.pop(0)
        
        smoothed_expressions = {}
        for expr in expressions.keys():
            values = [h[expr] for h in self.expression_history]
            smoothed_expressions[expr] = sum(values) / len(values)
        
        return smoothed_expressions

    def get_interview_metrics(self, expressions: Dict[str, float]) -> Dict[str, float]:
        # Calculate derived metrics for the interview
        confidence_score = expressions['confident'] * 0.6 + expressions['happy'] * 0.2 + (1 - expressions['stressed']) * 0.2
        stress_level = expressions['stressed'] * 0.7 + expressions['confused'] * 0.3
        engagement_score = (1 - expressions['neutral']) * 0.5 + expressions['confident'] * 0.3 + expressions['happy'] * 0.2
        
        return {
            'confidence': min(1.0, max(0.0, confidence_score)),
            'stress_level': min(1.0, max(0.0, stress_level)),
            'engagement': min(1.0, max(0.0, engagement_score))
        }

    def draw_debug_info(self, frame: np.ndarray, face_roi: Optional[Tuple[int, int, int, int]], expressions: Dict[str, float]) -> np.ndarray:
        # Draw face rectangle
        if face_roi is not None:
            x, y, w, h = face_roi
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        
        # Draw expression probabilities
        y_offset = 30
        for expr, prob in expressions.items():
            text = f"{expr}: {prob:.2f}"
            cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            y_offset += 20
        
        return frame

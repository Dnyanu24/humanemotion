# voice_emotion.py

import random

def detect_emotion_from_voice():
    """
    Simulate voice emotion detection by returning dummy results.
    """
    emotions = ['happy', 'sad', 'angry', 'neutral', 'fear', 'disgust', 'surprise']
    
    # Generate random scores for each emotion
    emotion_scores = [
        {"label": emotion, "score": round(random.uniform(0.05, 1.0), 2)}
        for emotion in emotions
    ]
    
    # Sort by score descending
    emotion_scores.sort(key=lambda x: x["score"], reverse=True)
    
    return {"emotions": emotion_scores}

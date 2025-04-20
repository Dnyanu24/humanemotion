from flask import render_template, request, Blueprint
from transformers import pipeline
from models import Emotion
from app import db
from datetime import datetime
import matplotlib.pyplot as plt
import os
import uuid

main_routes = Blueprint('main_routes', __name__)

classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)

emotion_emoji = {
    "joy": "😄", "anger": "😠", "sadness": "😢",
    "fear": "😨", "surprise": "😲", "disgust": "🤢",
    "neutral": "😐"
}

mood_task_map = {
    "joy": "Work on creative or collaborative projects.",
    "anger": "Take a break or work on less stressful tasks.",
    "sadness": "Focus on simple, low-effort tasks.",
    "fear": "Review plans and checklists to ease anxiety.",
    "surprise": "Document ideas and explore new opportunities.",
    "disgust": "Step away from distressing content; reflect or reorganize.",
    "neutral": "Continue regular work or plan the day."
}

def plot_emotion_chart(probabilities):
    emotions = [e['label'] for e in probabilities]
    scores = [e['score'] for e in probabilities]

    plt.figure(figsize=(8, 4))
    plt.bar(emotions, scores, color='mediumseagreen')
    plt.xlabel('Emotions')
    plt.ylabel('Score')
    plt.title('Emotion Analysis')
    plt.ylim([0, 1])
    plt.tight_layout()

    if not os.path.exists("static"):
        os.makedirs("static")

    filename = f"emotion_chart_{uuid.uuid4().hex}.png"
    path = os.path.join("static", filename)
    plt.savefig(path)
    plt.close()
    return filename

@main_routes.route('/', methods=['GET', 'POST'])
def index():
    emotion = None
    score = None
    suggestion = None
    chart_filename = None
    emoji = None

    if request.method == 'POST':
        user_input = request.form['user_input']
        result = classifier(user_input)[0]
        top_emotion = max(result, key=lambda x: x['score'])

        emotion = top_emotion['label']
        score_val = top_emotion['score']
        score = f"{score_val:.2f}"
        suggestion = mood_task_map.get(emotion.lower(), "No suggestion available.")
        emoji = emotion_emoji.get(emotion.lower(), "")

        # Save to database
        new_emotion = Emotion(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_input=user_input,
            emotion=emotion,
            score=score_val
        )
        db.session.add(new_emotion)
        db.session.commit()

        chart_filename = plot_emotion_chart(result)

    return render_template("index.html",
                           emotion=emotion,
                           score=score,
                           suggestion=suggestion,
                           emoji=emoji,
                           chart_url=chart_filename)

@main_routes.route('/dashboard')
def dashboard():
    emotions = Emotion.query.all()

    if not emotions:
        return render_template("dashboard.html", entries=[], pie_chart=None, bar_chart=None)

    emotion_counts = {e.emotion: emotion_counts.get(e.emotion, 0) + 1 for e in emotions}

    # Pie Chart
    pie_path = "static/pie_chart.png"
    plt.figure(figsize=(6, 6))
    plt.pie(emotion_counts.values(), labels=emotion_counts.keys(), autopct='%1.1f%%', startangle=140)
    plt.title("Emotion Distribution")
    plt.tight_layout()
    plt.savefig(pie_path)
    plt.close()

    # Bar Chart
    bar_path = "static/bar_chart.png"
    plt.figure(figsize=(8, 4))
    plt.bar(emotion_counts.keys(), emotion_counts.values(), color='salmon')
    plt.title("Emotion Frequency")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(bar_path)
    plt.close()

    return render_template("dashboard.html",
                           entries=emotions,
                           pie_chart=pie_path.split('/')[-1],
                           bar_chart=bar_path.split('/')[-1])

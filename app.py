from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify, Response
from transformers import pipeline
import matplotlib.pyplot as plt
import os
import sqlite3
from datetime import datetime
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import cv2
from deepface import DeepFace
import numpy as np
import pandas as pd
import json
from utils.graph_plotter import create_emotion_graph
from voice_emotion import detect_emotion_from_voice
from flask_login import current_user

# Flask App Setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emotion_data.db'
app.config['SECRET_KEY'] = 'your_secret_key'

# Extensions Init
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Emotion Model
classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)

# Emotion Mappings
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

# Database Initialization
def init_db():
    conn = sqlite3.connect('emotion_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emotions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        user_input TEXT,
        emotion TEXT,
        score REAL
    )''')
    conn.commit()
    conn.close()


# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Emotion Chart Generator
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

    os.makedirs("static", exist_ok=True)
    filename = f"emotion_chart_{uuid.uuid4().hex}.png"
    path = os.path.join("static", filename)
    plt.savefig(path)
    plt.close()
    return filename

# ---------------- ROUTES ----------------

@app.route('/', methods=['GET', 'POST'])
def index():
    emotion = score = suggestion = chart_filename = emoji = None

    if request.method == 'POST':
        user_input = request.form['user_input']
        result = classifier(user_input)

        if result and result[0]:
            top_emotion = max(result[0], key=lambda x: x['score'])
            emotion = top_emotion['label']
            score_val = top_emotion['score']
            score = f"{score_val:.2f}"
            suggestion = mood_task_map.get(emotion.lower(), "No suggestion available.")
            emoji = emotion_emoji.get(emotion.lower(), "")

            conn = sqlite3.connect('emotion_data.db')
            c = conn.cursor()
            c.execute("INSERT INTO emotions (timestamp, user_input, emotion, score) VALUES (?, ?, ?, ?)",
                      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_input, emotion, score_val))
            conn.commit()
            conn.close()

            chart_filename = plot_emotion_chart(result[0])

    return render_template("index.html",
                           emotion=emotion,
                           score=score,
                           suggestion=suggestion,
                           emoji=emoji,
                           chart_url=chart_filename)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(username=username, email=email, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created!', 'success')
            return redirect(url_for('login'))
        except:
            flash('Username or email already exists.', 'danger')

    return render_template('signup.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your credentials.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('emotion_data.db')
    df = pd.read_sql_query("SELECT * FROM emotions", conn)
    conn.close()

    if df.empty:
        return render_template(
            "dashboard.html",
            user=current_user,  # <-- ✅ you were missing this in the empty case
            entries=[],
            pie_chart=None,
            bar_chart=None
        )

    emotion_counts = df['emotion'].value_counts()

    pie_path = "static/pie_chart.png"
    plt.figure(figsize=(6, 6))
    plt.pie(emotion_counts, labels=emotion_counts.index, autopct='%1.1f%%', startangle=140)
    plt.title("Emotion Distribution")
    plt.tight_layout()
    plt.savefig(pie_path)
    plt.close()

    bar_path = "static/bar_chart.png"
    plt.figure(figsize=(8, 4))
    emotion_counts.plot(kind='bar', color='salmon')
    plt.title("Emotion Frequency")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(bar_path)
    plt.close()

    return render_template(
        "dashboard.html",
        user=current_user,
        entries=df.to_dict(orient='records'),
        pie_chart=pie_path,
        bar_chart=bar_path
    )

@app.route('/export_data', methods=['GET'])
@login_required
def export_data():
    conn = sqlite3.connect('emotion_data.db')
    df = pd.read_sql_query("SELECT * FROM emotions", conn)
    conn.close()

    if df.empty:
        return "No data available to export", 400

    export_path = "static/emotion_data.xlsx"
    df.to_excel(export_path, index=False, engine='openpyxl')
    return send_file(export_path, as_attachment=True)

# ---------- VOICE EMOTION ANALYSIS ----------
@app.route('/voice-analysis', methods=['GET', 'POST'])
@login_required
def voice_analysis():
    if request.method == 'POST':
        # Handle the audio file upload and process it
        audio_file = request.files['audio_file']
        
        # Example: Save the uploaded file temporarily
        audio_path = os.path.join('uploads', audio_file.filename)
        audio_file.save(audio_path)
        
        # Perform voice emotion analysis (e.g., using your existing model)
        # The result would be a dictionary or any other data format
        analysis_result = perform_voice_emotion_analysis(audio_path)
        
        # Generate a graph or some other analysis result to pass to the template
        graph = generate_voice_emotion_graph(analysis_result)  # e.g., using Seaborn
        
        # You could also pass the analysis result or graph image to the template
        return render_template('voice_analysis.html', result=analysis_result, graph=graph)

    return render_template('voice_analysis.html')


@app.route('/voice-analysis', methods=['GET'])
@login_required
def process_voice_analysis():
    result = detect_emotion_from_voice()
    if "error" in result:
        return jsonify(result)

    create_emotion_graph(result["emotions"])
    return render_template("voice_result.html", result=result, graph_path='static/graphs/voice_emotion.png')

# ---------- VIDEO EMOTION ANALYSIS ----------
@app.route('/video_analysis', methods=['GET', 'POST'])
def video_analysis():
    if request.method == 'POST':
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return jsonify({'error': 'Camera not available'})

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return jsonify({'error': 'Failed to capture frame'})

        try:
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            return jsonify({'emotion': result[0]['emotion']})
        except Exception as e:
            return jsonify({'error': str(e)})

    return render_template('video_analysis.html')

@app.route('/video_feed')
def video_feed():
    def gen_frames():
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        cap.release()
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/live_emotion_data')
def live_emotion_data():
    def generate():
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    continue

                try:
                    analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    dominant_emotion = analysis[0]['dominant_emotion']
                    emotion_probs = analysis[0]['emotion']

                    data = {
                        'emotion': dominant_emotion,
                        'probabilities': emotion_probs
                    }
                    yield f"data:{json.dumps(data)}\n\n"
                except Exception as e:
                    yield f"data:{json.dumps({'error': str(e)})}\n\n"
        finally:
            cap.release()

    return Response(generate(), mimetype='text/event-stream')

@app.route('/process_frame', methods=['POST'])
def process_frame():
    if 'frame' not in request.files:
        return jsonify({'error': 'No frame uploaded'}), 400

    file = request.files['frame']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        return jsonify({
            'emotion': analysis[0]['dominant_emotion'],
            'probabilities': analysis[0]['emotion']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------------- RUN APP ----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure SQLAlchemy tables like User are created
        init_db()        # Ensure raw SQLite 'emotions' table is created
    app.run(debug=True)

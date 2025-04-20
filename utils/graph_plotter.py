import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import os

def create_emotion_graph(emotion_scores, save_path='static/graphs/voice_emotion.png'):
    df = pd.DataFrame(emotion_scores)
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 5))
    sns.barplot(x='label', y='score', data=df, palette='coolwarm')
    plt.title("Voice-Based Emotion Scores")
    plt.ylim(0, 1)
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()

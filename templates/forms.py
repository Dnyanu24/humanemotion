from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class EmotionForm(FlaskForm):
    user_input = StringField('Enter your text:', validators=[DataRequired()])
    submit = SubmitField('Analyze Emotion')

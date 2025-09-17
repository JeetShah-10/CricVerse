from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired, Length

class StadiumOwnerApplicationForm(FlaskForm):
    stadium_name = StringField('Stadium Name', validators=[DataRequired(), Length(min=2, max=100)])
    stadium_location = StringField('Stadium Location', validators=[DataRequired(), Length(min=2, max=100)])
    business_document = FileField('Business Document (PDF)', validators=[DataRequired()])
    notes = TextAreaField('Additional Notes', validators=[Length(max=500)])
    submit = SubmitField('Submit Application')

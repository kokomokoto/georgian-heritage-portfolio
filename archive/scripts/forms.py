from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Email, ValidationError

class RegistrationForm(FlaskForm):
    name = StringField('სახელი', 
                      validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('ელ. ფოსტა', 
                       validators=[DataRequired(), Email()])
    password = PasswordField('პაროლი', 
                           validators=[DataRequired(), Length(min=4)])
    password2 = PasswordField('გაიმეორეთ პაროლი',
                            validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('რეგისტრაცია')

class LoginForm(FlaskForm):
    email = StringField('ელ. ფოსტა', 
                       validators=[DataRequired(), Email()])
    password = PasswordField('პაროლი', validators=[DataRequired()])
    submit = SubmitField('შესვლა')

class ForgotPasswordForm(FlaskForm):
    email = StringField('ელ. ფოსტა', 
                       validators=[DataRequired(), Email()])
    submit = SubmitField('პაროლის აღდგენა')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('ახალი პაროლი', 
                           validators=[DataRequired(), Length(min=4)])
    password2 = PasswordField('გაიმეორეთ ახალი პაროლი',
                            validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('პაროლის შეცვლა')
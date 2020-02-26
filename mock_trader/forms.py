from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from mock_trader.models import User, Portfolio_Item
from flask_login import current_user
from mock_trader.utils import lookup, usd
from mock_trader import bcrypt

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=2, max=255)])
    email = StringField('Email (for account recovery only)', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("That username is already in use. Please try another.")
    
    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError("That email is already in use. Please try another.")


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class QuoteForm(FlaskForm):
    symbol = StringField('Stock Symbol', validators=[DataRequired()], render_kw={"autofocus": True})
    submit = SubmitField('Get Quote')

class BuyForm(FlaskForm):
    symbol = StringField('Stock Symbol', validators=[DataRequired()])
    shares = StringField('Number of Shares', validators=[DataRequired(), Regexp('^[1-9]\d*$', message="Please enter a positive, whole number.")])
    submit = SubmitField('Buy Stock')

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        stock_data = lookup(self.symbol.data)
        if not stock_data:
            self.symbol.errors.append(f'Cannot find stock "{self.symbol.data.upper()}". Please try another.')
            return False
        else:
            user_cash = User.query.filter_by(id=current_user.id).first().cash
            cost = stock_data['latestPrice'] * int(self.shares.data)
            if cost > user_cash:
                self.shares.errors.append(f"This transaction costs {usd(cost)}. You only have {usd(user_cash)} in your account.")
                return False
        return True
            
class SellForm(FlaskForm):
    symbol = StringField('Stock Symbol', validators=[DataRequired()])
    shares = StringField('Number of Shares', validators=[DataRequired(), Regexp('^[1-9]\d*$', message="Please enter a positive, whole number.")])
    submit = SubmitField('Sell Stock')

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        stock_data = lookup(self.symbol.data)
        if not stock_data:
            self.symbol.errors.append(f'Cannot find stock "{self.symbol.data.upper()}". Please try another.')
            return False
        else:
            has_stock = Portfolio_Item.query.filter_by(user_id=current_user.id, stock=self.symbol.data.upper()).first()
            if has_stock:
                if int(self.shares.data) > has_stock.shares:
                    self.shares.errors.append(f'You do not own that many shares of {self.symbol.data.upper()}.')
                    return False
            else:
                self.shares.errors.append(f'You do not own any shares of {self.symbol.data.upper()}.')
                return False
        return True

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if not email:
            raise ValidationError("No user registered with that email address.")

class ResetTokenForm(FlaskForm):
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
                             DataRequired(), Length(min=8)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Reset Password')

    def validate_current_password(self, current_password):
        user = User.query.filter_by(id=current_user.id).first()
        if not bcrypt.check_password_hash(user.pw_hash, current_password.data):
            raise ValidationError("Incorrect password. Please try again.")


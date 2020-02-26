import requests
import os
from flask_mail import Message
from mock_trader import mail
from flask import url_for

def usd(value):
    """ Format value as dollar amt """
    return f"${value:,.2f}"

def lookup(symbol):
    """ Look up stock data by symbol """
    # api_key = os.environ.get('API_KEY')
    api_key = 'pk_337627f2c3e94b50ac2a52ee49fb92a7'
    try:
        r = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{symbol}/quote?token={api_key}")
        print(r)
        quote = r.json()
        return quote
    except:
        return None
    
def shorten_dec(value):
    """ Shortens long decimal values """
    return f"{value:,.5f}"

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender=os.environ.get('MAIL_USERNAME'), recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request, then simply ignore this email, and no changes will be made.
'''
    mail.send(msg)
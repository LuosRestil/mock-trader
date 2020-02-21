import os
from flask import Flask, render_template, url_for, request
from forms import RegistrationForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')


@app.route("/")
@app.route("/portfolio")
# @login_required
def home():
    return render_template('portfolio.html', title="Home")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if request.method == "GET":
        return render_template('register.html', title="Account Registration", form=form)
    else:
        # do something else
        return render_template('register.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "GET":
        return render_template('login.html', title='Login', form=form)
    else:
        # do something else
        return render_template('login.html')


if __name__ == ('__main__'):
    app.run()

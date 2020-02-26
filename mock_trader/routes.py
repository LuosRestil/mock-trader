import os
import decimal
import datetime
from flask import render_template, url_for, request, flash, redirect
from mock_trader import app, db, bcrypt
from mock_trader.models import User, Portfolio_Item, Transaction
from mock_trader.forms import RegistrationForm, LoginForm, QuoteForm, BuyForm, SellForm, RequestResetForm, ResetTokenForm, ResetPasswordForm
from mock_trader.utils import usd, lookup, shorten_dec, send_reset_email
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/portfolio")
@login_required
def portfolio():
    portfolio = Portfolio_Item.query.filter_by(user_id=current_user.id).all()
    cash = User.query.filter_by(id=current_user.id).first().cash
    stocks = []
    shares = []
    prices = []
    total_values = []
    net_worth = cash
    portfolio_length = len(portfolio)
    for i in range(portfolio_length):
        stocks.append(portfolio[i].stock)
        shares.append(portfolio[i].shares)
        stock_data = lookup(portfolio[i].stock)
        stock_price = stock_data['latestPrice']
        prices.append(usd(stock_price))
        total_value = decimal.Decimal(stock_price * portfolio[i].shares)
        net_worth += total_value
        total_values.append(usd(total_value))
    return render_template('portfolio.html', title="Portfolio", portfolio_length=portfolio_length, stocks=stocks, shares=shares, prices=prices, total_values=total_values, cash=usd(cash), net_worth=usd(net_worth))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash('You are already registered and logged in.', 'info')
        return redirect(url_for('portfolio'))
    form = RegistrationForm()
    if form.validate_on_submit():
        pw_hash = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, pw_hash=pw_hash)
        db.session.add(user)
        db.session.commit()
        flash(f'Registration successful! You may now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash('You are already registered and logged in.', 'info')
        return redirect(url_for('portfolio'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.pw_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            # next_page = request.args.get('next')
            return redirect(url_for('portfolio'))
        else:
            flash(f"Login unsuccessful. Please check username and password.", 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/quote', methods=["GET", "POST"])
@login_required
def quote():
    first_load = True
    symbol = ''
    stock_data = None
    form = QuoteForm()
    if form.validate_on_submit():
        symbol = form.symbol.data.upper()
        stock_data = lookup(symbol)
        first_load = False
        form.symbol.data = ""
    return render_template('quote.html', form=form, title="Stock Quote", stock_data=stock_data, first_load=first_load, usd=usd, shorten_dec=shorten_dec, symbol=symbol)

@app.route('/buy', methods=["GET", "POST"])
@login_required
def buy():
    form = BuyForm()
    if form.validate_on_submit():
        stock = form.symbol.data.upper()
        shares = int(form.shares.data)
        stock_data = lookup(stock)
        price = stock_data['latestPrice']
        total = decimal.Decimal(price * shares)
        user = User.query.filter_by(id=current_user.id).first()
        cash = user.cash
        cash -= total
        user.cash = cash
        transaction = Transaction(user_id=current_user.id, stock=stock, shares=shares, stock_price=price, total=total, transaction_type="BUY")
        db.session.add(transaction)
        user_portfolio = Portfolio_Item.query.filter_by(user_id=current_user.id).all()
        for row in user_portfolio:
            if row.stock == stock:
                update_shares = Portfolio_Item.query.filter_by(user_id=current_user.id, stock=stock).first()
                update_shares.shares = update_shares.shares + shares
                db.session.commit()
                flash('Stock purchased successfully!', 'success')
                return redirect(url_for('buy'))
        new_item = Portfolio_Item(user_id=current_user.id, stock=stock, shares=shares)
        db.session.add(new_item)
        db.session.commit()
        flash('Stock purchased successfully!', 'success')
        return redirect(url_for('buy'))
    return render_template('buy.html', form=form, title='Buy Stock')

@app.route('/sell', methods=["GET", "POST"])
@login_required
def sell():
    form = SellForm()
    if form.validate_on_submit():
        stock = form.symbol.data.upper()
        shares = int(form.shares.data)
        stock_data = lookup(stock)
        stock_price = stock_data['latestPrice']
        total = decimal.Decimal(stock_price * shares)
        transaction = Transaction(user_id=current_user.id, stock=stock, shares=shares, stock_price=stock_price, total=total, transaction_type="SELL")
        db.session.add(transaction)
        user = User.query.filter_by(id=current_user.id).first()
        cash = user.cash
        user.cash = cash + total
        user_stock = Portfolio_Item.query.filter_by(user_id=current_user.id, stock=stock).first()
        if user_stock.shares == shares:
            db.session.delete(user_stock)
        else:
            user_stock.shares -= shares
        db.session.commit()
        flash('Stock successfully sold.', 'success')
        return redirect(url_for('sell'))
    return render_template('sell.html', form=form, title='Sell Stock')
        
@app.route('/history')
@login_required
def history():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date_time.desc()).all()
    return render_template('history.html', title='Transaction History', transactions=transactions, usd=usd)

@app.route('/request_pw_reset', methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        logout_user()
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title="Request Password Reset", form=form)

@app.route('/reset_token/<token>', methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('portfolio'))
    user = User.verify_reset_token(token)
    if not user:
        flash('Password reset token invalid or expired.', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetTokenForm()
    if form.validate_on_submit():
        pw_hash = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.pw_hash = pw_hash
        db.session.commit()
        flash(f'Your password has been updated! You may now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title="Reset Password", form=form)

@app.route('/reset_password', methods=["GET", "POST"])
@login_required
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=current_user.id).first()
        pw_hash = bcrypt.generate_password_hash(
            form.new_password.data).decode('utf-8')
        user.pw_hash = pw_hash
        db.session.commit()
        flash('Password reset successful!', 'success')
        return redirect(url_for('portfolio'))

    return render_template('reset_password.html', title='Reset Password', form=form)


from urllib.parse import urlsplit

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
import sqlalchemy as sa

from app.forms import RegistrationForm, LoginForm
from app.models import User
from app import db, app



@app.route('/')
@app.route('/home')
@login_required
def home():
    return render_template('home.html', title="Home")

@app.route('/welcome')
def welcome():
    return render_template('welcome.html', title="Welcome")

@app.route('/register', methods=['GET', 'POST'])
def register():

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', title = 'Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('welcome'))

@app.route('/shop')
def shop():
    return render_template('shop.html', title="Shop")


if __name__ == '__main__':
    app.run(debug=True)
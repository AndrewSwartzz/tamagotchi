from flask import Flask, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required

from forms import RegistrationForm
from app.models import User
from app import db, app



@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title="Home")

@app.route('/welcome')
def welcome():
    return render_template('welcome.html', title="Welcome")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


if __name__ == '__main__':
    app.run(debug=True)
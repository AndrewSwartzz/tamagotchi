from urllib.parse import urlsplit

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
import sqlalchemy as sa

from app.forms import RegistrationForm, LoginForm
from app.models import User
from app import db, app

#return a dict with the current player's money and stats

def _dump_stats(user):
    return {
        "money":      user.money,
        "health":     user.health,
        "happiness":  user.happiness,
        "hunger":     user.hunger,
        "energy":     user.energy,
    }


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


@app.route('/api/feed', methods=['POST'])
@login_required
def api_feed():
    pet = current_user
    if pet.hunger < 100:
        pet.hunger = min(100, pet.hunger + 20)
        pet.money  += 2          # reward for caring
        db.session.commit()
    return jsonify(_dump_stats(pet))

@app.route('/api/decay', methods=['POST'])
@login_required
def api_decay():
    pet = current_user
    pet.health = max(0, pet.health - 1)
    pet.happiness = max(0, pet.happiness - 1)
    pet.energy = max(0, pet.energy - 1)
    pet.hunger = min(100, pet.hunger - 1)
    db.session.commit()
    return jsonify(_dump_stats(pet))

@app.route('/api/buy', methods=['POST'])
@login_required
def api_buy():
    data = request.get_json() or {}
    item = data.get('item')
    prices = {"Food": 10, "Collar": 5, "Toy": 3}
    price = prices.get(item, 0)

    pet = current_user
    success = False
    if price and pet.money >= price:
        pet.money -= price
        if item == 'Food':
            pet.hunger = min(100, pet.hunger + 10)
        else:
            pet.happiness = min(100, pet.happiness + 10)
        db.session.commit()
        success = True
    return jsonify({**_dump_stats(pet), "success": success})

@app.route('/api/stats')
@login_required
def api_stats():
    return jsonify(_dump_stats(current_user))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('welcome'))

@app.route('/shop')
@login_required
def shop():
    return render_template('shop.html', title='Shop')

if __name__ == '__main__':
    app.run(debug=True)
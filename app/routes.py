from datetime import datetime
from urllib.parse import urlsplit

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
import sqlalchemy as sa

from app.forms import RegistrationForm, LoginForm
from app.models import User, Pet, Graveyard, Store, Inventory, init_user_inventory
from app import db, app, login


@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def _dump_stats(user):
    pet = Pet.query.filter_by(user_id=current_user.id).first()

    return {
        "money": current_user.currency,
        "health": pet.health,
        "cleanliness": pet.cleanliness,
        "hunger": pet.hunger,
    }


def kill_pet(pet, cause="natural causes"):
    grave = Graveyard(
        pet_name=pet.username,
        pet_type=pet.pet_type,
        cause_of_death=cause,
        original_pet_id=pet.id,
        user_id=current_user.id
    )
    db.session.add(grave)
    db.session.delete(pet)
    db.session.commit()


@app.route('/')
@app.route('/home')
@login_required
def home():
    pet = Pet.query.filter_by(user_id=current_user.id).first()

    if pet:
        return render_template('home.html', pet=pet)
    else:
        return redirect(url_for('adopt'))


@app.route('/welcome')
def welcome():
    return render_template('welcome.html', title="Welcome")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            currency=0
        )
        user.set_password(form.password.data)
        db.session.add(user)

        init_user_inventory(user)

        db.session.commit()
        flash('Account created successfully!')
        return redirect(url_for('login'))
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
    return render_template('login.html', title='Sign In', form=form)


@app.route('/api/feed', methods=['POST'])
@login_required
def api_feed():
    pet = Pet.query.filter_by(user_id=current_user.id).first()
    if not pet:
        return jsonify({"error": "No pet found!"}), 400

    if pet.hunger < 20:
        return jsonify({
            **(_dump_stats(current_user)),
            "message": "Tamagotchi is not hungry!"
        })

    pet.hunger = max(0, pet.hunger - 20)
    current_user.currency += 2
    db.session.commit()

    return jsonify(_dump_stats(current_user))

@app.route('/api/clean', methods=['POST'])
@login_required
def api_clean():
    pet = Pet.query.filter_by(user_id=current_user.id).first()

    if pet.cleanliness > 80:
        return jsonify({
            **(_dump_stats(current_user)),
            "message": "Tamagotchi is clean already!"
        })

    pet.cleanliness = max(0, pet.cleanliness + 20)
    current_user.currency += 2
    db.session.commit()

    return jsonify(_dump_stats(current_user))


@app.route('/api/decay', methods=['POST'])
@login_required
def api_decay():
    pet = Pet.query.filter_by(user_id=current_user.id).first()

    if pet.health <= 0:
        kill_pet(pet)
        db.session.commit()
        return jsonify({
            "status": "dead",
            "message": f"{pet.username} has passed away",
            "redirect": url_for('death_screen')
        })

    # Normal decay logic
    pet.cleanliness = max(0, pet.cleanliness - 1)
    pet.hunger = min(100, pet.hunger + 1)

    if pet.cleanliness < 20:
        pet.health = max(0, pet.health - 1)
    elif pet.cleanliness > 20:
        pet.health = min(100, pet.health + 1)

    if pet.hunger > 80:
        pet.health = max(0, pet.health - 1)
    elif pet.hunger < 80:
        pet.health = min(100, pet.health + 1)


    db.session.commit()

    return jsonify(_dump_stats(current_user))

@app.route('/graveyard')
@login_required
def graveyard():
    graves = Graveyard.query.filter_by(user_id=current_user.id)\
                           .order_by(Graveyard.death_time.desc())\
                           .all()
    return render_template('graveyard.html', pets=graves)



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
    return render_template('shop.html')


@app.route('/adopt', methods=['GET', 'POST'])
@login_required
def adopt():
    if request.method == 'POST':
        selected_pet = request.form.get('pet')
        if selected_pet:
            session['selected_pet'] = selected_pet  # Store the pet type in session
            return redirect(url_for('name_pet'))

    return render_template('adoption.html', title='Adopt')


@app.route('/name_pet', methods=['GET', 'POST'])
@login_required
def name_pet():
    selected_pet_type = session.get('selected_pet', 'duck')

    if request.method == 'POST':
        pet_name = request.form.get('pet_name')
        if pet_name:
            if current_user.pet:
                return render_template('name_pet.html',
                                       selected_pet=selected_pet_type,
                                       error="You already have a pet!")


            new_pet = Pet(
                username=pet_name,
                pet_type=selected_pet_type,
                personality="Friendly",
                clothing="Basic",
                hunger=80,
                cleanliness=80,
                health=100,
                mood="Happy",
                user_id=current_user.id,
                alive=True
            )

            try:
                db.session.add(new_pet)
                store = Store()
                db.session.add(store)
                db.session.commit()
                session.pop('selected_pet', None)
                return redirect(url_for('home'))
            except Exception as e:
                db.session.rollback()
                return render_template('name_pet.html',
                                       selected_pet=selected_pet_type,
                                       error=str(e))

    return render_template('name_pet.html',
                           selected_pet=selected_pet_type)


@app.route('/death-screen')
@login_required
def death_screen():
    last_pet = Graveyard.query.filter_by(user_id=current_user.id)\
                             .order_by(Graveyard.death_time.desc())\
                             .first()
    return render_template('death_screen.html', pet=last_pet)


@app.route('/api/shop/items')
@login_required
def api_shop_items():
    store = Store.query.first()
    if not store:
        store = Store()
        db.session.add(store)
        db.session.commit()

    return jsonify({
        'toys': store.toys,
        'hats': store.hats,
        'collars': store.collars
    })

@app.route('/api/shop/buy', methods=['POST'])
@login_required
def buy_item():
    data = request.get_json(force=True)  # <-- force=True avoids silent fail on invalid JSON
    category = data.get('category')
    item_name = data.get('item')

    if not category or not item_name:
        return jsonify({"error": "Missing category or item"}), 400

    store = Store.query.first()
    if not store:
        return jsonify({"error": "Store not found"}), 500

    category_items = getattr(store, category, {})
    item = category_items.get(item_name)

    if not item:
        return jsonify({"error": "Item not found"}), 404

    price = item['price']

    if current_user.currency < price:
        return jsonify({"error": "Not enough currency"}), 400

    current_user.currency -= price

    inventory = Inventory.query.filter_by(user_id=current_user.id).first()
    inventory_items = getattr(inventory, category, [])
    inventory_items.append({
        "name": item_name,
        "displayName": item['displayName'],
        "price": price
    })
    setattr(inventory, category, inventory_items)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Purchased {item['displayName']}!",
        "currency": current_user.currency,
        "inventory": inventory_items
    })



@app.route('/debug/auth')
def debug_auth():
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'user': current_user.username if current_user.is_authenticated else None
    })


if __name__ == '__main__':
    app.run(debug=True)

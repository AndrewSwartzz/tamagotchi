from datetime import datetime
from urllib.parse import urlsplit

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
import sqlalchemy as sa

from app.forms import RegistrationForm, LoginForm
from app.models import User, Pet, Graveyard, Store, Inventory, init_user_inventory
from app import db, app, login, mail
from flask_mail import Message
from threading import Thread


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
        "happiness": pet.happiness
    }


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_pet_death_email(user, pet_name, cause):
    subject = f"Your Tamagotchi {pet_name} has passed away"
    sender = app.config['MAIL_DEFAULT_SENDER']
    recipients = [user.email]

    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = f"""
    Dear {user.username},

    We're sorry to inform you that your Tamagotchi {pet_name} 
    has passed away due to {cause}.

    You can visit the memorial garden at:
    {url_for('graveyard', _external=True)}

    Sincerely,
    The Tamagotchi Team
    """

    Thread(target=send_async_email, args=(app, msg)).start()


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

    send_pet_death_email(current_user._get_current_object(), pet.username, cause)

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

@app.route('/api/play', methods=['POST'])
@login_required
def api_play():
    pet = Pet.query.filter_by(user_id=current_user.id).first()

    if pet.happiness > 80:
        return jsonify({
            **(_dump_stats(current_user)),
            "message": "Tamagotchi is happy already!"
        })

    pet.happiness = max(0, pet.happiness + 20)
    current_user.currency += 2
    db.session.commit()

    return jsonify(_dump_stats(current_user))

@app.route('/api/decay', methods=['POST'])
@login_required
def api_decay():
    pet = Pet.query.filter_by(user_id=current_user.id).first()

    if not pet:
        return redirect(url_for('adopt'))

    if pet.health <= 0:
        kill_pet(pet)
        db.session.commit()
        return jsonify({
            "status": "dead",
            "message": f"{pet.username} has passed away",
            "redirect": url_for('death_screen')
        })

    pet.cleanliness = max(0, pet.cleanliness - 1)
    pet.happiness = max(0, pet.happiness - 1)
    pet.hunger = min(100, pet.hunger + 1)

    if pet.cleanliness < 20:
        pet.health = max(0, pet.health - 1)
    elif pet.cleanliness > 20:
        pet.health = min(100, pet.health + 1)

    if pet.happiness < 20:
        pet.health = max(0, pet.health - 1)
        if pet.mood != 'Sad':
            pet.mood = 'Sad'
    elif pet.happiness > 20:
        if pet.mood == 'Sad':
            pet.mood = 'Happy'
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
    pet = Pet.query.filter_by(user_id=current_user.id).first()
    if pet:
        return redirect(url_for('home'))
    if request.method == 'POST':
        selected_pet = request.form.get('pet')
        if selected_pet:
            session['selected_pet'] = selected_pet  # Store the pet type in session
            return redirect(url_for('name_pet'))

    return render_template('adoption.html', title='Adopt')


@app.route('/name_pet', methods=['GET', 'POST'])
@login_required
def name_pet():
    pet = Pet.query.filter_by(user_id=current_user.id).first()
    if pet:
        return redirect(url_for('home'))
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
                happiness=100,
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
    try:
        data = request.get_json()
        category = data.get('category')
        item_name = data.get('item')
        inventory = Inventory.query.filter_by(user_id=current_user.id).first()

        if not category or not item_name:
            return jsonify({"error": "Missing category or item"}), 400

        db.session.refresh(current_user)
        if inventory:
            db.session.refresh(inventory)

        store = Store.query.first()
        store_items = getattr(store, category, {})
        if item_name not in store_items:
            return jsonify({"error": "Item not found"}), 404

        if inventory:
            items = getattr(inventory, category, []) or []
            if item_name in items:
                return jsonify({
                    "error": f"You already own this {category[:-1]}!",
                    "code": "duplicate_item"
                }), 400

        price = store_items[item_name]['price']

        if current_user.currency < price:
            return jsonify({"error": "Not enough currency"}), 400

        if not inventory:
            inventory = Inventory(
                user_id=current_user.id,
                toys=[],
                hats=[],
                collars=[]
            )
            db.session.add(inventory)
            db.session.flush()

        items = getattr(inventory, category, []) or []
        new_items = items.copy()
        new_items.append(item_name)
        setattr(inventory, category, new_items)

        current_user.currency -= price

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(inventory, category)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Purchased {store_items[item_name]['displayName']}!",
            "currency": current_user.currency,
            "inventory": new_items
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/inventory')
@login_required
def inventory():
    inventory = Inventory.query.filter_by(user_id=current_user.id).first()
    if not inventory:
        inventory = Inventory(
            user_id=current_user.id,
            toys=[],
            hats=[],
            collars=[]
        )
        db.session.add(inventory)
        db.session.commit()

    store = Store.query.first()
    if not store:
        store = Store()
        db.session.add(store)
        db.session.commit()

    inventory_data = {
        'toys': [],
        'hats': [],
        'collars': []
    }

    for category in ['toys', 'hats', 'collars']:
        items = getattr(inventory, category, [])
        for item_name in items:
            store_item = getattr(store, category, {}).get(item_name)
            display_name = store_item['displayName'] if store_item else item_name
            inventory_data[category].append({
                'name': item_name,
                'displayName': display_name
            })

    return render_template('inventory.html',
                           inventory=inventory_data,
                           currency=current_user.currency)


@app.route('/api/inventory/use', methods=['POST'])
@login_required
def use_inventory_item():
    try:
        data = request.get_json()
        category = data.get('category')
        item_name = data.get('item')

        if not category or not item_name:
            return jsonify({"error": "Missing category or item"}), 400

        inventory = Inventory.query.filter_by(user_id=current_user.id).first()
        if not inventory:
            return jsonify({"error": "No inventory found"}), 404

        items = getattr(inventory, category, [])

        if item_name not in items:
            return jsonify({"error": "Item not in inventory"}), 404

        pet = Pet.query.filter_by(user_id=current_user.id).first()
        if category == 'hats' or category == 'collars':
            pet.clothing = item_name
            message = f"Equipped {item_name}!"
        elif category == 'toys':
            pet.toy = item_name
            pet.mood = "Playful"
            message = f"Used {item_name}! Your pet is happy!"
        else:
            message = f"Used {item_name}!"

        db.session.commit()

        return jsonify({
            "success": True,
            "message": message
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

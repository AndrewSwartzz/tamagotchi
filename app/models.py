from datetime import datetime, timezone
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login

class Pet(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    personality: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    clothing: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    hunger: so.Mapped[int] = so.mapped_column(sa.Integer())
    cleanliness: so.Mapped[int] = so.mapped_column(sa.Integer())
    health: so.Mapped[int] = so.mapped_column(sa.Integer())
    mood: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    pet_type: so.Mapped[str] = so.mapped_column(sa.String(64))
    alive: so.Mapped[bool] = so.mapped_column(sa.Boolean)

    # Foreign key to User (non-nullable)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), nullable=False)

    # Relationship with User (back_populates)
    user: so.Mapped['User'] = so.relationship(back_populates='pet')


class Inventory(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    toys: so.Mapped[list[str]] = so.mapped_column(sa.JSON, default=list)
    hats: so.Mapped[list[str]] = so.mapped_column(sa.JSON, default=list)
    collars: so.Mapped[list[str]] = so.mapped_column(sa.JSON, default=list)
    equipped_hat: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    equipped_collar: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    equipped_toy: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))

    # Relationship with User
    user_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('user.id'))
    user: so.Mapped['User'] = so.relationship(back_populates='inventory')

    def add_item(self, item_type: str, item_name: str):
        """Helper method to add items safely"""
        items = getattr(self, item_type)
        if item_name not in items:
            items.append(item_name)
            setattr(self, item_type, items)
            return True
        return False

    def equip_item(self, item_type: str, item_name: str):
        """Equip an item from inventory"""
        items = getattr(self, item_type)
        if item_name in items:
            setattr(self, f'equipped_{item_type}', item_name)
            return True
        return False

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    currency: so.Mapped[int] = so.mapped_column(sa.Integer(), nullable=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))


    # One-to-one relationship with Pet (uselist=False)
    pet: so.Mapped[Optional['Pet']] = so.relationship(
        back_populates='user',
        uselist=False  # Ensures one-to-one
    )

    # Relationship with Inventory
    inventory: so.Mapped[Optional['Inventory']] = so.relationship(
        back_populates='user',
        cascade='all, delete-orphan',
        single_parent=True,
        uselist=False
    )

    graves: so.Mapped[List['Graveyard']] = so.relationship(back_populates='user')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Store(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    toys: so.Mapped[dict] = so.mapped_column(sa.JSON, default={
        "blue_ball": 10,
        "pink_ball": 15,
        "football": 20
    })
    hats: so.Mapped[dict] = so.mapped_column(sa.JSON, default={
        "tree_hat": 25,
        "checker_hat": 30,
        "ic_hat": 35
    })
    collars: so.Mapped[dict] = so.mapped_column(sa.JSON, default={
        "red_collar": 20,
        "blue_green_collar": 25,
        "rainbow_collar": 50
    })

class Graveyard(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    pet_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    pet_type: so.Mapped[str] = so.mapped_column(sa.String(64))
    death_time: so.Mapped[datetime] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    cause_of_death: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    original_pet_id: so.Mapped[int]
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'))  # Add this

    # Relationship to User (optional but useful)
    user: so.Mapped['User'] = so.relationship(back_populates='graves')


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

def init_user_inventory(user: User):
    """Initialize inventory for a user if it doesn't exist"""
    if not user.inventory:
        inventory = Inventory(
            toys=[],  # Starter items
            collars=[],
            hats=[]
        )
        user.inventory = inventory
        db.session.add(inventory)
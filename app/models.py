from datetime import datetime, timezone
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin, current_user
from sqlalchemy import JSON
from sqlalchemy.orm import mapped_column, Mapped
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
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'))

    # Use proper SQLAlchemy 2.0 typing
    toys: so.Mapped[dict] = so.mapped_column(sa.JSON, default=dict)
    hats: so.Mapped[dict] = so.mapped_column(sa.JSON, default=dict)
    collars: so.Mapped[dict] = so.mapped_column(sa.JSON, default=dict)

    # Relationship (optional, since User has the main relationship)
    user: so.Mapped['User'] = so.relationship(back_populates='inventory')


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

    graves: so.Mapped[List['Graveyard']] = so.relationship(back_populates='user')

    inventory: so.Mapped['Inventory'] = so.relationship(
        backref='owner',
        uselist=False,  # One-to-one relationship
        cascade='all, delete-orphan')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



def default_toys():
    return {
        "Blue_Ball": {"price": 10, "displayName": "Blue Ball"},
        "Pink_Ball": {"price": 15, "displayName": "Pink Ball"},
        "Football": {"price": 20, "displayName": "Football"}
    }

def default_hats():
    return {
        "Tree_Hat": {"price": 25, "displayName": "Tree Hat"},
        "Checker_Hat": {"price": 30, "displayName": "Checker Hat"},
        "IC_Hat": {"price": 35, "displayName": "Ice Cream Hat"}
    }

def default_collars():
    return {
        "Red_Collar": {"price": 20, "displayName": "Red Collar"},
        "Blue_green_Collar": {"price": 25, "displayName": "Blue-Green Collar"},
        "Rainbow_Collar": {"price": 50, "displayName": "Rainbow Collar"}
    }

class Store(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    toys: Mapped[dict] = mapped_column(JSON, default=default_toys)
    hats: Mapped[dict] = mapped_column(JSON, default=default_hats)
    collars: Mapped[dict] = mapped_column(JSON, default=default_collars)

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
    if not user.inventory:  # Check if inventory exists
        inventory = Inventory(
            user_id=user.id,  # Explicitly set user_id
            toys=[],  # Empty list or starter items
            hats=[],
            collars=[]
        )
        db.session.add(inventory)
        # No need to explicitly assign to user.inventory
        # because backref handles it
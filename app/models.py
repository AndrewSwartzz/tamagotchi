from datetime import datetime, timezone
from hashlib import md5
from time import time
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import app, db, login

from app import db

class Pet(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    personality: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    clothing: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    hunger: so.Mapped[int] = so.mapped_column(sa.String(120))
    cleanliness: so.Mapped[int] = so.mapped_column(sa.String(120))
    health: so.Mapped[int] = so.mapped_column(sa.String(120))
    mood: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)

    user: so.Mapped['User'] = so.relationship(back_populates='pet')
    grave: so.Mapped['Graveyard'] = so.relationship(back_populates='pet')

class Inventory(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    toys: so.Mapped[list[str]] = so.mapped_column(sa.JSON, default=list)
    hats: so.Mapped[list[str]] = so.mapped_column(sa.JSON, default=list)
    collars: so.Mapped[list[str]] = so.mapped_column(sa.JSON, default=list)

    user: so.Mapped['User'] = so.relationship(back_populates='inventory')

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    currency: so.Mapped[int] = so.mapped_column(sa.String(120), nullable=True)

    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))

    pet_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Pet.id), nullable=True)
    inventory_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Inventory.id), nullable=True)



    pet: so.Mapped['Pet'] = so.relationship(back_populates='user')
    inventory: so.Mapped['Inventory'] = so.relationship(back_populates='user')



    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Store(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    toys: so.Mapped[list[str]] = so.mapped_column(sa.JSON, default=list)
    hats: so.Mapped[list[str]] = so.mapped_column(sa.JSON, default=list)
    collars: so.Mapped[list[str]] = so.mapped_column(sa.JSON, default=list)

class Graveyard(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    pet_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Pet.id))

    pet: so.Mapped['Pet'] = so.relationship(back_populates='grave')

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))





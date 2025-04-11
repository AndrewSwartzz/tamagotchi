from datetime import datetime, timezone
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from sqlalchemy import ARRAY
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login


class User(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    password: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                            unique=True)
    currency: so.Mapped[int] = so.mapped_column(primary_key=True)



    pet: so.WriteOnlyMapped['pet'] = so.relationship(
        back_populates='Pet')

    past_pets: so.WriteOnlyMapped['past_pets'] = so.relationship(
        back_populates='past_pets')

    inventory: so.WriteOnlyMapped['inventory'] = so.relationship(
        back_populates='inventory')

    def __repr__(self):
        return 'Series: {}'.format(self.name)
from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Base class for ORM models
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    peeps: Mapped[List['Peep']] = relationship(back_populates='user', cascade='all, delete-orphan')
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False, onupdate=func.now())


class Peep(Base):
    __tablename__ = 'peeps'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    # This is the actual foreign key at the database level
    # We need the ondelete='cascade' on the Foreign key so the constraints are actually at the database level (otherwise
    # they are only at the Python-level). Check the table DDL to confirm that an `ON DELETE CASCADE` is actually there.
    # The reason is that if we don't do it this way, then if in sqlalchemy we delete the "wrong" way, which is:
    # >>> session.query(Peep).filter(...).delete()
    # instead of
    # >>> peep = session.query(Peep).filter(...).first()
    # >>> session.delete(peep)
    # then the Python-level constraints won't be triggered, and because there aren't also DB level constraints, deleting a
    # parent object will fail if it has related child data; the DB will return a "referential integrity" error.

    # So TLDR: use this to have ON DELETE constraints at the DB level, and in the code make sure to use the second
    # method to delete an object.
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='cascade'),
                                          nullable=False)
    # This is a Python-level field to refer to the related object directly
    user: Mapped['User'] = relationship(back_populates='peeps')
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False, onupdate=func.now())


class Follows(Base):
    __tablename__ = 'follows'

    follower_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='cascade'),
                                              primary_key=True)
    followee_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='cascade'),
                                              primary_key=True)

from datetime import datetime

from sqlalchemy import create_engine, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, scoped_session, sessionmaker

# Create a global engine and session factory
DATABASE_URL = 'postgresql+psycopg2://peep_user:peep_password@postgres/peep_python'

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=True)

# Create a thread-safe scoped session factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base class for ORM models
Base = declarative_base()


# TODO: Refactor this into its own file
class Peep(Base):
    __tablename__ = 'peeps'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False, onupdate=func.now())


class User(Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False, onupdate=func.now())


def get_db_session():
    """
    Dependency or utility function to provide a database session.
    Ensures that sessions are properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize the database (useful for creating tables)
def init_db():
    """
    Initialize the database by creating all tables defined in ORM models.
    """
    Base.metadata.create_all(bind=engine)


init_db()

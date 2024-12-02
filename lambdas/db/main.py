import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .models import Base


class DBConfigException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f'{self.message}'


# Create a global engine and session factory
# On the GitHub actions CI, the hostname of the service container for the database is the label. Since in our workflow
# the service is named "postgres", the hostname here must also be "postgres"
def get_db_url():
    current_env = os.environ.get('PEEP_ENV')
    if not current_env:
        raise DBConfigException('PEEP_ENV environment variable is not set')

    env_file = '.env'
    if current_env == 'test':
        env_file += '.test'

    load_dotenv(env_file)

    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')

    if not user or not password:
        raise DBConfigException('DB_USER and DB_PASSWORD environment variables not set')

    host = os.environ.get('DB_HOST')
    port = os.environ.get('DB_PORT')
    db_name = os.environ.get('DB_NAME')

    return f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}'


# Create the SQLAlchemy engine
engine = create_engine(get_db_url(), pool_pre_ping=True, echo=True)

# Create a thread-safe scoped session factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


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

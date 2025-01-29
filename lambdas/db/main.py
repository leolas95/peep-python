import logging
import os

import boto3
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

logger = logging.getLogger()
logger.setLevel("INFO")

from .models import Base

DB_ENGINE = 'postgresql'
DB_DRIVER = 'psycopg2'


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
        logger.error('PEEP_ENV environment variable is not set')
        raise DBConfigException('PEEP_ENV environment variable is not set')

    # Only for local development and test we use .env files. Other envs (ci, live) use managed secrets
    if current_env in ('local', 'test'):
        env_file = '.env.test' if current_env == 'test' else '.env'
        logger.info(f'Retrieving DB credentials from env file {env_file}')

        load_dotenv(env_file, verbose=True)
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
    else:
        logger.info('Retrieving DB credentials from Parameter Store')
        ssm = boto3.client('ssm')

        response = ssm.get_parameter(Name=f'/peep/{current_env}/db-user')
        user = response['Parameter']['Value']
        logger.info('found user param')

        response = ssm.get_parameter(Name=f'/peep/{current_env}/db-password')
        password = response['Parameter']['Value']
        logger.info('found password param')

        logger.info('DB credentials retrieved successfully')

    if not user or not password:
        logger.error('Could not retrieve DB credentials for user and password')
        raise DBConfigException(
            'DB_USER and DB_PASSWORD environment variables not set, or values not found in Parameter Store')

    host = os.environ.get('DB_HOST')
    port = os.environ.get('DB_PORT')
    db_name = os.environ.get('DB_NAME')

    logger.info('Connecting to database')
    return f'{DB_ENGINE}+{DB_DRIVER}://{user}:{password}@{host}:{port}/{db_name}'


# Create the SQLAlchemy engine
engine = create_engine(get_db_url(), pool_pre_ping=True, echo=True)

# Create a thread-safe scoped session factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def install_extensions():
    with SessionLocal() as session:
        session.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        session.commit()


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
    install_extensions()
    Base.metadata.create_all(bind=engine)


init_db()

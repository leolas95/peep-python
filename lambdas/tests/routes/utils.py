from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from starlette.testclient import TestClient

from lambdas.db.main import Base, User, get_db_session
from lambdas.main import app
from lambdas.routes.authentication.utils import check_logged_in, make_password


@pytest.fixture(name="session_fixture")
def session_fixture() -> Generator:
    engine = create_engine(
        "postgresql+psycopg2://peep_user:peep_password@localhost/test_peep_python",
        echo=True,
    )
    connection = engine.connect()
    transaction = connection.begin()

    Base.metadata.create_all(bind=connection)

    TestingSessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=connection))
    session = TestingSessionLocal()

    test_users = [
        User(name="leo1", email="leo1@email.com", username='leolas1', password=make_password('password1')),
        User(name="leo2", email="leo2@email.com", username='leolas2', password=make_password('password2')),
        User(name="leo3", email="leo3@email.com", username='leolas3', password=make_password('password3')),
        User(name="leo4", email="leo4@email.com", username='leolas4', password=make_password('password4')),
    ]

    session.begin_nested()
    session.bulk_save_objects(test_users)

    with session:
        yield session

    session.close()
    transaction.rollback()


@pytest.fixture(name='client')
def client(session_fixture: Session) -> Generator:
    def override_get_db_session():
        yield session_fixture

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[check_logged_in] = lambda: True
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

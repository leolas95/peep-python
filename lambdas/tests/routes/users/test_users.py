from typing import Generator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from lambdas.db.main import Base, User, get_db_session
from lambdas.main import app
from lambdas.routes.authentication.utils import check_logged_in, make_password


@pytest.fixture(name="session")
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
def client(session: Session) -> Generator:
    def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[check_logged_in] = lambda: True
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Here's the important detail to notice: we can require fixtures in other fixtures and also in the test functions.
# See: https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#why-two-fixtures
def test_create_user(client: TestClient, session: Session):
    body = {'name': 'user1', "email": "user1@email.com", 'username': 'user1', "password": "abc123"}
    response = client.post(
        "/users/auth/signup/",  # random non-existent UUID
        json=body
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_update_user(client: TestClient, session: Session):
    first_user = session.query(User).with_entities(User.id).first()

    body = {'name': 'new name'}
    response = client.patch(
        f'/users/{first_user.id}',
        json=body
    )

    updated_user = session.query(User).with_entities(User.name).where(User.id == first_user.id).one()
    assert response.status_code == status.HTTP_200_OK
    assert updated_user.name == 'new name'


def test_delete_user(client: TestClient, session: Session):
    first_user = session.query(User).with_entities(User.id).first()

    response = client.delete(f'/users/{first_user.id}')

    assert response.status_code == status.HTTP_200_OK

    deleted_user = session.query(User).where(User.id == first_user.id).one_or_none()
    assert deleted_user is None

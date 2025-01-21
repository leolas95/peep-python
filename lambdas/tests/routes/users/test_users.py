import json

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from lambdas.db import User
from lambdas.tests.routes.users.utils import follow_user
from lambdas.tests.routes.utils import client, session_fixture


# Here's the important detail to notice: we can require fixtures in other fixtures and also in the test functions.
# See: https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#why-two-fixtures
def test_create_user(client: TestClient, session_fixture: Session):
    body = {'name': 'user1', "email": "user1@email.com", 'username': 'user1', "password": "abc123"}
    response = client.post(
        "/users/auth/signup/",
        json=body
    )
    assert response.content is not None
    parsed_body = json.loads(response.content)
    assert parsed_body['statusCode'] == status.HTTP_201_CREATED


def test_update_user(client: TestClient, session_fixture: Session):
    first_user = session_fixture.query(User).with_entities(User.id).first()

    body = {'name': 'new name'}
    response = client.patch(
        f'/users/{first_user.id}',
        json=body
    )

    updated_user = session_fixture.query(User).with_entities(User.name).where(User.id == first_user.id).one()
    assert response.status_code == status.HTTP_200_OK
    assert updated_user.name == 'new name'


def test_delete_user(client: TestClient, session_fixture: Session):
    first_user = session_fixture.query(User).with_entities(User.id).first()

    response = client.delete(f'/users/{first_user.id}')

    assert response.status_code == status.HTTP_200_OK

    deleted_user = session_fixture.query(User).where(User.id == first_user.id).one_or_none()
    assert deleted_user is None


def test_follow(client: TestClient, session_fixture: Session):
    follower = session_fixture.query(User).where(User.username == 'leolas1').with_entities(User.id).first()
    followee = session_fixture.query(User).where(User.username == 'leolas2').with_entities(User.id).first()

    follow_user(client, follower.id, followee.id)


def test_unfollow(client: TestClient, session_fixture: Session):
    follower = session_fixture.query(User).where(User.username == 'leolas1').with_entities(User.id).first()
    followee = session_fixture.query(User).where(User.username == 'leolas2').with_entities(User.id).first()

    # First follow
    follow_user(client, follower.id, followee.id)

    # Then unfollow
    body = {'followee_id': str(followee.id)}
    response = client.post(
        f'/users/{follower.id}/unfollow',
        json=body
    )
    assert response.status_code == status.HTTP_200_OK


def test_fetch_timeline(client: TestClient, session_fixture: Session):
    follower = session_fixture.query(User).where(User.username == 'leolas1').with_entities(User.id).first()
    followee = session_fixture.query(User).where(User.username == 'leolas2').with_entities(User.id).first()

    # First follow
    follow_user(client, follower.id, followee.id)

    # Now test the actual timeline feature
    response = client.get(f'users/{follower.id}/timeline')

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    assert 'timeline' in response_json

    timeline = response_json['timeline']
    assert len(timeline) > 0

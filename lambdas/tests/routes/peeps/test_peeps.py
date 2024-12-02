from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from lambdas.db import Peep
from lambdas.tests.routes.utils import client, session_fixture


def test_create_peep(client: TestClient, session_fixture: Session):
    test_id = 'test user id'
    body = {'content': 'test peep', 'user_id': test_id}
    response = client.post(
        "/peeps/",
        json=body
    )

    # check response has id
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert 'peep' in response_json
    assert 'id' in response_json['peep']

    # check new peep on db
    peep_id = response_json['peep']['id']
    new_peep = session_fixture.query(Peep).filter_by(id=peep_id).one_or_none()

    assert new_peep is not None


def test_find_one(client: TestClient, session_fixture: Session):
    # Get any first peep to call the API with its id
    first_peep = session_fixture.query(Peep).with_entities(Peep.id).first()

    response = client.get(f'/peeps/{first_peep.id}')
    assert response.status_code == status.HTTP_200_OK


def test_delete_peep(client: TestClient, session_fixture: Session):
    first_peep = session_fixture.query(Peep).with_entities(Peep.id).first()

    response = client.delete(f'/peeps/{first_peep.id}')

    assert response.status_code == status.HTTP_200_OK

    deleted_peep = session_fixture.query(Peep).where(Peep.id == first_peep.id).one_or_none()
    assert deleted_peep is None

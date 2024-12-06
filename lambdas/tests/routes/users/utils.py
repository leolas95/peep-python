from fastapi import status
from fastapi.testclient import TestClient


def follow_user(client: TestClient, followee_id: str, follower_id: str):
    body = {'followee_id': str(followee_id)}
    response = client.post(
        f'/users/{follower_id}/follow',
        json=body
    )
    assert response.status_code == status.HTTP_200_OK

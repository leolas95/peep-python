from datetime import datetime, timezone, timedelta

import jwt
import pytest

from lambdas.routes.authentication.utils import validate_token, create_access_token, SIGNING_KEY, ALGORITHM


def test_should_return_none_for_invalid_token():
    result = validate_token('invalid.jwt')
    assert result is None


def test_should_return_none_when_username_is_none():
    token = create_access_token({'sub': None})
    result = validate_token(token)
    assert result is None


def test_should_return_username_for_valid_token():
    token = create_access_token({'sub': 'test username'})
    result = validate_token(token)
    assert result == 'test username'


def test_should_return_none_when_username_is_empty_string():
    token = create_access_token({'sub': ''})
    result = validate_token(token)
    assert result is None


def test_should_create_token_with_default_expiry():
    token = create_access_token({'sub': 'test username'})
    payload = jwt.decode(token, SIGNING_KEY, algorithms=[ALGORITHM])
    assert 'exp' in payload

    # Check expiry is ~15 minutes (the default) from now
    exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
    expected_exp = datetime.now(timezone.utc) + timedelta(minutes=15)

    assert exp == pytest.approx(exp, expected_exp)


def test_should_create_token_with_30_minutes_expiry():
    token = create_access_token({'sub': 'test username'}, expires_delta=timedelta(minutes=30))
    payload = jwt.decode(token, SIGNING_KEY, algorithms=[ALGORITHM])
    assert 'exp' in payload

    # Check expiry is ~30 minutes from now
    actual_exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
    expected_exp = datetime.now(timezone.utc) + timedelta(minutes=30)

    difference = expected_exp - actual_exp
    tolerance = timedelta(seconds=1)
    assert difference < tolerance

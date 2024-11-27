from lambdas.routes.authentication.utils import validate_token, create_access_token


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

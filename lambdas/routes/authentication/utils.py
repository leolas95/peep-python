import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from lambdas.db import User, get_db_session

logger = logging.getLogger()
logger.setLevel("INFO")

JWT_SIGNING_KEY = 'ab594818b3aadd5c954486ff2951563e6e154848bc4449ca3626235c747bc701'
JWT_SIGNING_ALGORITHM = 'HS256'

# tokenUrl is the relative URL from where to get the JWT token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def check_password(username: str, password: str, db: Session = Depends(get_db_session)):
    user = find_user(username, db)
    if user is None:
        return False
    input_password_bytes = password.encode('utf-8')
    stored_password_bytes = user.password.encode('utf-8')
    if not bcrypt.checkpw(input_password_bytes, stored_password_bytes):
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SIGNING_KEY, algorithm=JWT_SIGNING_ALGORITHM)
    return encoded_jwt


# Get the credentials from the token, also validating the token on the way
def validate_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SIGNING_KEY, algorithms=[JWT_SIGNING_ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username == '':
            return None
    except InvalidTokenError:
        return None

    return username


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           db: Session = Depends(get_db_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = validate_token(token)
    if username is None:
        raise credentials_exception

    user = find_user(username, db)
    if user is None:
        raise credentials_exception
    return user


def find_user(username: str, db: Session = Depends(get_db_session)) -> User | None:
    return db.query(User).filter(User.username == username).first()


# Because of the dependency on oauth2_scheme, FastAPI makes sure that if this function is called, the token is present
# in the Authorization Header. See: https://fastapi.tiangolo.com/tutorial/security/first-steps/#what-it-does
# But decoding and making sure the token is actually valid is our job, but at least we don't have to check the headers manually.
async def check_logged_in(token: Annotated[str, Depends(oauth2_scheme)]) -> bool:
    if validate_token(token) is None:
        return False

    return True


def make_password(plain_password: str) -> str | None:
    try:
        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
        return hashed_password.decode('utf-8')
    except (TypeError, ValueError) as e:
        logger.error(f'Error hashing password', exc_info=True, extra={'exception': e})
        return None

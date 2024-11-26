from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status

from lambdas.db.main import get_db_session, User

SIGNING_KEY = 'ab594818b3aadd5c954486ff2951563e6e154848bc4449ca3626235c747bc701'
ALGORITHM = 'HS256'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def check_password(username: str, password: str, db: Session = Depends(get_db_session)):
    user = find_user(username, db)
    if user is None:
        return False
    if not password_context.verify(password, str(user.password)):
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SIGNING_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Get the credentials from the token, also validating the token on the way
def extract_credentials(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SIGNING_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
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
    username = extract_credentials(token)
    if username is None:
        raise credentials_exception

    user = find_user(username, db)
    if user is None:
        raise credentials_exception
    return user


def find_user(username: str, db: Session = Depends(get_db_session)) -> User | None:
    return db.query(User).filter(User.username == username).first()

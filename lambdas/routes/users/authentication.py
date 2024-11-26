from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db.main import get_db_session, User
from ...dtos.users import CreateResponseDTO, CreateRequestDTO

SIGNING_KEY = 'ab594818b3aadd5c954486ff2951563e6e154848bc4449ca3626235c747bc701'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
TOKEN_TYPE = 'bearer'


class Token(BaseModel):
    access_token: str
    token_type: str


# tokenUrl is the relative URL from where to get the JWT token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth")


@router.post('/signup', response_model=CreateResponseDTO)
async def signup(user: CreateRequestDTO, db: Session = Depends(get_db_session)):
    hashed_password = password_context.hash(user.password)
    new_user = User(name=user.name, email=user.email, username=user.username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user, attribute_names=['id', 'name', 'email', 'username'])
    return {
        'message': 'User created successfully',
        'user': {
            'id': str(new_user.id),
            'name': new_user.name,
            'email': new_user.email,
            'username': new_user.username
        }
    }


# Because of the OAuth2PasswordRequestForm dependency, this must be called with a Form body
@router.post('/login')
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db_session)):
    user = check_password(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type=TOKEN_TYPE)


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


# Get the credentials from the token, checking if it's a valid token on the way
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


class UserInfoDTO(BaseModel):
    id: str
    name: str
    email: str
    username: str


# Just to test that the login actually worked
@router.get('/me')
async def get_me(user: User = Depends(get_current_user)) -> UserInfoDTO:
    return UserInfoDTO(id=str(user.id), name=user.name, email=user.email, username=user.username)
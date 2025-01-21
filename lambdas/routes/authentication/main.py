import json
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from lambdas.db import User, get_db_session
from lambdas.dtos.users import CreateRequestDTO
from lambdas.routes.authentication.utils import check_password, create_access_token, get_current_user, \
    make_password

ACCESS_TOKEN_EXPIRE_MINUTES = 30
# This value is required for the password flow of OAuth2, it must be 'bearer'
TOKEN_TYPE = 'bearer'


class Token(BaseModel):
    access_token: str
    token_type: str


router = APIRouter(prefix="/auth")


@router.post('/signup')
async def signup(user: CreateRequestDTO, db: Session = Depends(get_db_session)):
    hashed_password = make_password(user.password)
    if hashed_password is None:
        return {
            'statusCode': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Error hashing password'}),
        }

    new_user = User(name=user.name, email=user.email, username=user.username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user, attribute_names=['id', 'name', 'email', 'username'])
    body = {
        'message': 'User created successfully',
        'user': {
            'id': str(new_user.id),
            'name': new_user.name,
            'email': new_user.email,
            'username': new_user.username
        },
    }
    return JSONResponse(content=body, status_code=status.HTTP_201_CREATED)


# Because of the OAuth2PasswordRequestForm dependency, the request body must be a Form. Due to OAuth2 spec, the
# form must contain username and password fields, and they must be named like that, other names are not accepted.
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


class UserInfoDTO(BaseModel):
    id: str
    name: str
    email: str
    username: str


# Just to test that the login actually worked
@router.get('/me')
async def get_me(user: User = Depends(get_current_user)) -> UserInfoDTO:
    return UserInfoDTO(id=str(user.id), name=user.name, email=user.email, username=user.username)

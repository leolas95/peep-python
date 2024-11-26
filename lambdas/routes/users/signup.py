from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from ...db.main import get_db_session, User
from ...dtos.users import CreateResponseDTO, CreateRequestDTO

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(prefix="/signup")


@router.post('', response_model=CreateResponseDTO)
async def signup(user: CreateRequestDTO, db: Session = Depends(get_db_session)):
    hashed_password = bcrypt.hash(user.password)
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

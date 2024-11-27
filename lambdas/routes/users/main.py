from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from lambdas.routes.authentication.main import router as authentication_router
from ..authentication.utils import check_logged_in
from ...db.main import get_db_session, User
from ...dtos.users import UpdateRequestDTO

router = APIRouter(prefix="/users", tags=["users"])
router.include_router(authentication_router)


@router.patch('/{user_id}')
async def update(user_id: str, user: UpdateRequestDTO, db: Session = Depends(get_db_session),
                 is_logged_in: bool = Depends(check_logged_in)):
    if not is_logged_in:
        raise HTTPException(status_code=401, detail='Not logged in', headers={'WWW-Authenticate': 'Bearer'})

    fields = extract_set_fields(user)
    if len(fields) == 0:
        raise HTTPException(status_code=400, detail='Body cannot be empty')

    count = db.query(User).filter(User.id == user_id).update(fields)
    if count == 0:
        raise HTTPException(status_code=404, detail='User not found')
    db.commit()

    return {'message': 'User successfully updated'}


@router.delete('/{user_id}')
async def delete(user_id: str, db: Session = Depends(get_db_session), is_logged_in: bool = Depends(check_logged_in)):
    if not is_logged_in:
        raise HTTPException(status_code=401, detail='Not logged in', headers={'WWW-Authenticate': 'Bearer'})
    
    count = db.query(User).filter(User.id == user_id).delete()
    if count == 0:
        raise HTTPException(status_code=404, detail='User not found')

    db.commit()
    return {'message': 'User successfully deleted'}


def extract_set_fields(body: BaseModel):
    fields = {}
    for key, value in body.model_dump().items():
        if value is not None:
            fields[key] = value

    return fields

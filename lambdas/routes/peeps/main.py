from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..authentication.utils import check_logged_in
from ...db import Peep, get_db_session
from ...dtos.peeps import CreateRequestDTO, CreateResponseDTO

router = APIRouter(prefix="/peeps", tags=["peeps"])


@router.post('', response_model=CreateResponseDTO)
async def create(peep: CreateRequestDTO, db: Session = Depends(get_db_session),
                 is_logged_in: bool = Depends(check_logged_in)):
    if not is_logged_in:
        raise HTTPException(status_code=401, detail='Not logged in', headers={'WWW-Authenticate': 'Bearer'})

    new_peep = Peep(**peep.model_dump())
    try:
        db.add(new_peep)
        db.commit()
        db.refresh(new_peep, attribute_names=['id', 'content'])
    except IntegrityError:
        db.rollback()
        return JSONResponse(status_code=400, content={'message': 'Invalid data'})
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={'message': 'Peep created successfully', 'peep': {'id': str(new_peep.id), 'content': peep.content}}
    )


@router.get('/{peep_id}')
async def find_one(peep_id: str, db: Session = Depends(get_db_session), is_logged_in: bool = Depends(check_logged_in)):
    if not is_logged_in:
        raise HTTPException(status_code=401, detail='Not logged in', headers={'WWW-Authenticate': 'Bearer'})

    peep = db.query(Peep).filter(Peep.id == peep_id).one_or_none()
    if peep is None:
        raise HTTPException(status_code=404, detail='Peep not found')

    return {'peep': peep}


@router.delete('/{peep_id}')
async def remove(peep_id: str, db: Session = Depends(get_db_session), is_logged_in: bool = Depends(check_logged_in)):
    if not is_logged_in:
        raise HTTPException(status_code=401, detail='Not logged in', headers={'WWW-Authenticate': 'Bearer'})

    peep = db.query(Peep).filter(Peep.id == peep_id).first()
    if peep is None:
        raise HTTPException(status_code=404, detail='Peep not found')

    db.delete(peep)
    db.commit()
    return {'message': 'Peep successfully removed'}

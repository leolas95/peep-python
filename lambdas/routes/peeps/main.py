from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .models import CreatePeep
from ...db.main import get_db_session, Peep

router = APIRouter(prefix="/peeps", tags=["peeps"])


@router.post('')
async def create(peep: CreatePeep, db: Session = Depends(get_db_session)):
    new_peep = Peep(content=peep.content)
    db.add(new_peep)
    db.commit()
    return {"message": "peep successfully created", 'id': new_peep.id}


@router.get('/{peep_id}')
async def find_one(peep_id: str, db: Session = Depends(get_db_session)):
    peep = db.query(Peep).filter(Peep.id == peep_id).one_or_none()
    if peep is None:
        raise HTTPException(status_code=404, detail='Peep not found')

    return {'peep': peep}


@router.delete('/{peep_id}')
async def remove(peep_id: str, db: Session = Depends(get_db_session)):
    count = db.query(Peep).filter(Peep.id == peep_id).delete()
    if count == 0:
        raise HTTPException(status_code=404, detail='Peep not found')
    db.commit()
    return {'message': 'Peep successfully removed'}

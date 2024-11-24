from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.main import get_db_session, Peep
from ...dtos.peeps import CreateRequestDTO, CreateResponseDTO

router = APIRouter(prefix="/peeps", tags=["peeps"])


@router.post('', response_model=CreateResponseDTO)
async def create(peep: CreateRequestDTO, db: Session = Depends(get_db_session)):
    new_peep = Peep(content=peep.content)
    db.add(new_peep)
    db.commit()
    db.refresh(new_peep)
    return {'message': 'Peep created successfully', 'peep': {'id': str(new_peep.id), 'content': peep.content}}


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

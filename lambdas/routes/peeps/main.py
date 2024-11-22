from fastapi import APIRouter
from .models import CreatePeep

router = APIRouter(prefix="/peeps", tags=["peeps"])

@router.post('')
async def create(peep: CreatePeep):
    print(peep)
    return {"message": "peep successfully created", 'data': peep.model_dump()}
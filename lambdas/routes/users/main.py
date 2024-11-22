from fastapi import APIRouter
from .models import CreateUser

router = APIRouter(prefix="/users", tags=["users"])

@router.post('')
async def create(user: CreateUser):
    return {"message": "user successfully created", 'data': user.model_dump()}
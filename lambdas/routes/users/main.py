from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from lambdas.routes.authentication.main import router as authentication_router
from ..authentication.utils import check_logged_in
from ...db import Follows, Peep, User, get_db_session
from ...dtos.users import FollowRequestDTO, UpdateRequestDTO

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

    # Deleting like this is better because it triggers the Python-level cascade constraints on deletion
    # See: https://stackoverflow.com/a/19245058
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')

    db.delete(user)
    db.commit()
    return {'message': 'User successfully deleted'}


@router.post('/{user_id}/follow')
async def follow(user_id: UUID, who: FollowRequestDTO, db: Session = Depends(get_db_session),
                 is_logged_in: bool = Depends(check_logged_in)):
    if not is_logged_in:
        raise HTTPException(status_code=401, detail='Not logged in', headers={'WWW-Authenticate': 'Bearer'})

    new_follow = Follows(follower_id=user_id, followee_id=who.followee_id)
    db.add(new_follow)
    db.commit()
    db.refresh(new_follow)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'message': 'User followed successfully'}
    )


@router.post('/{user_id}/unfollow')
async def unfollow(user_id: UUID, who: FollowRequestDTO, db: Session = Depends(get_db_session),
                   is_logged_in: bool = Depends(check_logged_in)):
    if not is_logged_in:
        raise HTTPException(status_code=401, detail='Not logged in', headers={'WWW-Authenticate': 'Bearer'})

    follows = db.query(Follows).filter(Follows.follower_id == user_id, Follows.followee_id == who.followee_id).first()
    if follows is None:
        raise HTTPException(status_code=404, detail='No follows relation found')

    db.delete(follows)
    db.commit()
    return {'message': 'User unfollowed successfully'}


@router.get('/{user_id}/timeline')
async def fetch_timeline(user_id: str, db: Session = Depends(get_db_session),
                         is_logged_in: bool = Depends(check_logged_in)):
    if not is_logged_in:
        raise HTTPException(status_code=401, detail='Not logged in', headers={'WWW-Authenticate': 'Bearer'})

    today = datetime.today()

    # Set the time to zero so we include Peeps that were created before the time we care about; so we consider the full day
    # e.g: today = 2024-12-20T14:00:00
    # we want last_5_days to be 2024-12-15T00:00:00, NOT 2024-12-15T14:00:00, otherwise Peeps created before 14:00:00 would be ignored
    last_5_days = (today - timedelta(days=5)).replace(hour=0, minute=0, second=0, microsecond=0)

    # TODO: find a way to improve this
    query = (
        select(Peep.content,
               func.to_char(Peep.created_at, 'YYYY-MM-DD"T"HH24:MI "UTC"OF').label('created_at'))
        .join(Follows, Follows.followee_id == Peep.user_id)  # Join peeps on follows
        .join(User, User.id == Follows.followee_id)  # Join users on follows
        .filter(Follows.follower_id == user_id, Peep.created_at >= last_5_days)
        .order_by(desc(Peep.created_at))
    )

    timeline = db.execute(query).mappings().all()

    return timeline


def extract_set_fields(body: BaseModel):
    fields = {}
    for key, value in body.model_dump().items():
        if value is not None:
            fields[key] = value

    return fields

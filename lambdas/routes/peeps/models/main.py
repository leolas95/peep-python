from pydantic import BaseModel


class CreatePeep(BaseModel):
    content: str
    user_id: str

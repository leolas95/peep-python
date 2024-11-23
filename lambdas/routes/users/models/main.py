from pydantic import BaseModel


class CreateUser(BaseModel):
    name: str
    email: str
    username: str


class UpdateUser(BaseModel):
    name: str | None = None
    email: str | None = None
    username: str | None = None

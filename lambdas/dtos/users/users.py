from pydantic import BaseModel


class CreateRequestDTO(BaseModel):
    name: str
    email: str
    username: str
    password: str


class CreateResponseDTO(BaseModel):
    message: str
    user: dict


class UpdateRequestDTO(BaseModel):
    name: str | None = None
    email: str | None = None
    username: str | None = None

from pydantic import BaseModel


class CreateRequestDTO(BaseModel):
    name: str
    email: str
    username: str


class CreateResponseDTO(BaseModel):
    message: str
    user: dict


class UpdateRequestDTO(BaseModel):
    name: str
    email: str
    username: str

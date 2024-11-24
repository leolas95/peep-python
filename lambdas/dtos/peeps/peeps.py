from pydantic import BaseModel


class CreateRequestDTO(BaseModel):
    content: str
    user_id: str


class CreateResponseDTO(BaseModel):
    message: str
    peep: dict

# TODO: cool but I don't like it that much
# class CreatePeepResponseDTO:
#     def __init__(self, message: str, data: Any):
#         self.message = message
#         self.data = data
#
#     def __call__(self):
#         return jsonable_encoder({'message': self.message, 'data': self.data})

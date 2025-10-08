# Внешние зависимости
from typing import Annotated
from pydantic import BaseModel, Field


# Схема Пользователя
class UserResponse(BaseModel):
    id: Annotated[int, Field(ge=1)]
    name: Annotated[str, Field(strict=True, max_length=50)]
    balance: Annotated[int, Field(ge=0)]

    class Config:
        from_attributes = True


# Схема добавления Пользователя
class AddUserRequest(BaseModel):
    name: Annotated[str, Field(strict=True, max_length=50)]
    balance: Annotated[int, Field(ge=0)] = 0
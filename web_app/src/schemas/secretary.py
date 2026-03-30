# Внешние зависимости
from typing import Annotated
from pydantic import BaseModel, Field


# Схема ответа судьи
class CreateSecretaryRequest(BaseModel):
    full_name: Annotated[str, Field(min_length=1)]
    username: Annotated[str, Field(min_length=1)]
    password: Annotated[str, Field(min_length=1)]
    judge_id: Annotated[int, Field(ge=1)]


# Схема запроса на подтверждение создания секретаря
class ConfirmCreateRequest(BaseModel):
    token: str


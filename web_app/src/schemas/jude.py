# Внешние зависимости
from typing import Annotated
from pydantic import BaseModel, Field


# Схема ответа судьи
class JudgeResponse(BaseModel):
    id: Annotated[int, Field(ge=1)]
    full_name: Annotated[str, Field()]
    department: Annotated[str, Field()]
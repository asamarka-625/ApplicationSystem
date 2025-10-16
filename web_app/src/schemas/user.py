# Внешние зависимости
from typing import Annotated, Optional, Literal
from pydantic import BaseModel, Field
# Внутренние модули
from web_app.src.models import ROLE_MAPPING


LIST_ROLE = list(role.capitalize() for role in ROLE_MAPPING.keys())


# Схема ответа информации о пользователе
class UserInfoResponse(BaseModel):
    full_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    role: Literal[*LIST_ROLE]
    email: Annotated[str, Field(strict=True, strip_whitespace=True)]
    phone: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]


# Схема ответа пользователя
class UserResponse(BaseModel):
    id: Optional[Annotated[int, Field(ge=1)]]
    name: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
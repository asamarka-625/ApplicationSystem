# Внешние зависимости
from typing import Annotated, Optional, Literal, List
from pydantic import BaseModel, Field
# Внутренние модули
from web_app.src.models import ROLE_MAPPING


class UserResponse(BaseModel):
    full_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    role: Literal[*list(ROLE_MAPPING.keys())]
    email: Annotated[str, Field(strict=True, strip_whitespace=True)]
    phone: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]


class UserRequest(BaseModel):
    id: Optional[Annotated[int, Field(ge=1)]]
    name: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
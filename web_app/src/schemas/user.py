# Внешние зависимости
from typing import Annotated, Optional, Literal
from pydantic import BaseModel, Field
# Внутренние модули
from web_app.src.models import ROLE_MAPPING


class UserResponse(BaseModel):
    full_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    role: Annotated[str, Field(strict=True, strip_whitespace=True)]
    email: Literal[*list(ROLE_MAPPING.keys())]
    phone: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]


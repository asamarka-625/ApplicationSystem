# Внешние зависимости
from typing import Annotated, List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field
# Внутренние модули
from web_app.src.models import TYPE_MAPPING


"""
# Схема Пользователя
class UserResponse(BaseModel):
    id: Annotated[int, Field(ge=1)]
    name: Annotated[str, Field(strict=True, max_length=50)]
    balance: Annotated[int, Field(ge=0)]

    class Config:
        from_attributes = True
"""

# Схема запроса на создание заявки
class CreateRequest(BaseModel):
    items: List[Annotated[int, Field(ge=1)]]
    description: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Annotated[int, Field(ge=0, lt=len(TYPE_MAPPING))]


# Схема информации о заявки
class RequestResponse(BaseModel):
    registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Dict[str, str]
    status: Dict[str, str]
    is_emergency: bool
    created_at: datetime
    deadline: Optional[datetime]


# Схема истории изменения заявки
class RequestHistoryResponse(BaseModel):
    created_at: datetime
    action: Dict[str, str]
    description: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
    user: Annotated[str, Field(strict=True, strip_whitespace=True)]


# Схема подробной информации о заявки
class RequestDetailResponse(BaseModel):
    registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Dict[str, str]
    status: Dict[str, str]
    items: List[str]
    description: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
    department_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    secretary_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    judge_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    management_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    executor_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    created_at: datetime
    deadline: Optional[datetime]
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    is_emergency: bool
    history: List[RequestHistoryResponse]
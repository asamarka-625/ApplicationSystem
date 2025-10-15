# Внешние зависимости
from typing import Annotated, List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
# Внутренние модули
from web_app.src.models import TYPE_MAPPING


# Схема запроса на создание заявки
class CreateRequest(BaseModel):
    items: List[Annotated[int, Field(ge=1)]]
    description: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Annotated[int, Field(ge=0, lt=len(TYPE_MAPPING))]


# Схема прав на действия с заявкой
class RightsRequest(BaseModel):
    view: bool
    edit: bool
    approve: bool
    reject: bool
    redirect: bool
    deadline: bool
    planning: bool
    ready: bool


# Схема информации о заявки
class RequestResponse(BaseModel):
    registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Dict[str, str]
    status: Dict[str, str]
    is_emergency: bool
    created_at: datetime
    deadline: Optional[datetime]
    rights: RightsRequest


# Схема данных заявки
class RequestDataResponse(BaseModel):
    registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Dict[str, Any]
    items: List[Dict[str, Any]]
    description: Annotated[str, Field(strict=True, strip_whitespace=True)]


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


# Схема запроса на назначение исполнителя
class RedirectRequest(BaseModel):
    executor: Annotated[int, Field(ge=1)]
    description: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
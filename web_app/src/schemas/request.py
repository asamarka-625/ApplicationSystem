# Внешние зависимости
from typing import Annotated, List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
# Внутренние модули
from web_app.src.models import TYPE_MAPPING
from web_app.src.schemas.user import UserResponse


# Схема предметов заявки
class ItemsRequest(BaseModel):
    id: Annotated[int, Field(ge=1)]
    quantity: Annotated[int, Field(ge=1)]


# Схема названий предметов заявки
class ItemsNameRequest(BaseModel):
    name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    quantity: Annotated[int, Field(ge=1)]


# Схема вложений заявки
class AttachmentsRequest(BaseModel):
    file_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    content_type: Annotated[str, Field(strict=True, strip_whitespace=True)]
    file_path: Annotated[str, Field(strict=True, strip_whitespace=True)]
    size: Annotated[int, Field(ge=0)]


# Схема запроса на создание заявки
class CreateRequest(BaseModel):
    items: Optional[List[ItemsRequest]] = None
    is_emergency: bool = False
    description: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Annotated[int, Field(ge=0, lt=len(TYPE_MAPPING))]
    attachments: Optional[List[AttachmentsRequest]] = None


# Схема ответа прав на действия с заявкой
class RightsResponse(BaseModel):
    view: bool
    edit: bool
    approve: bool
    reject: bool
    redirect: bool
    deadline: bool
    planning: bool
    ready: bool


# Схема ответа информации о заявки
class RequestResponse(BaseModel):
    registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Dict[str, str]
    status: Dict[str, str]
    is_emergency: bool
    created_at: datetime
    deadline: Optional[datetime]
    rights: RightsResponse


# Схема ответа данных о заявки
class RequestDataResponse(BaseModel):
    registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Dict[str, Any]
    items: List[Dict[str, Any]]
    description: Annotated[str, Field(strict=True, strip_whitespace=True)]


# Схема ответа истории изменения заявки
class RequestHistoryResponse(BaseModel):
    created_at: datetime
    action: Dict[str, str]
    description: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
    user: UserResponse


# Схема ответа подробной информации о заявки
class RequestDetailResponse(BaseModel):
    registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Dict[str, str]
    status: Dict[str, str]
    items: List[ItemsNameRequest]
    description: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
    description_executor: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
    department_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    secretary: UserResponse
    judge: UserResponse
    management: UserResponse
    executor: UserResponse
    created_at: datetime
    deadline: Optional[datetime]
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    is_emergency: bool
    attachments: Optional[List[AttachmentsRequest]] = None
    history: List[RequestHistoryResponse]


# Схема запроса на назначение исполнителя
class RedirectRequest(BaseModel):
    user_role_id: Annotated[int, Field(ge=1)]
    description: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]


# Схема запроса комментария
class CommentRequest(BaseModel):
    comment: Annotated[str, Field(strict=True, strip_whitespace=True)]


# Схема запроса даты и времени
class ScheduleRequest(BaseModel):
    scheduled_datetime: datetime
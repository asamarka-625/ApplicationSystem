# Внешние зависимости
from typing import Annotated, List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
# Внутренние модули
from web_app.src.models import TYPE_MAPPING, RequestStatus, RequestItemStatus
from web_app.src.schemas.user import UserResponse


# Enum для фактического статуса заявке
class ActualStatusRequest(Enum):
    CANCELLED = "cancelled"
    OVERDUE = "overdue"
    PLANNED = "planned"
    PARTIALLY_FULFILLED = "partially"
    COMPLETED = "completed"
    IN_PROGRESS = "progress"
    CONFIRMED = "confirmed"
    REGISTERED = "registered"
    ENDING_COMPLETED = "ending_completed"
    FINISHED = "finished"

ACTUAL_STATUS_MAPPING_FOR_REQUEST_STATUS = {
    RequestStatus.CANCELLED: ActualStatusRequest.CANCELLED,
    RequestStatus.PLANNED: ActualStatusRequest.PLANNED,
    RequestStatus.PARTIALLY_FULFILLED: ActualStatusRequest.PARTIALLY_FULFILLED,
    RequestStatus.COMPLETED: ActualStatusRequest.COMPLETED,
    RequestStatus.IN_PROGRESS: ActualStatusRequest.IN_PROGRESS,
    RequestStatus.CONFIRMED: ActualStatusRequest.CONFIRMED,
    RequestStatus.REGISTERED: ActualStatusRequest.REGISTERED,
    RequestStatus.ENDING_COMPLETED: ActualStatusRequest.ENDING_COMPLETED,
    RequestStatus.FINISHED: ActualStatusRequest.FINISHED
}

ACTUAL_STATUS_MAPPING_FOR_REQUEST_ITEM_STATUS = {
    RequestItemStatus.CANCELLED: ActualStatusRequest.CANCELLED,
    RequestItemStatus.PLANNED: ActualStatusRequest.PLANNED,
    RequestItemStatus.COMPLETED: ActualStatusRequest.COMPLETED,
    RequestItemStatus.IN_PROGRESS: ActualStatusRequest.IN_PROGRESS,
    RequestItemStatus.REGISTERED: ActualStatusRequest.REGISTERED
}


# Схема ID предмета заявки
class ItemsIdRequest(BaseModel):
    id: Annotated[int, Field(ge=1)]


# Схема предмета заявки
class ItemsRequest(ItemsIdRequest):
    quantity: Annotated[int, Field(ge=1)]


# Схема готовности заявки
class ItemsExecuteRequest(ItemsIdRequest):
    comment: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]


# Схема вложений заявки
class AttachmentsRequest(BaseModel):
    file_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    content_type: Annotated[str, Field(strict=True, strip_whitespace=True)]
    file_path: Annotated[str, Field(strict=True, strip_whitespace=True)]
    size: Annotated[int, Field(ge=0)]


# Схема запроса на создание заявки
class CreateRequest(BaseModel):
    items: List[ItemsRequest]
    is_emergency: bool = False
    description: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Annotated[int, Field(ge=0, lt=len(TYPE_MAPPING))]
    attachments: Optional[List[AttachmentsRequest]] = None


# Схема ответа прав на действия с заявкой
class RightsResponse(BaseModel):
    view: bool
    edit: bool
    approve: bool
    reject_before: bool
    reject_after: bool
    redirect_management_department: bool
    redirect_executor: bool
    redirect_org: bool
    deadline: bool
    planning: bool
    ready: bool
    confirm_management_department: bool
    confirm_management: bool


# Схема ответа информации о заявки
class RequestResponse(BaseModel):
    registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    human_registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Dict[str, str]
    status: Dict[str, str]
    is_emergency: bool
    created_at: datetime
    rights: RightsResponse
    actual_status: ActualStatusRequest
    

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


# Схема названия предмета заявки
class ItemsNameRequest(BaseModel):
    id: Annotated[int, Field(ge=1)]
    name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    quantity: Annotated[int, Field(ge=1)]


# Схема полной информации предмета заявки
class ItemsNameRequestFull(ItemsNameRequest):
    executor: Optional[UserResponse]
    executor_organization: Optional[UserResponse]
    description_executor: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
    description_organization: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
    description_completed: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
    deadline_executor: Optional[datetime]
    deadline_organization: Optional[datetime]
    status: RequestItemStatus
    access: bool


# Схема ответа подробной информации о заявки
class RequestDetailResponse(BaseModel):
    registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    human_registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Dict[str, str]
    status: Dict[str, str]
    items: List[ItemsNameRequestFull]
    description: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
    description_management_department: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]
    department_name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    secretary: UserResponse
    judge: UserResponse
    management: Optional[UserResponse]
    management_department: Optional[UserResponse]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    is_emergency: bool
    pdf_request: Annotated[str, Field(strict=True, strip_whitespace=True)]
    attachments: Optional[List[AttachmentsRequest]] = None
    history: List[RequestHistoryResponse]
    rights: RightsResponse


# Схема запроса на назначение пользователя
class RedirectRequest(BaseModel):
    user_role_id: Annotated[int, Field(ge=1)]
    description: Optional[Annotated[str, Field(strict=True, strip_whitespace=True)]]


# Схема запроса на назначение пользователя вместе с deadline
class RedirectRequestWithDeadline(RedirectRequest):
    item_id: Annotated[int, Field(ge=1)]
    deadline: datetime


# Схема запроса комментария
class CommentRequest(BaseModel):
    comment: Annotated[str, Field(strict=True, strip_whitespace=True)]


# Схема запроса даты и времени
class ScheduleRequest(BaseModel):
    scheduled_datetime: datetime


# Схема заявки для исполнителя
class RequestExecutorResponse(BaseModel):
    registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    human_registration_number: Annotated[str, Field(strict=True, strip_whitespace=True)]
    request_type: Dict[str, str]
    status: Dict[str, str]
    item: ItemsNameRequest
    is_emergency: bool
    created_at: datetime
    deadline: Optional[datetime]
    rights: RightsResponse
    actual_status: ActualStatusRequest


# Схема планирования предмета
class PlanningRequest(BaseModel):
    item_id: Annotated[int, Field(ge=1)]
    deadline: datetime
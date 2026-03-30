from web_app.src.schemas.request import (CreateRequest, RequestResponse, RequestDetailResponse,
                                         RequestHistoryResponse, RequestDataResponse, RightsResponse,
                                         RedirectRequest, CommentRequest, ScheduleRequest, ItemsRequest,
                                         AttachmentsRequest, ItemsNameRequest, RedirectRequestWithDeadline,
                                         RequestExecutorResponse, ItemsNameRequestFull, PlanningRequest,
                                         ItemsIdRequest, ActualStatusRequest, ACTUAL_STATUS_MAPPING_FOR_REQUEST_STATUS,
                                         ACTUAL_STATUS_MAPPING_FOR_REQUEST_ITEM_STATUS, ItemsExecuteRequest)
from web_app.src.schemas.user import UserInfoResponse, UserResponse, PasswordResetRequest, CheckUsernameRequest
from web_app.src.schemas.documents import DocumentResponse, DocumentEmblem, DocumentData, DocumentItem
from web_app.src.schemas.jude import JudgeResponse
from web_app.src.schemas.secretary import CreateSecretaryRequest, ConfirmCreateRequest
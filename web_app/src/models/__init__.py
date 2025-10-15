from web_app.src.models.base import Base
from web_app.src.models.user import (UserRole, ROLE_MAPPING, User, Secretary,
                                     Judge, Management, Executor)
from web_app.src.models.product import Category, Item
from web_app.src.models.request import (Request, RequestType, RequestStatus, STATUS_MAPPING,
                                        TYPE_MAPPING, STATUS_ID_MAPPING, TYPE_ID_MAPPING,
                                        RequestHistory, RequestDocument)
from web_app.src.models.table import request_item
from web_app.src.models.organization import Department
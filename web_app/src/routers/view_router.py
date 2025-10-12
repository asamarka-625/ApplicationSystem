# Внешние зависимости
import random
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import Field
# Внутренние модули
# from web_app.src.crud import sql_get_all_departament, sql_search_items
from web_app.src.models import TYPE_MAPPING, STATUS_MAPPING


router = APIRouter(
    prefix="/api/v1/request/view",
    tags=["API"],
)


@router.get(
    path="/list/",
    response_class=JSONResponse,
    summary="",
)
async def get_reuests_by_user(
    status: str = "all",
    request_type: str = "all"
):  
    requests = [
        {
            "registration_number": i,
            "request_type": random.choice(list(TYPE_MAPPING.keys())).capitalize(),
            "items": random.choices(ITEMS, k=3),
            "status": random.choice(list(STATUS_MAPPING.keys())).capitalize(),
            "created_at": datetime.now(),
            "deadline": datetime.now() + timedelta(days=random.randint(1, 10))
        }
    for i in range(5)]
    return {
        "count_requests": len(requests),
        "requests": requests
    }


@router.get(
    path="/info",
    response_class=JSONResponse,
    summary="",
)
async def get_info_for_view():
    return {
        "request_type": (r_type.capitalize() for r_type in TYPE_MAPPING.keys()),
        "status": (status.capitalize() for status in STATUS_MAPPING.keys())
    }
# Внешние зависимости
from typing import List
import uuid
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import (Request, TYPE_ID_MAPPING, request_item, RequestHistory,
                                RequestStatus, TYPE_MAPPING, STATUS_MAPPING, User, RequestType,
                                Secretary, Judge, Management, Executor)
from web_app.src.core import connection
from web_app.src.schemas import (CreateRequest, RequestResponse, RequestDetailResponse,
                                 RequestHistoryResponse)


# Создаем новую заявку
@connection
async def sql_create_request(
        data: CreateRequest,
        secretary_id: int,
        judge_id: int,
        department_id: int,
        session: AsyncSession
) -> int:
    try:
        request_type = next(
            TYPE_MAPPING[r_type["name"].lower()]
            for r_type in TYPE_ID_MAPPING if r_type["id"] == data.request_type
        )

        if request_type is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request type")

        new_request = Request(
            registration_number=str(uuid.uuid4()),
            description=data.description,
            request_type=request_type,
            is_emergency=request_type == RequestType.EMERGENCY,
            secretary_id=secretary_id,
            judge_id=judge_id,
            department_id=department_id
        )
        session.add(new_request)
        await session.flush()

        for item_id in data.items:
            # Связываем предметы с заявкой
            await session.execute(request_item.insert().values(
                request_id=new_request.id,
                item_id=item_id
            ))

        new_history = RequestHistory(
            action=RequestStatus.REGISTERED,
            request_id=new_request.id,
            user_id=secretary_id
        )
        session.add(new_history)

        await session.commit()
        return new_request.id

    except SQLAlchemyError as e:
        config.logger.error(f"Database error while creating request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error while creating request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выводим список заявок
@connection
async def sql_get_requests_by_user(
        session: AsyncSession,
        user: User,
        status_filter: str = "all",
        type_filter: str = "all",
) -> List[RequestResponse]:
    try:
        query = (
            sa.select(Request)
        )

        if user.is_secretary:
            query.where(Request.secretary_id == user.id)

        elif user.is_judge:
            query.where(Request.judge_id == user.id)

        elif user.is_management:
            pass

        elif user.is_executor:
            query.where(Request.executor_id == user.id)

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

        if status_filter and status_filter != "all" and STATUS_MAPPING.get(status_filter):
            query.where(Request.status == STATUS_MAPPING[status_filter])

        if type_filter and type_filter != "all" and TYPE_MAPPING.get(type_filter):
            query.where(Request.request_type == TYPE_MAPPING[type_filter])

        requests_result = await session.execute(query)
        requests = requests_result.scalars()

        return [
            RequestResponse(
                registration_number=request.registration_number,
                request_type={
                    "name": request.request_type.name,
                    "value": request.request_type.value
                },
                status={
                    "name": request.status.name,
                    "value": request.status.value
                },
                is_emergency=request.is_emergency,
                created_at=request.created_at,
                deadline=request.deadline
            )
            for request in requests
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view requests: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error view requests: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выводим подробную информацию о заявке
@connection
async def sql_get_request_details(
        registration_number: str,
        session: AsyncSession
) -> RequestDetailResponse:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(Request.registration_number == registration_number)
            .options(
                so.selectinload(Request.items),
                so.joinedload(Request.secretary).joinedload(Secretary.user),
                so.joinedload(Request.judge).joinedload(Judge.user),
                so.joinedload(Request.management).joinedload(Management.user),
                so.joinedload(Request.executor).joinedload(Executor.user),
                so.joinedload(Request.department),
                so.selectinload(Request.history).joinedload(RequestHistory.user)
            )
        )

        request = request_result.scalar_one()

        return RequestDetailResponse(
            registration_number=request.registration_number,
            request_type={
                "name": request.request_type.name,
                "value": request.request_type.value
            },
            status={
                "name": request.status.name,
                "value": request.status.value
            },
            items=[item.name for item in request.items],
            description=request.description,
            department_name=f"[{request.department.code}] {request.department.name} ({request.department.address})",
            secretary_name=request.secretary.user.full_name,
            judge_name=request.judge.user.full_name,
            management_name=request.management.user.full_name if request.management else 'Не задан',
            executor_name=request.executor.user.full_name if request.executor else 'Не задан',
            created_at=request.created_at,
            deadline=request.deadline,
            updated_at=request.update_at,
            completed_at=request.completed_at,
            is_emergency=request.is_emergency,
            history=[
                RequestHistoryResponse(
                    created_at=h.created_at,
                    action={
                        "name": h.action.name,
                        "value": h.action.value
                    },
                    description=h.description,
                    user=h.user.full_name
                )
                for h in request.history
            ]
        )

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view detail request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error view detail request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
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
                                RequestAction, RequestStatus, TYPE_MAPPING, STATUS_MAPPING, User, RequestType,
                                Secretary, Judge, Management, Executor, Item, UserRole)
from web_app.src.core import connection
from web_app.src.schemas import (CreateRequest, RequestResponse, RequestDetailResponse,
                                 RequestHistoryResponse, RequestDataResponse, RightsRequest,
                                 RedirectRequest)


# Создаем новую заявку
@connection
async def sql_create_request(
        data: CreateRequest,
        user_id: int,
        secretary_id: int,
        judge_id: int,
        department_id: int,
        session: AsyncSession
) -> str:
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
            action=RequestAction.REGISTERED,
            request_id=new_request.id,
            user_id=user_id,
            description="Заявка зарегистрирована"
        )
        session.add(new_history)

        await session.commit()
        return new_request.registration_number

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
            query = query.where(Request.secretary_id == user.secretary_profile.id)

        elif user.is_judge:
            query = query.where(Request.judge_id == user.judge_profile.id)

        elif user.is_management:
            query = query.where(
                Request.status.notin_((RequestStatus.REGISTERED, RequestStatus.CANCELLED))
            )

        elif user.is_executor:
            query = query.where(Request.executor_id == user.executor_profile.id)

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

        if status_filter and status_filter != "all" and STATUS_MAPPING.get(status_filter):
            query = query.where(Request.status == STATUS_MAPPING[status_filter])

        if type_filter and type_filter != "all" and TYPE_MAPPING.get(type_filter):
            query = query.where(Request.request_type == TYPE_MAPPING[type_filter])

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
                deadline=request.deadline,
                rights=RightsRequest(
                    view=True,
                    edit=request.status == RequestStatus.REGISTERED,
                    approve=request.status == RequestStatus.REGISTERED,
                    reject=request.status == RequestStatus.REGISTERED or request.status == RequestStatus.CONFIRMED,
                    redirect=request.status == RequestStatus.CONFIRMED,
                    deadline=request.status == RequestStatus.CONFIRMED,
                    planning=request.status == RequestStatus.CONFIRMED or request.status == RequestStatus.IN_PROGRESS,
                    ready=request.status == RequestStatus.IN_PROGRESS
                )
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
            items=[f"{item.name} {item.description}" for item in request.items],
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


@connection
async def sql_get_request_data(
        registration_number: str,
        session: AsyncSession
) -> RequestDataResponse:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(Request.registration_number == registration_number)
            .options(
                so.selectinload(Request.items)
            )
        )

        request = request_result.scalar_one()

        return RequestDataResponse(
            registration_number=request.registration_number,
            request_type=next(
                (type_ for type_ in TYPE_ID_MAPPING if type_["name"].lower() == request.request_type.value),
            ),
            items=[
                {"id": item.id, "name": item.name, "description": item.description}
                for item in request.items
            ],
            description=request.description
        )

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view data request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error view data request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


@connection
async def sql_edit_request(
        registration_number: str,
        user_id: int,
        role: UserRole,
        role_id: int,
        data: CreateRequest,
        session: AsyncSession
) -> None:
    try:
        query = sa.select(Request).where(
                Request.registration_number == registration_number
        )

        if role == UserRole.SECRETARY:
            query = query.where(Request.secretary_id == role_id)

        elif role == UserRole.JUDGE:
            query = query.where(Request.judge_id == role_id)

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

        request_result = await session.execute(query)

        request = request_result.scalar_one()

        if request.status != RequestStatus.REGISTERED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

        list_update = []

        request_type = next(
            TYPE_MAPPING[r_type["name"].lower()]
            for r_type in TYPE_ID_MAPPING if r_type["id"] == data.request_type
        )

        if request_type is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request type")

        if request_type != request.request_type:
            list_update.append("Изменен тип заявки: "
                               f"{request.request_type.value.capitalize()} -> {request_type.value.capitalize()}")
            request.request_type = request_type

        if data.description.strip() != request.description.strip():
            list_update.append(f"Изменено описание: {request.description} -> {data.description}")
            request.description = data.description

        # Удаляем записи и возвращаем удаленные данные
        delete_result = await session.execute(
            sa.delete(request_item).where(
                sa.and_(
                    request_item.c.request_id == request.id,
                    request_item.c.item_id.notin_(data.items)
                )
            ).returning(request_item.c.item_id)
        )

        # Получаем удаленные item_id
        deleted_item_ids = [row[0] for row in delete_result]

        # Находим все записи для данной заявки
        existing_items = await session.execute(
            sa.select(request_item.c.item_id).where(
                sa.and_(
                    request_item.c.request_id == request.id,
                    request_item.c.item_id.in_(data.items)
                )
            )
        )
        existing_item_ids = {row.item_id for row in existing_items}

        new_items = [
            {"request_id": request.id, "item_id": item_id}
            for item_id in data.items
            if item_id not in existing_item_ids
        ]

        inserted_item_ids = set()
        # Добавляем новые записи
        if new_items:
            insert_result = await session.execute(
                request_item.insert().returning(request_item.c.item_id),
                new_items
            )
            inserted_item_ids = {row[0] for row in insert_result}

        all_changed_ids = inserted_item_ids.union(deleted_item_ids)

        if all_changed_ids:
            update_items_result = await session.execute(
                sa.select(Item.id, Item.name, Item.description)
                .where(
                    Item.id.in_(all_changed_ids)
                )
            )

            update_items = update_items_result.all()

            del_info = []
            add_info = []
            for item in update_items:
                if item[0] in deleted_item_ids:
                    del_info.append(f"Удален предмет: {item[1]} {item[2]}")

                if item[0] in inserted_item_ids:
                    add_info.append(f"Добавлен предмет: {item[1]} {item[2]}")

            if del_info:
                list_update.append("\n".join(del_info))

            if add_info:
                list_update.append("\n".join(add_info))

        new_history = RequestHistory(
            action=RequestAction.UPDATE,
            request_id=request.id,
            user_id=user_id,
            description="\n".join(list_update)
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error edit data request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error edit data request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


@connection
async def sql_approve_request(
        registration_number: str,
        user_id: int,
        judge_id: int,
        session: AsyncSession
) -> None:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(
                Request.registration_number == registration_number,
                Request.judge_id == judge_id,
                Request.status == RequestStatus.REGISTERED
            )
        )

        request = request_result.scalar_one()

        request.status = RequestStatus.CONFIRMED

        new_history = RequestHistory(
            action=RequestAction.CONFIRMED,
            request_id=request.id,
            user_id=user_id,
            description="Заявка утверждена"
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error approve request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error approve request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


@connection
async def sql_reject_request(
        registration_number: str,
        user_id: int,
        judge_id: int,
        session: AsyncSession
) -> None:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(
                Request.registration_number == registration_number,
                Request.judge_id == judge_id
            )
        )

        request = request_result.scalar_one()

        if request.status != RequestStatus.REGISTERED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

        request.status = RequestStatus.CANCELLED

        new_history = RequestHistory(
            action=RequestAction.CANCELLED,
            request_id=request.id,
            user_id=user_id,
            description="Заявка отклонена"
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reject request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error reject request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


@connection
async def sql_redirect_request(
        registration_number: str,
        user_id: int,
        management_id: int,
        data: RedirectRequest,
        session: AsyncSession
) -> None:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(
                Request.registration_number == registration_number,
            )
        )

        request = request_result.scalar_one()

        if request.status in (RequestStatus.REGISTERED, RequestStatus.CANCELLED):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough rights")

        request.status = RequestStatus.IN_PROGRESS
        request.management_id = management_id
        request.executor_id = data.executor
        request.description_executor = data.description

        new_history = RequestHistory(
            action=RequestAction.IN_PROGRESS,
            request_id=request.id,
            user_id=user_id,
            description="Заявка отправлена на выполнение"
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error redirect request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error redirect request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
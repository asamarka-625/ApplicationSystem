# Внешние зависимости
from typing import List, Optional
from datetime import datetime
import uuid
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import config
from web_app.src.models import (Request, TYPE_ID_MAPPING, request_item, RequestItem, RequestHistory,
                                RequestType, RequestDocument, RequestAction, RequestStatus, TYPE_MAPPING,
                                STATUS_MAPPING, User, Secretary, Judge, Management, Executor, Item, UserRole,
                                ManagementDepartment, ExecutorOrganization, RequestItemStatus)
from web_app.src.core import connection
from web_app.src.schemas import (CreateRequest, RequestResponse, RequestDetailResponse,
                                 RequestHistoryResponse, RequestDataResponse, RightsResponse,
                                 RedirectRequest, UserResponse, AttachmentsRequest, ItemsNameRequest,
                                 ItemsNameRequestFull, RedirectRequestWithDeadline, RequestExecutorResponse,
                                 PlanningRequest, ActualStatusRequest)


# Вспомогательная функция для получения прав для взаимодействия с предметом
def get_right_for_item_by_role(
    executor_id: Optional[int],
    organization_id: Optional[int],
    user: User
) -> bool:
    if user.role in (UserRole.MANAGEMENT, UserRole.MANAGEMENT_DEPARTMENT):
        return True

    if user.role == UserRole.EXECUTOR:
        return bool(executor_id) and executor_id == user.executor_profile.id

    if user.role == UserRole.EXECUTOR_ORGANIZATION:
        return bool(organization_id) and organization_id == user.executor_organization_profile.id

    return False


# Вспомогательная функция для получения просрочки заявке
def get_overdue_request(
    role: UserRole,
    item_associations: List[RequestItem]
) -> bool:
    
    if role not in (UserRole.MANAGEMENT, UserRole.MANAGEMENT_DEPARTMENT, 
                    UserRole.EXECUTOR, UserRole.EXECUTOR_ORGANIZATION):
        return False
        
    now = datetime.now()
    for association in item_associations:
        if (association.deadline_executor < now or association.deadline_organization < now 
            or association.deadline_planning < now):
            return True

    return False
    
    
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

        if request_type == RequestType.MATERIAL:
            if not (data.items and data.description == '' and not data.is_emergency):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

        elif request_type == RequestType.TECHNICAL:
            if not (data.items is None and len(data.description) > 0):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

        new_request = Request(
            registration_number=str(uuid.uuid4()),
            description=data.description,
            request_type=request_type,
            is_emergency=data.is_emergency,
            secretary_id=secretary_id,
            judge_id=judge_id,
            department_id=department_id
        )
        session.add(new_request)
        await session.flush()

        if data.items:
            for item in data.items:
                # Связываем предметы с заявкой
                await session.execute(request_item.insert().values(
                    request_id=new_request.id,
                    item_id=item.id,
                    count=item.quantity
                ))

        if data.attachments:
            for attachment in data.attachments:
                new_document = RequestDocument(
                    document_type=attachment.content_type,
                    file_path=attachment.file_path,
                    file_name=attachment.file_name,
                    size=attachment.size,
                    request_id=new_request.id
                )
                session.add(new_document)

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

    except HTTPException:
        raise

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
                Request.status != RequestStatus.REGISTERED
            ).options(
                so.selectinload(Request.item_associations)
            )

        elif user.is_management_department:
            query = query.where(
                Request.management_department_id == user.management_department_profile.id
            ).options(
                so.selectinload(Request.item_associations)
            )

        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

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
                rights=RightsResponse(
                    view=True,
                    edit=request.status == RequestStatus.REGISTERED,
                    approve=request.status == RequestStatus.REGISTERED,
                    reject_before=request.status == RequestStatus.REGISTERED,
                    reject_after=request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED),
                    redirect_management_department=request.status not in (RequestStatus.COMPLETED,
                                                                          RequestStatus.CANCELLED),
                    redirect_executor=request.status not in (RequestStatus.COMPLETED,
                                                             RequestStatus.CANCELLED),
                    redirect_org=request.status not in (RequestStatus.COMPLETED,
                                                        RequestStatus.CANCELLED),
                    deadline=request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED),
                    planning=request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED),
                    ready=request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED),
                    confirm_management_department=request.status not in (RequestStatus.COMPLETED,
                                                                         RequestStatus.CANCELLED),
                    confirm_management=request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED)
                ),
                actual_status=(ActualStatusRequest.OVERDUE if get_overdue_request(user.role, request.item_associations)
                               else ACTUAL_STATUS_MAPPING[request.status])
            )
            for request in requests
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view requests: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error view requests: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выводим список заявок для исполнителя (организации)
@connection
async def sql_get_requests_for_executor(
        session: AsyncSession,
        user: User,
        status_filter: str = "all",
        type_filter: str = "all"
) -> List[RequestExecutorResponse]:
    try:
        query = (
            sa.select(Request)
            .options(
                so.selectinload(Request.item_associations).joinedload(RequestItem.item)
            )
        )

        conditions = []

        if user.is_executor:
            conditions.append(
                Request.id.in_(
                    sa.select(RequestItem.request_id).where(
                        RequestItem.executor_id == user.executor_profile.id,
                        RequestItem.status != RequestItemStatus.PLANNED
                    )
                )
            )
            validate_association = lambda a, u: a.executor_id == u.executor_profile.id

        elif user.is_executor_organization:
            conditions.append(
                Request.id.in_(
                    sa.select(RequestItem.request_id).where(
                        RequestItem.executor_organization_id == user.executor_organization_profile.id,
                        RequestItem.status != RequestItemStatus.PLANNED
                    )
                )
            )
            validate_association = lambda a, u: a.executor_organization_id == u.executor_organization_profile.id

        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        if status_filter and status_filter != "all" and STATUS_MAPPING.get(status_filter):
            conditions.append(Request.status == STATUS_MAPPING[status_filter])

        if type_filter and type_filter != "all" and TYPE_MAPPING.get(type_filter):
            conditions.append(Request.request_type == TYPE_MAPPING[type_filter])

        query = query.where(sa.and_(*conditions))

        requests_result = await session.execute(query)
        requests = requests_result.scalars().all()

        return [
            RequestExecutorResponse(
                registration_number=request.registration_number,
                item=ItemsNameRequest(
                    id=association.item.id,
                    name=association.item.name,
                    quantity=association.count,
                ),
                request_type={
                    "name": request.request_type.name,
                    "value": request.request_type.value
                },
                status={
                    "name": association.status.name,
                    "value": association.status.value
                },
                is_emergency=request.is_emergency,
                created_at=request.created_at,
                deadline=association.deadline_executor if user.is_executor else association.deadline_organization,
                rights=RightsResponse(
                    view=True,
                    edit=False,
                    approve=False,
                    reject_before=False,
                    reject_after=False,
                    redirect_management_department=False,
                    redirect_executor=False,
                    redirect_org=association.status not in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED),
                    deadline=association.status not in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED),
                    planning=association.status not in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED,
                                                        RequestItemStatus.PLANNED),
                    ready=association.status not in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED),
                    confirm_management_department=False,
                    confirm_management=False
                ),
                actual_status=(ActualStatusRequest.OVERDUE if get_overdue_request(user.role, request.item_associations)
                               else ACTUAL_STATUS_MAPPING[request.status])
            )
            for request in requests
            for association in request.item_associations
            if validate_association(association, user) and association.status != RequestItemStatus.PLANNED
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view requests for executor: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error view requests for executor: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выводим список запланированных заявок для пользователя
@connection
async def sql_get_planning_requests(
        session: AsyncSession,
        user: User,
        status_filter: str = "all",
        type_filter: str = "all"
) -> List[RequestExecutorResponse]:
    try:
        query = (
            sa.select(Request)
            .options(
                so.selectinload(Request.item_associations).joinedload(RequestItem.item)
            )
        )

        conditions = []

        if user.is_management:
            conditions.append(Request.management_id == user.management_profile.id)
            conditions.append(
                Request.id.in_(
                    sa.select(RequestItem.request_id).where(
                        RequestItem.status == RequestItemStatus.PLANNED
                    )
                )
            )
            validate_association = lambda a, u: True

        elif user.is_management_department:
            conditions.append(Request.management_department_id == user.management_department_profile.id)
            conditions.append(
                Request.id.in_(
                    sa.select(RequestItem.request_id).where(
                        RequestItem.status == RequestItemStatus.PLANNED
                    )
                )
            )
            validate_association = lambda a, u: True

        elif user.is_executor:
            conditions.append(
                Request.id.in_(
                    sa.select(RequestItem.request_id).where(
                        RequestItem.executor_id == user.executor_profile.id,
                        RequestItem.status == RequestItemStatus.PLANNED
                    )
                )
            )
            validate_association = lambda a, u: a.executor_id == u.executor_profile.id

        elif user.is_executor_organization:
            conditions.append(
                Request.id.in_(
                    sa.select(RequestItem.request_id).where(
                        RequestItem.executor_organization_id == user.executor_organization_profile.id,
                        RequestItem.status == RequestItemStatus.PLANNED
                    )
                )
            )
            validate_association = lambda a, u: a.executor_organization_id == u.executor_organization_profile.id

        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        if status_filter and status_filter != "all" and STATUS_MAPPING.get(status_filter):
            conditions.append(Request.status == STATUS_MAPPING[status_filter])

        if type_filter and type_filter != "all" and TYPE_MAPPING.get(type_filter):
            conditions.append(Request.request_type == TYPE_MAPPING[type_filter])

        query = query.where(sa.and_(*conditions))

        requests_result = await session.execute(query)
        requests = requests_result.scalars().all()

        return [
            RequestExecutorResponse(
                registration_number=request.registration_number,
                item=ItemsNameRequest(
                    id=association.item.id,
                    name=association.item.name,
                    quantity=association.count,
                ),
                request_type={
                    "name": request.request_type.name,
                    "value": request.request_type.value
                },
                status={
                    "name": association.status.name,
                    "value": association.status.value
                },
                is_emergency=request.is_emergency,
                created_at=request.created_at,
                deadline=association.deadline_planning,
                rights=RightsResponse(
                    view=True,
                    edit=False,
                    approve=False,
                    reject_before=False,
                    reject_after=False,
                    redirect_management_department=False,
                    redirect_executor=False,
                    redirect_org=association.status not in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED),
                    deadline=association.status not in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED),
                    planning=association.status not in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED,
                                                        RequestItemStatus.PLANNED),
                    ready=association.status not in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED),
                    confirm_management_department=False,
                    confirm_management=False
                )
            )
            for request in requests
            for association in request.item_associations
            if validate_association(association, user) and association.status == RequestItemStatus.PLANNED
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view requests for executor: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error view requests for executor: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выводим подробную информацию о заявке
@connection
async def sql_get_request_details(
        registration_number: str,
        user: User,
        session: AsyncSession
) -> RequestDetailResponse:
    try:
        role = user.role

        request_result = await session.execute(
            sa.select(Request)
            .where(Request.registration_number == registration_number)
            .options(
                so.selectinload(Request.item_associations)
                .joinedload(RequestItem.item),
                so.selectinload(Request.item_associations)
                .joinedload(RequestItem.executor).joinedload(Executor.user),
                so.selectinload(Request.item_associations)
                .joinedload(RequestItem.executor_organization).joinedload(ExecutorOrganization.user),
                so.joinedload(Request.secretary).joinedload(Secretary.user),
                so.joinedload(Request.judge).joinedload(Judge.user),
                so.joinedload(Request.management).joinedload(Management.user),
                so.joinedload(Request.management_department).joinedload(ManagementDepartment.user),
                so.joinedload(Request.department),
                so.selectinload(Request.related_documents),
                so.selectinload(Request.history).joinedload(RequestHistory.user)
            )
        )

        request = request_result.scalar_one()
        items = []
        for association in request.item_associations:
            right_item = get_right_for_item_by_role(
                executor_id=association.executor_id,
                organization_id=association.executor_organization_id,
                user=user
            )
            items.append(ItemsNameRequestFull(
                id=association.item_id,
                name=f"{association.item.name} {association.item.description}".strip(),
                quantity=association.count,
                executor=UserResponse(
                    id=association.executor.user.id,
                    name=association.executor.user.full_name
                ) if association.executor else None,
                executor_organization=UserResponse(
                    id=association.executor_organization.user.id,
                    name=association.executor_organization.user.full_name
                ) if association.executor_organization else None,
                description_executor=(association.description_executor if right_item and
                                      not user.is_executor_organization else None),
                description_organization=association.description_organization if right_item else None,
                deadline_executor=association.deadline_executor,
                deadline_organization=association.deadline_organization,
                access=right_item and not user.is_executor_organization
            ))

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
            items=items,
            description=request.description,
            description_management_department=request.description_management_department if \
                role in (UserRole.MANAGEMENT, UserRole.MANAGEMENT_DEPARTMENT) else None,
            department_name=f"[{request.department.code}] {request.department.name} ({request.department.address})",
            secretary=UserResponse(
                id=request.secretary.user.id,
                name=request.secretary.user.full_name
            ),
            judge=UserResponse(
                id=request.judge.user.id,
                name=request.judge.user.full_name
            ),
            management=UserResponse(
                id=request.management.user.id,
                name=request.management.user.full_name
            ) if request.management else None,
            management_department=UserResponse(
                id=request.management_department.user.id,
                name=request.management_department.user.full_name
            ) if request.management_department else None,
            created_at=request.created_at,
            updated_at=request.update_at,
            completed_at=request.completed_at,
            is_emergency=request.is_emergency,
            attachments=[
                AttachmentsRequest(
                    file_name=attachment.file_name,
                    content_type=attachment.document_type,
                    file_path=attachment.file_path,
                    size=attachment.size
                )
                for attachment in request.related_documents
            ],
            history=[
                RequestHistoryResponse(
                    created_at=h.created_at,
                    action={
                        "name": h.action.name,
                        "value": h.action.value
                    },
                    description=h.description,
                    user=UserResponse(
                        id=h.user.id,
                        name=h.user.full_name if h.user else None
                    )
                )
                for h in request.history
            ],
            rights=RightsResponse(
                view=True,
                edit=request.status == RequestStatus.REGISTERED,
                approve=request.status == RequestStatus.REGISTERED,
                reject_before=request.status == RequestStatus.REGISTERED,
                reject_after=request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED),
                redirect_management_department=request.status not in (RequestStatus.COMPLETED,
                                                                      RequestStatus.CANCELLED),
                redirect_executor=request.status not in (RequestStatus.COMPLETED,
                                                         RequestStatus.CANCELLED),
                redirect_org=request.status not in (RequestStatus.COMPLETED,
                                                    RequestStatus.CANCELLED),
                deadline=request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED),
                planning=request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED),
                ready=request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED),
                confirm_management_department=request.status not in (RequestStatus.COMPLETED,
                                                                     RequestStatus.CANCELLED),
                confirm_management=request.status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED)
            )
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


# Данные заявки
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
                so.selectinload(Request.item_associations).joinedload(RequestItem.item),
            )
        )

        request = request_result.scalar_one()

        return RequestDataResponse(
            registration_number=request.registration_number,
            request_type=next(
                (type_ for type_ in TYPE_ID_MAPPING if type_["name"].lower() == request.request_type.value),
            ),
            items=[
                {
                    "id": association.item.id,
                    "name": association.item.name,
                    "description": association.item.description
                }
                for association in request.item_associations
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


# Редактирование заявки
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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        request_result = await session.execute(query)

        request = request_result.scalar_one()

        if request.status != RequestStatus.REGISTERED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

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

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error edit data request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Подтвреждение заявки
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


# Отклонение заявки
@connection
async def sql_reject_request(
        registration_number: str,
        user_id: int,
        role: UserRole,
        role_id: int,
        session: AsyncSession,
        comment: str = ''
) -> None:
    try:
        query = sa.select(Request).where(Request.registration_number == registration_number)

        if role == UserRole.JUDGE:
            query = query.where(Request.judge_id == role_id)

        elif role == UserRole.MANAGEMENT:
            query = query.where(Request.management_id == role_id)

        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        request_result = await session.execute(query)

        request = request_result.scalar_one()

        if request.status in (RequestStatus.COMPLETED, RequestStatus.CANCELLED):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        request.status = RequestStatus.CANCELLED

        comment = f"Причина: {comment}" if comment else ''
        new_history = RequestHistory(
            action=RequestAction.CANCELLED,
            request_id=request.id,
            user_id=user_id,
            description=f"Заявка отклонена\n{comment}"
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error reject request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error reject request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Назначение исполнителя заявки
@connection
async def sql_redirect_executor_request(
        registration_number: str,
        user_id: int,
        data: RedirectRequestWithDeadline,
        user: User,
        session: AsyncSession
) -> None:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(
                Request.registration_number == registration_number
            )
            .options(
                so.selectinload(Request.item_associations)
            )
        )

        request = request_result.scalar_one()

        executor_result = await session.execute(
            sa.select(Executor)
            .where(Executor.id == data.user_role_id)
            .options(so.joinedload(Executor.user))
        )
        executor = executor_result.scalar_one_or_none()

        if executor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Executor not found")

        if (user.role == UserRole.MANAGEMENT_DEPARTMENT and
            executor.management_department_id != user.management_department_profile.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        request_item = next((obj for obj in request.item_associations if obj.item_id == data.item_id), None)

        if request_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

        if request_item.status in (RequestStatus.REGISTERED, RequestStatus.CANCELLED) or \
            request_item.status in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        request_item.executor_id = data.user_role_id
        request_item.description_executor = data.description
        request_item.deadline_executor = data.deadline

        new_history = RequestHistory(
            action=RequestAction.APPOINTED,
            request_id=request.id,
            user_id=user_id,
            description=(f"Заявка отправлена на выполнение\nИсполнитель: {executor.user.full_name}"
                         f"Срок: {data.deadline.strftime("%d.%m.%Y")}")
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error redirect executor request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error redirect executor request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Назначение исполнителя заявки
@connection
async def sql_redirect_organization_request(
        registration_number: str,
        user_id: int,
        data: RedirectRequestWithDeadline,
        user: User,
        session: AsyncSession
) -> None:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(
                Request.registration_number == registration_number
            )
            .options(
                so.selectinload(Request.item_associations)
            )
        )

        request = request_result.scalar_one()

        org_user_result = await session.execute(
            sa.select(User)
            .join(ExecutorOrganization, ExecutorOrganization.user_id == User.id)
            .where(ExecutorOrganization.id == data.user_role_id)
        )
        org_user = org_user_result.scalar_one_or_none()

        if org_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization executor not found")

        request_item = next((obj for obj in request.item_associations if obj.item_id == data.item_id), None)

        if request_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

        if request_item.status in (RequestItemStatus.COMPLETED, RequestStatus.REGISTERED, RequestStatus.CANCELLED) or \
                (user.role == UserRole.EXECUTOR and user.executor_profile.id != request_item.executor_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        request_item.executor_organization_id = data.user_role_id
        request_item.description_organization = data.description
        request_item.deadline_organization = data.deadline

        new_history = RequestHistory(
            action=RequestAction.APPOINTED,
            request_id=request.id,
            user_id=user_id,
            description=(f"Заявка отправлена на выполнение\nИсполнитель: {org_user.full_name}\n"
                         f"Срок: {data.deadline.strftime("%d.%m.%Y")}")
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error redirect executor request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error redirect executor request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Назначение сотрудника управления отдела
@connection
async def sql_redirect_management_request(
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
                Request.registration_number == registration_number
            )
        )

        request = request_result.scalar_one()

        management_department_user_result = await session.execute(
            sa.select(User)
            .join(ManagementDepartment, ManagementDepartment.user_id == User.id)
            .where(ManagementDepartment.id == data.user_role_id)
        )
        management_department_user = management_department_user_result.scalar_one_or_none()

        if management_department_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Management not found")

        if request.status in (RequestStatus.REGISTERED, RequestStatus.CANCELLED):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        request.status = RequestStatus.IN_PROGRESS
        request.management_id = management_id
        request.management_department_id = data.user_role_id
        request.description_management_department = data.description

        new_history = RequestHistory(
            action=RequestAction.IN_PROGRESS,
            request_id=request.id,
            user_id=user_id,
            description=("Заявке назначен сотрудник управления отдела\n"
                         f"Исполнитель: {management_department_user.full_name}")
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error redirect management request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error redirect management request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выполнение заявки
@connection
async def sql_execute_request(
        registration_number: str,
        user_id: int,
        item_id: int,
        session: AsyncSession
) -> None:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(
                Request.registration_number == registration_number
            )
            .options(
                so.selectinload(Request.item_associations).joinedload(RequestItem.item)
            )
        )

        request = request_result.scalar_one()

        if request.status not in (RequestStatus.IN_PROGRESS, RequestStatus.PARTIALLY_FULFILLED):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        association_num = next(
            (i for i, request_item in enumerate(request.item_associations) if request_item.item_id == item_id),
            None
        )

        request.item_associations[association_num].status = RequestItemStatus.COMPLETED
        
        sum_items_completed = sum(
            filter(lambda x: x.status == (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED), request.item_associations)
        )
        sum_items_completed_and_planned = sum(
            filter(
                lambda x: x.status in (RequestItemStatus.PLANNED, RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED),
                request.item_associations
            )
        )
        
        if len(request.item_associations) == sum_items_completed:
            request.status = RequestStatus.COMPLETED
        
        elif len(request.item_associations) == sum_items_completed_and_planned:
            request.status = RequestStatus.PLANNED
            
        else:
            request.status = RequestStatus.PARTIALLY_FULFILLED

        new_history = RequestHistory(
            action=RequestAction.COMPLETED,
            request_id=request.id,
            user_id=user_id,
            description=f"Предмет: {item_association.item.name} выполнен"
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error execute request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error execute request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Добавление предмета в планирование
@connection
async def sql_planning_request(
        registration_number: str,
        user_id: int,
        data: PlanningRequest,
        session: AsyncSession
) -> None:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(
                Request.registration_number == registration_number
            )
            .options(
                so.selectinload(Request.item_associations).joinedload(RequestItem.item)
            )
        )

        request = request_result.scalar_one()

        if request.status not in (RequestStatus.IN_PROGRESS, RequestStatus.PARTIALLY_FULFILLED):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        association_num = next(
            (i for i, request_item in enumerate(request.item_associations) if request_item.item_id == item_id),
            None
        )

        request.item_associations[association_num].status = RequestItemStatus.PLANNED
        request.item_associations[association_num].deadline_planning = data.deadline
        
        sum_items_completed_and_planned = sum(
            filter(
                lambda x: x.status in (RequestItemStatus.PLANNED, RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED),
                request.item_associations
            )
        )
        
        if len(request.item_associations) == sum_items_completed_and_planned:
            request.status = RequestStatus.PLANNED
            
        else:
            request.status = RequestStatus.PARTIALLY_FULFILLED

        new_history = RequestHistory(
            action=RequestAction.PLANNED,
            request_id=request.id,
            user_id=user_id,
            description=f"Предмет: {item_association.item.name} отправлен в планирование"
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error planning request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error planning request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
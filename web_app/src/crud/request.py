# Внешние зависимости
from typing import List, Optional, Dict, Any
from collections import defaultdict
from datetime import datetime, timezone
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
                                ManagementDepartment, ExecutorOrganization, RequestItemStatus,
                                STATUS_ID_MAPPING, REQUEST_ITEM_STATUS_ID_MAPPING, REQUEST_ITEM_STATUS_MAPPING,
                                Department)
from web_app.src.core import connection
from web_app.src.schemas import (CreateRequest, RequestResponse, RequestDetailResponse,
                                 RequestHistoryResponse, RequestDataResponse, RightsResponse,
                                 RedirectRequest, UserResponse, AttachmentsRequest, ItemsNameRequest,
                                 ItemsNameRequestFull, RedirectRequestWithDeadline, RequestExecutorResponse,
                                 PlanningRequest, ActualStatusRequest, ACTUAL_STATUS_MAPPING_FOR_REQUEST_STATUS,
                                 ACTUAL_STATUS_MAPPING_FOR_REQUEST_ITEM_STATUS, DocumentData, DocumentItem)
from web_app.src.utils import delete_files, generate_pdf
from web_app.src.crud.departament import sql_get_all_department


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


# Вспомогательная функция для получения просрочки заявке для управляющих
def get_overdue_request_for_management(
    role: UserRole,
    request: Request
) -> bool:
    
    if (role not in (UserRole.MANAGEMENT, UserRole.MANAGEMENT_DEPARTMENT) or
        request.status == RequestStatus.FINISHED):
        return False
        
    now = datetime.now(timezone.utc)
    for association in request.item_associations:
        if ((association.deadline_executor and association.deadline_executor < now) or
            (association.deadline_organization and association.deadline_organization < now) or
            (association.deadline_planning and association.deadline_planning < now)):
            return True

    return False


# Вспомогательная функция для получения просрочки заявке для исполнителей
def get_overdue_request_for_executor(
    association: RequestItem
) -> bool:        
    now = datetime.now(timezone.utc)
    if ((association.deadline_executor and association.deadline_executor < now) or
        (association.deadline_organization and association.deadline_organization < now) or
        (association.deadline_planning and association.deadline_planning < now)):
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
        fio_secretary: str,
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
            if not (data.items and len(data.description) > 0):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request type")

        department_code_address_result = await session.execute(
            sa.Select(Department.code, Department.address)
            .where(Department.id == department_id)
        )
        department_code_address = department_code_address_result.all()

        if not department_code_address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        department_code, department_address = department_code_address[0]

        judge_user_result = await session.execute(
            sa.select(User)
            .select_from(Judge)
            .join(User, Judge.user_id == User.id)
            .where(Judge.id == judge_id)
        )
        judge_user = judge_user_result.scalar_one_or_none()

        if judge_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Judge not found")

        fio_judge = judge_user.full_name.split(" ")

        registration_number = str(uuid.uuid4())
        processed_items = {}

        if data.items:
            for item in data.items:
                if processed_items.get(item.id) is None:
                    processed_items[item.id] = {
                        "item_id": item.id,
                        "count": item.quantity
                    }
                else:
                    processed_items[item.id]["count"] += item.quantity

        item_names_result = await session.execute(
            sa.select(Item.id, Item.name)
            .where(Item.id.in_(tuple(processed_items.keys())))
        )
        item_names = item_names_result.all()

        data_for_pdf = DocumentData(
            date=datetime.now().strftime("%d.%m.%Y"),
            department_number=department_code,
            address=department_address,
            items=[
                DocumentItem(
                    name=item[1],
                    count=processed_items[item[0]]["count"]
                )
                for item in item_names
            ],
            secretary=fio_secretary,
            judge=f"{' '.join(tuple(f'{part[0]}.' for part in fio_judge[1:]))} {fio_judge[0]}"
        )

        document_info = generate_pdf(data=data_for_pdf, filename=registration_number)

        new_request = Request(
            registration_number=registration_number,
            description=data.description,
            request_type=request_type,
            pdf_request_url=document_info.file_url,
            is_emergency=data.is_emergency,
            secretary_id=secretary_id,
            judge_id=judge_id,
            department_id=department_id
        )
        session.add(new_request)
        await session.flush()

        new_request.human_registration_number = f"{new_request.id}-{department_code}-{datetime.now().year}"

        if processed_items:
            for key in processed_items:
                processed_items[key]["request_id"] = new_request.id

            # Связываем предметы с заявкой
            await session.execute(request_item.insert().values(tuple(processed_items.values())))

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
        status_filter_id: Optional[int] =  None,
        type_filter_id: Optional[int] =  None,
        department_filter_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 10
) -> List[RequestResponse]:
    try:
        query = (
            sa.select(Request)
        ).offset((page - 1) * page_size).limit(page_size).order_by(Request.created_at.desc())

        if user.is_secretary:
            query = query.where(Request.secretary_id == user.secretary_profile.id)

        elif user.is_judge:
            query = query.where(Request.judge_id == user.judge_profile.id)

        elif user.is_management:
            query = (query.where(
                Request.status != RequestStatus.REGISTERED
            ).where(
                sa.or_(
                    Request.status == RequestStatus.CONFIRMED,
                    Request.management_id == user.management_profile.id
                )
            ).options(
                so.selectinload(Request.item_associations)
            ))

        elif user.is_management_department:
            query = query.where(
                Request.management_department_id == user.management_department_profile.id
            ).options(
                so.selectinload(Request.item_associations)
            )

        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        if isinstance(status_filter_id, int):
            status_filter = next(
                (status_["name"].lower() for status_ in STATUS_ID_MAPPING if status_["id"] == status_filter_id),
                None
            )
            if STATUS_MAPPING.get(status_filter):
                query = query.where(Request.status == STATUS_MAPPING[status_filter])

        else:
            query = query.where(Request.status == RequestStatus.REGISTERED)

        if isinstance(type_filter_id, int):
            type_filter = next(
                (type_["name"].lower() for type_ in TYPE_ID_MAPPING if type_["id"] == type_filter_id),
                None
            )
            if TYPE_MAPPING.get(type_filter):
                query = query.where(Request.request_type == TYPE_MAPPING[type_filter])

        if isinstance(department_filter_id, int):
            query = query.where(Request.department_id == department_filter_id)

        requests_result = await session.execute(query)
        requests = requests_result.scalars()

        return [
            RequestResponse(
                registration_number=request.registration_number,
                human_registration_number=request.human_registration_number,
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
                    reject_after=request.status not in (RequestStatus.FINISHED,
                                                        RequestStatus.CANCELLED),
                    redirect_management_department=request.status not in (RequestStatus.CANCELLED,
                                                                          RequestStatus.FINISHED),
                    redirect_executor=request.status not in (RequestStatus.FINISHED, RequestStatus.CANCELLED),
                    redirect_org=request.status not in (RequestStatus.FINISHED, RequestStatus.CANCELLED),
                    deadline=request.status not in (RequestStatus.FINISHED, RequestStatus.CANCELLED),
                    planning=request.status not in (RequestStatus.FINISHED, RequestStatus.CANCELLED),
                    ready=request.status not in (RequestStatus.FINISHED, RequestStatus.CANCELLED),
                    confirm_management_department=request.status == RequestStatus.COMPLETED,
                    confirm_management=request.status == RequestStatus.ENDING_COMPLETED
                ),
                actual_status=(ActualStatusRequest.OVERDUE if get_overdue_request_for_management(user.role, request)
                               else ACTUAL_STATUS_MAPPING_FOR_REQUEST_STATUS[request.status])
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
    status_filter_id: Optional[int] = None,
    type_filter_id: Optional[int] = None,
    department_filter_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 10
) -> List[RequestExecutorResponse]:
    try:
        query = (
            sa.select(Request)
            .options(
                so.selectinload(Request.item_associations).joinedload(RequestItem.item)
            ).offset((page - 1) * page_size).limit(page_size).order_by(Request.created_at.desc())
        )

        conditions = []

        if user.is_executor:
            request_item_conditions = [
                RequestItem.executor_id == user.executor_profile.id
            ]
            validate_association = lambda a, u: a.executor_id == u.executor_profile.id

        elif user.is_executor_organization:
            request_item_conditions = [
                RequestItem.executor_organization_id == user.executor_organization_profile.id
            ]
            validate_association = lambda a, u: a.executor_organization_id == u.executor_organization_profile.id

        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        if isinstance(status_filter_id, int):
            status_filter = next(
                (status_["name"].lower() for status_ in REQUEST_ITEM_STATUS_ID_MAPPING \
                 if status_["id"] == status_filter_id),
                None
            )
            if REQUEST_ITEM_STATUS_MAPPING.get(status_filter):
                request_item_conditions.append(
                    RequestItem.status == REQUEST_ITEM_STATUS_MAPPING[status_filter]
                )
                validate_status = lambda s: s == REQUEST_ITEM_STATUS_MAPPING[status_filter]

        else:
            request_item_conditions.append(
                RequestItem.status != RequestItemStatus.PLANNED
            )
            validate_status = lambda s: s != RequestItemStatus.PLANNED

        conditions.append(
            Request.id.in_(
                sa.select(RequestItem.request_id).where(
                    sa.and_(*request_item_conditions)
                )
            )
        )

        if isinstance(type_filter_id, int):
            type_filter = next(
                (type_["name"].lower() for type_ in TYPE_ID_MAPPING if type_["id"] == type_filter_id),
                None
            )
            if TYPE_MAPPING.get(type_filter):
                conditions.append(Request.request_type == TYPE_MAPPING[type_filter])

        if isinstance(department_filter_id, int):
            conditions.append(Request.department_id == department_filter_id)

        query = query.where(sa.and_(*conditions))

        requests_result = await session.execute(query)
        requests = requests_result.scalars().all()

        return [
            RequestExecutorResponse(
                registration_number=request.registration_number,
                human_registration_number=request.human_registration_number,
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
                actual_status=(ActualStatusRequest.OVERDUE if get_overdue_request_for_executor(association)
                               else ACTUAL_STATUS_MAPPING_FOR_REQUEST_ITEM_STATUS[association.status])
            )
            for request in requests
            for association in request.item_associations
            if validate_association(association, user) and validate_status(association.status)
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
    department_filter_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 10
) -> List[RequestExecutorResponse]:
    try:
        query = (
            sa.select(Request)
            .options(
                so.selectinload(Request.item_associations).joinedload(RequestItem.item)
            ).offset((page - 1) * page_size).limit(page_size)
        )

        if isinstance(department_filter_id, int):
            query = query.where(Request.department_id == department_filter_id)

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

        query = query.where(sa.and_(*conditions))

        requests_result = await session.execute(query)
        requests = requests_result.scalars().all()

        return [
            RequestExecutorResponse(
                registration_number=request.registration_number,
                human_registration_number=request.human_registration_number,
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
                ),
                actual_status=(ActualStatusRequest.OVERDUE if get_overdue_request_for_executor(association)
                               else ActualStatusRequest.PLANNED)
            )
            for request in requests
            for association in request.item_associations
            if validate_association(association, user) and association.status == RequestItemStatus.PLANNED
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view requests for planning: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error view requests for planning: {e}")
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
                name=(f"{association.item.name} "
                      f"{association.item.description if association.item.description else ''}").strip(),
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
                description_completed=association.description_completed if association.description_completed else None,
                deadline_executor=association.deadline_executor,
                deadline_organization=association.deadline_organization,
                status=association.status,
                access=right_item and not user.is_executor_organization
            ))

        return RequestDetailResponse(
            registration_number=request.registration_number,
            human_registration_number=request.human_registration_number,
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
            department_name=f"№{request.department.code} {request.department.name} ({request.department.address})",
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
            pdf_request=request.pdf_signed_request_url if request.pdf_signed_request_url else request.pdf_request_url,
            attachments=[
                AttachmentsRequest(
                    file_name=attachment.file_name,
                    content_type=attachment.document_type,
                    file_path=attachment.file_path.replace("web_app/src", ""),
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
                reject_after=request.status not in (RequestStatus.FINISHED, RequestStatus.CANCELLED),
                redirect_management_department=request.status not in (RequestStatus.FINISHED,
                                                                      RequestStatus.CANCELLED),
                redirect_executor=request.status not in (RequestStatus.FINISHED,
                                                         RequestStatus.CANCELLED),
                redirect_org=request.status not in (RequestStatus.FINISHED,
                                                    RequestStatus.CANCELLED),
                deadline=request.status not in (RequestStatus.FINISHED, RequestStatus.CANCELLED),
                planning=request.status not in (RequestStatus.FINISHED, RequestStatus.CANCELLED),
                ready=request.status not in (RequestStatus.FINISHED, RequestStatus.CANCELLED),
                confirm_management_department=request.status == RequestStatus.COMPLETED,
                confirm_management=request.status == RequestStatus.ENDING_COMPLETED
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

        request_result = await session.execute(
            query
            .options(
                so.joinedload(Request.secretary).joinedload(Secretary.user),
                so.joinedload(Request.judge).joinedload(Judge.user),
                so.joinedload(Request.department)
            )
        )

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

        if data.is_emergency != request.is_emergency:
            view_emergency = lambda x: "Аварийная" if x else "Обычная"
            list_update.append(f"Изменена срочность: {view_emergency(request.is_emergency)} "
                               f"-> {view_emergency(data.is_emergency)}")
            request.is_emergency = data.is_emergency

        items_ids = tuple(item.id for item in data.items)

        processed_items = {}
        if data.items:
            for item in data.items:
                if processed_items.get(item.id) is None:
                    processed_items[item.id] = {
                        "item_id": item.id,
                        "count": item.quantity
                    }
                else:
                    processed_items[item.id]["count"] += item.quantity

        item_names_result = await session.execute(
            sa.select(Item.id, Item.name)
            .where(Item.id.in_(items_ids))
        )
        item_names = item_names_result.all()
        fio_judge = request.judge.user.full_name.split(" ")

        data_for_pdf = DocumentData(
            date=datetime.now().strftime("%d.%m.%Y"),
            department_number=request.department.code,
            address=request.department.address,
            items=[
                DocumentItem(
                    name=item[1],
                    count=processed_items[item[0]]["count"]
                )
                for item in item_names
            ],
            secretary=request.secretary.user.full_name,
            judge=f"{' '.join(tuple(f'{part[0]}.' for part in fio_judge[1:]))} {fio_judge[0]}"
        )

        generate_pdf(data=data_for_pdf, filename=registration_number)

        # Удаляем записи и возвращаем удаленные данные
        delete_result = await session.execute(
            sa.delete(request_item).where(
                sa.and_(
                    request_item.c.request_id == request.id,
                    request_item.c.item_id.notin_(items_ids)
                )
            ).returning(request_item.c.item_id)
        )

        # Получаем удаленные item_id
        deleted_item_ids = [row[0] for row in delete_result]

        # Находим все существующие записи для данной заявки
        existing_items_result = await session.execute(
            sa.select(request_item.c.item_id, request_item.c.count).where(
                sa.and_(
                    request_item.c.request_id == request.id,
                    request_item.c.item_id.in_(items_ids)
                )
            )
        )
        existing_items = {row.item_id: row.count for row in existing_items_result}

        items_to_update = []
        new_items = []
        items_to_process = []

        for item_data in data.items:
            item_id = item_data.id
            new_quantity = item_data.quantity

            if item_id in existing_items:
                # Если количество изменилось - добавляем в обновление
                if existing_items[item_id] != new_quantity:
                    items_to_update.append({
                        "request_id": request.id,
                        "item_id": item_id,
                        "count": new_quantity
                    })
                    items_to_process.append(item_id)
            else:
                # Если записи нет - добавляем новую
                new_items.append({
                    "request_id": request.id,
                    "item_id": item_id,
                    "count": new_quantity
                })
                items_to_process.append(item_id)

        # Обновляем существующие записи с новым количеством
        updated_item_ids = set()
        if items_to_update:
            # Создаем CASE выражение для массового обновления
            case_stmt = sa.case(
                *[(request_item.c.item_id == item["item_id"], item["count"]) for item in items_to_update],
                else_=request_item.c.count
            )

            update_stmt = sa.update(request_item).where(
                sa.and_(
                    request_item.c.request_id == request.id,
                    request_item.c.item_id.in_([item["item_id"] for item in items_to_update])
                )
            ).values(count=case_stmt)

            update_result = await session.execute(update_stmt.returning(request_item.c.item_id))
            updated_item_ids = {row[0] for row in update_result}

        # Добавляем новые записи
        inserted_item_ids = set()
        if new_items:
            insert_result = await session.execute(
                request_item.insert().returning(request_item.c.item_id),
                new_items
            )
            inserted_item_ids = {row[0] for row in insert_result}

        # Собираем все измененные ID для получения информации о предметах
        all_changed_ids = inserted_item_ids.union(updated_item_ids).union(deleted_item_ids)

        if all_changed_ids:
            update_items_result = await session.execute(
                sa.select(Item.id, Item.name, Item.description)
                .where(Item.id.in_(all_changed_ids))
            )
            update_items = update_items_result.all()

            del_info = []
            add_info = []
            update_info = []

            # Создаем словарь для быстрого доступа к данным о количестве
            quantity_map = {item.id: item.quantity for item in data.items}
            existing_quantity_map = existing_items

            for item in update_items:
                item_id, item_name, item_description = item

                if item_id in deleted_item_ids:
                    del_info.append(f"Удален предмет: {item_name} {item_description or ''}")

                if item_id in inserted_item_ids:
                    quantity = quantity_map.get(item_id, 1)
                    add_info.append(f"Добавлен предмет: {item_name} {item_description or ''} (количество: {quantity})")

                if item_id in updated_item_ids:
                    old_quantity = existing_quantity_map.get(item_id, 1)
                    new_quantity = quantity_map.get(item_id, 1)
                    update_info.append(
                        f"Обновлен предмет: {item_name} {item_description or ''} (количество: {old_quantity} → {new_quantity})")

            if del_info:
                list_update.append("\n".join(del_info))

            if add_info:
                list_update.append("\n".join(add_info))

            if update_info:
                list_update.append("\n".join(update_info))

        if data.attachments:
            for attachment in data.attachments:
                list_update.append(f"Прикреплен файл: {attachment.file_name}")
                new_document = RequestDocument(
                    document_type=attachment.content_type,
                    file_path=attachment.file_path,
                    file_name=attachment.file_name,
                    size=attachment.size,
                    request_id=request.id
                )
                session.add(new_document)

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
        import traceback
        traceback.print_exc()
        config.logger.error(f"Unexpected error edit data request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Подтвреждение заявки
@connection
async def sql_approve_request(
    registration_number: str,
    user_id: int,
    judge_id: int,
    signed_pdf_url: str,
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
        request.pdf_signed_request_url = signed_pdf_url

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

        exists_executor_flag = next((True for obj in request.item_associations if obj.executor_id is not None), False)
        if exists_executor_flag:
            request_item = next((obj for obj in request.item_associations if obj.item_id == data.item_id), None)
            if request_item is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

            if request_item.status in (RequestStatus.REGISTERED, RequestStatus.CANCELLED) or \
                    request_item.status in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

            request_item.executor_id = data.user_role_id
            request_item.description_executor = data.description
            request_item.deadline_executor = data.deadline

            description = (f"Заявка отправлена на выполнение\nИсполнитель: {executor.user.full_name}\n"
                           f"Срок: {data.deadline.strftime("%d.%m.%Y")}")

        else:
            for obj in request.item_associations:
                obj.executor_id = data.user_role_id
                obj.description_executor = data.description
                obj.deadline_executor = data.deadline

            description = (f"Заявки отправлены на выполнение\nИсполнитель для всех заявок: {executor.user.full_name}\n"
                           f"Срок: {data.deadline.strftime("%d.%m.%Y")}")

        new_history = RequestHistory(
            action=RequestAction.APPOINTED,
            request_id=request.id,
            user_id=user_id,
            description=description
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


# Назначение организации-исполнителя заявки
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
        comment: Optional[str],
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

        if request.status not in (RequestStatus.IN_PROGRESS, RequestStatus.PARTIALLY_FULFILLED, RequestStatus.PLANNED):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        association_num = next(
            (i for i, request_item in enumerate(request.item_associations) if request_item.item_id == item_id),
            None
        )

        request.item_associations[association_num].status = RequestItemStatus.COMPLETED
        if comment is not None:
            request.item_associations[association_num].description_completed = comment

        sum_items_completed = sum(
            1 for item in request.item_associations
            if item.status in (RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED)
        )
        sum_items_completed_and_planned = sum(
            1 for item in request.item_associations
            if item.status in (RequestItemStatus.PLANNED, RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED)
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
            description=f"Предмет: {request.item_associations[association_num].item.name} выполнен"
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
            (i for i, request_item in enumerate(request.item_associations) if request_item.item_id == data.item_id),
            None
        )

        request.item_associations[association_num].status = RequestItemStatus.PLANNED
        request.item_associations[association_num].deadline_planning = data.deadline
        
        sum_items_completed_and_planned = sum(
            1 for item in request.item_associations
            if item.status in (RequestItemStatus.PLANNED, RequestItemStatus.COMPLETED, RequestItemStatus.CANCELLED)
        )
        
        if len(request.item_associations) == sum_items_completed_and_planned:
            request.status = RequestStatus.PLANNED
            
        else:
            request.status = RequestStatus.PARTIALLY_FULFILLED

        new_history = RequestHistory(
            action=RequestAction.PLANNED,
            request_id=request.id,
            user_id=user_id,
            description=f"Предмет: {request.item_associations[association_num].item.name} отправлен в планирование"
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


# Завершение заявки
@connection
async def sql_finish_request(
        registration_number: str,
        user: User,
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

        if user.is_management_department and request.status == RequestStatus.COMPLETED:
            action = RequestAction.ENDING_COMPLETED
            description = "Выполнение заявки подтверждено"
            request.status = RequestStatus.ENDING_COMPLETED

        elif user.is_management and request.status == RequestStatus.ENDING_COMPLETED:
            action = RequestAction.FINISHED
            description = "Заявка завершена"
            request.status = RequestStatus.FINISHED

        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        new_history = RequestHistory(
            action=action,
            request_id=request.id,
            user_id=user.id,
            description=description
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error finish request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error finish request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Удаляем прикрепленные файлы
@connection
async def sql_delete_attachment(
    registration_number: str,
    filename: str,
    user: User,
    session: AsyncSession
) -> None:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(
                Request.registration_number == registration_number,
            )
            .options(
                so.selectinload(Request.related_documents)
            )
        )
        request = request_result.scalar_one()

        if user.is_secretary and not request.secretary_id == user.secretary_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        elif user.is_judge and not request.judge_id == user.judge_profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        file = next((f for f in request.related_documents if f.file_name == filename), None)

        if file is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        delete_files(file_paths=[file.file_path])
        await session.delete(file)

        new_history = RequestHistory(
            action=RequestAction.UPDATE,
            request_id=request.id,
            user_id=user.id,
            description=f"Удален прикрепленный файл: {filename}"
        )
        session.add(new_history)

        await session.commit()

    except NoResultFound:
        config.logger.info(f"Request not found by registration_number: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error delete file: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error delete file: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выводим список заявок для скачивания
@connection
async def sql_get_requests_for_download(
        session: AsyncSession,
        status_filter_id: int,
        type_filter_id: Optional[int] = None,
        department_filter_id: Optional[int] = None,
        date_filter_from: Optional[datetime] = None,
        date_filter_until: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    try:
        query = (
            sa.select(Request)
            .options(
                so.selectinload(Request.item_associations).joinedload(RequestItem.item)
            )
        )

        status_filter = next(
            (status_["name"].lower() for status_ in STATUS_ID_MAPPING if status_["id"] == status_filter_id),
            None
        )
        if STATUS_MAPPING.get(status_filter):
            query = query.where(Request.status == STATUS_MAPPING[status_filter])

        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status not found")

        if isinstance(type_filter_id, int):
            type_filter = next(
                (type_["name"].lower() for type_ in TYPE_ID_MAPPING if type_["id"] == type_filter_id),
                None
            )
            if TYPE_MAPPING.get(type_filter):
                query = query.where(Request.request_type == TYPE_MAPPING[type_filter])

        if isinstance(department_filter_id, int):
            query = query.where(Request.department_id == department_filter_id)

        if date_filter_from:
            query = query.where(Request.created_at >= date_filter_from)

        if date_filter_until:
            query = query.where(Request.created_at <= date_filter_until)

        requests_result = await session.execute(query)
        requests = requests_result.scalars()

        return [
            {
                "Индентификатор": request.id,
                "Номер": request.registration_number,
                "Предметы": "\n".join(f"{association.item.name} ({association.count}шт.)" \
                                      for association in request.item_associations),
                "Тип": request.request_type.value,
                "Статус": request.status.value,
                "Аварийность": "Да" if request.is_emergency else "Нет",
                "Создана": request.created_at.strftime("%d.%m.%Y %H:%M")
            }
            for request in requests
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view requests for download: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error view requests for download: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выводим список заявок из планирования для скачивания
@connection
async def sql_get_planning_for_download(
    session: AsyncSession,
    department_filter_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    try:
        query = (
            sa.select(RequestItem)
            .where(
                RequestItem.status == RequestItemStatus.PLANNED
            ).options(
                so.joinedload(RequestItem.item),
                so.joinedload(RequestItem.request)
            )
        )

        if isinstance(department_filter_id, int):
            query = query.where(RequestItem.request.department_id == department_filter_id)

        request_items_result = await session.execute(query)
        request_items = request_items_result.scalars()

        return [
            {
                "Номер заявки": request_item.request.registration_number,
                "Предмет": request_item.item.name,
                "Количество": request_item.count,
                "Сроки": request_item.deadline_planning.strftime("%d.%m.%Y %H:%M")
            }
            for request_item in request_items
        ]

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view planning for download: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        config.logger.error(f"Unexpected error view planning for download: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выводим количество заявок пользователя
@connection
async def sql_get_count_requests_by_user(
    user: User,
    current_department: Optional[int],
    current_type: Optional[int],
    session: AsyncSession
) -> List[Dict[str, Any]]:
    try:
        if user.role in (UserRole.EXECUTOR, UserRole.EXECUTOR_ORGANIZATION):
            query = sa.select(
                RequestItem.status,
                sa.func.count(RequestItem.status).label('count')
            ).join(
                Request, RequestItem.request_id == Request.id
            ).group_by(RequestItem.status)

            status_mapping = tuple(REQUEST_ITEM_STATUS_MAPPING.values())
            status_mapping_id = REQUEST_ITEM_STATUS_ID_MAPPING

            if user.is_executor:
                query = query.where(RequestItem.executor_id == user.executor_profile.id)

            else:
                query = query.where(RequestItem.executor_organization_id == user.executor_organization_profile.id)
        else:
            query = sa.select(
                Request.status,
                sa.func.count(Request.status).label('count')
            ).group_by(Request.status)

            if user.is_secretary:
                status_mapping = tuple(STATUS_MAPPING.values())
                status_mapping_id = STATUS_ID_MAPPING
                query = query.where(Request.secretary_id == user.secretary_profile.id)

            elif user.is_judge:
                status_mapping = tuple(STATUS_MAPPING.values())
                status_mapping_id = STATUS_ID_MAPPING
                query = query.where(Request.judge_id == user.judge_profile.id)

            elif user.is_management:
                status_mapping = tuple(STATUS_MAPPING.values())[1:]
                status_mapping_id = STATUS_ID_MAPPING[1:]
                query = query.where(
                    sa.or_(
                        Request.status == RequestStatus.CONFIRMED,
                        Request.management_id == user.management_profile.id
                    )
                )

            elif user.is_management_department:
                status_mapping = tuple(STATUS_MAPPING.values())[2:]
                status_mapping_id = STATUS_ID_MAPPING[2:]
                query = query.where(Request.management_department_id == user.management_department_profile.id)

            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        if current_department is not None:
            query = query.where(Request.department_id == current_department)

        if current_type is not None:
            type_name = next(
                (type_["name"].lower() for type_ in TYPE_ID_MAPPING if type_["id"] == current_type),
                None
            )
            if type_name is not None:
                query = query.where(Request.request_type == TYPE_MAPPING[type_name])

        requests_status_result = await session.execute(query)
        requests_status = requests_status_result.all()

        status_count = defaultdict(int, {s: count for s, count in requests_status})

        result = []
        for value, status_info in zip(status_mapping, status_mapping_id):
            result.append({
                **status_info,
                "count": status_count[value]
            })

        return result

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view count requests: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error view count requests: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Выводим количество планируемых заявок пользователя
@connection
async def sql_get_count_planning_requests_by_user(
    user: User,
    session: AsyncSession
) -> List[Dict[str, Any]]:
    try:
        query = (
            sa.select(
                Request.department_id,
                sa.func.count(Request.department_id).label('count')
            )
            .join(RequestItem, Request.id == RequestItem.request_id)
            .where(RequestItem.status == RequestItemStatus.PLANNED)
            .group_by(Request.department_id)
        )

        if user.is_management:
           query = query.where(Request.management_id == user.management_profile.id)

        elif user.is_management_department:
            query = query.where(Request.management_department_id == user.management_department_profile.id)

        elif user.is_executor:
            query = query.where(RequestItem.executor_id == user.executor_profile.id)

        elif user.is_executor_organization:
            query = query.where(RequestItem.executor_organization_id == user.executor_organization_profile.id)

        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")

        planning_department_result = await session.execute(query)
        planning_department = planning_department_result.all()
        planning_count = defaultdict(int, {dept_id: count for dept_id, count in planning_department})

        department = await sql_get_all_department(session=session, no_decor=True)

        result = []

        for department_info in department:
            result.append({
                **department_info,
                "count": planning_count[department_info["id"]]
            })

        return result

    except SQLAlchemyError as e:
        config.logger.error(f"Database error view count planning: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error view count planning: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Проверяем принадлежит ли заявка судье
@connection
async def sql_check_request_for_sign_by_judge(
    judge_id: int,
    registration_number: str,
    session: AsyncSession
) -> bool:
    try:
        request_result = await session.execute(
            sa.select(sa.exists().where(
                Request.registration_number == registration_number,
                Request.judge_id == judge_id,
                Request.status == RequestStatus.REGISTERED
            ))
        )
        return request_result.scalar()

    except SQLAlchemyError as e:
        config.logger.error(f"Database error check request by judge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error check request by judge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем данные о заявке для формирования pdf файла
@connection
async def sql_get_data_request_for_sign_by_judge(
    judge_id: int,
    registration_number: str,
    session: AsyncSession
) -> DocumentData:
    try:
        request_result = await session.execute(
            sa.select(Request)
            .where(
                Request.registration_number == registration_number,
                Request.judge_id == judge_id,
                Request.status == RequestStatus.REGISTERED
            )
            .options(
                so.selectinload(Request.item_associations).joinedload(RequestItem.item),
                so.joinedload(Request.secretary).joinedload(Secretary.user),
                so.joinedload(Request.judge).joinedload(Judge.user),
                so.joinedload(Request.department)
            )
        )

        request = request_result.scalar_one()
        fio_judge = request.judge.user.full_name.split(" ")

        return DocumentData(
            date=datetime.now().strftime("%d.%m.%Y"),
            department_number=request.department.code,
            address=request.department.address,
            items=[
                DocumentItem(
                    name=association.item.name,
                    count=association.count
                )
                for association in request.item_associations
            ],
            secretary=request.secretary.user.full_name,
            judge=f"{' '.join(tuple(f'{part[0]}.' for part in fio_judge[1:]))} {fio_judge[0]}"
        )

    except NoResultFound:
        config.logger.info(f"Request not found for sign by judge: {registration_number}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    except SQLAlchemyError as e:
        config.logger.error(f"Database error for sign by judge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except HTTPException:
        raise

    except Exception as e:
        config.logger.error(f"Unexpected error for sign by judge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
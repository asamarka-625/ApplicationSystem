from web_app.src.crud.user import (sql_chek_existing_user_by_name, sql_chek_existing_user_by_email,
                                   sql_get_user_by_id, sql_chek_update_role_by_user_id,
                                   sql_get_info_user_by_id, sql_get_user_by_username,
                                   sql_get_users_without_role, sql_update_role_by_user_id)
from web_app.src.crud.item import (sql_chek_existing_item_by_serial, sql_get_categories_choices,
                                   sql_chek_existing_category_by_name, sql_search_items,
                                   sql_create_category_and_items)
from web_app.src.crud.departament import sql_get_all_department
from web_app.src.crud.request import (sql_create_request, sql_get_requests_by_user, sql_get_request_details,
                                      sql_get_request_data, sql_edit_request, sql_approve_request,
                                      sql_reject_request, sql_redirect_executor_request,
                                      sql_execute_request, sql_redirect_management_request,
                                      sql_redirect_organization_request, sql_get_requests_for_executor,
                                      sql_get_planning_requests, sql_planning_request, sql_finish_request,
                                      sql_delete_attachment, sql_get_requests_for_download,
                                      sql_get_planning_for_download)
from web_app.src.crud.judge import sql_get_department_id_by_judge_id
from web_app.src.crud.executor import sql_get_executors
from web_app.src.crud.management_department import sql_get_management_departments
from web_app.src.crud.executor_organization import sql_get_executor_organizations
from web_app.src.crud.user import (sql_chek_existing_user_by_name, sql_chek_existing_user_by_email,
                                   sql_get_user_by_id)
from web_app.src.crud.item import (sql_chek_existing_item_by_serial, sql_get_categories_choices,
                                   sql_chek_existing_category_by_name, sql_search_items)
from web_app.src.crud.departament import sql_get_all_departament
from web_app.src.crud.request import (sql_create_request, sql_get_requests_by_user, sql_get_request_details,
                                      sql_get_requests_all)
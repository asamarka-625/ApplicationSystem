from web_app.src.admin.user import UserAdmin
from web_app.src.admin.secretary import SecretaryAdmin
from web_app.src.admin.judge import JudgeAdmin
from web_app.src.admin.management import ManagementAdmin
from web_app.src.admin.management_department import ManagementDepartmentAdmin
from web_app.src.admin.executor import ExecutorAdmin
from web_app.src.admin.executor_organization import ExecutorOrganizationAdmin

from web_app.src.admin.item import ItemAdmin
from web_app.src.admin.category import CategoryAdmin
from web_app.src.admin.request import RequestAdmin
from web_app.src.admin.departament import DepartmentAdmin
from web_app.src.admin.authentication import BasicAuthBackend

from web_app.src.core import config

authentication_backend = BasicAuthBackend(secret_key=config.SECRET_KEY)
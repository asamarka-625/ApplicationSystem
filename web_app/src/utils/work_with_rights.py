# Внешние зависимости
from typing import Dict
# Внутренние модули
from web_app.src.models import User


# Получение прав пользователя
def get_allowed_rights(current_user: User) -> Dict[str, bool]:
    return {
        "view": True,
        "edit": current_user.is_secretary or current_user.is_judge,
        "approve": current_user.is_judge,
        "reject_before": current_user.is_judge,
        "reject_after": current_user.is_management,
        "redirect_management_department": current_user.is_management,
        "redirect_executor": current_user.is_management or current_user.is_management_department,
        "redirect_org": current_user.is_management or current_user.is_management_department \
                        or current_user.is_executor,
        "deadline": current_user.is_management or current_user.is_management_department \
                    or current_user.is_executor_organization,
        "planning": current_user.is_management or current_user.is_management_department or current_user.is_executor,
        "ready": current_user.is_executor or current_user.is_executor_organization,
        "confirm_management_department": current_user.is_management_department,
        "confirm_management": current_user.is_management,
        "download": current_user.is_management or current_user.is_management_department
    }
from web_app.src.utils.validators import validate_phone_from_form, validate_phone_list
from web_app.src.utils.work_with_password import (verify_password, get_password_hash,
                                                  create_reset_token, generate_password)
from web_app.src.utils.redis_token_service import get_token_service
from web_app.src.utils.work_with_files import save_uploaded_files, delete_files
from web_app.src.utils.work_with_rights import get_allowed_rights
from web_app.src.utils.email_service import send_password_reset_email

token_service = get_token_service()
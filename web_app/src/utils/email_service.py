# Внешние зависимости
from datetime import datetime
from emails import Message
from emails.template import JinjaTemplate
# Внутренние модули
from web_app.src.core import config


# Отправка email для восстановления пароля
def send_password_reset_email(to_email: str, reset_token: str, username: str):
    reset_link = f"{config.FRONTEND_URL}/login/reset-password?token={reset_token}"

    # HTML шаблон письма
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: #4F46E5; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background: #f9f9f9; }
            .button { display: inline-block; padding: 12px 24px; background: #4F46E5; 
                     color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Восстановление пароля</h1>
            </div>
            <div class="content">
                <p>Здравствуйте, {{ username }}!</p>
                <p>Мы получили запрос на восстановление пароля для вашей учетной записи.</p>
                <p>Для установки нового пароля нажмите на кнопку ниже:</p>
                <p style="text-align: center;">
                    <a href="{{ reset_link }}" class="button">Восстановить пароль</a>
                </p>
                <p>Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.</p>
                <p>Ссылка действительна в течение 24 часов.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Текстовый вариант письма
    text_template = f"""
    Восстановление пароля

    Здравствуйте, {username}!

    Мы получили запрос на восстановление пароля для вашей учетной записи.

    Для установки нового пароля перейдите по ссылке:
    {reset_link}

    Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.

    Ссылка действительна в течение 24 часов.

    С уважением,
    Команда {config.APP_NAME}
    """

    try:
        message = Message(
            subject="Восстановление пароля",
            mail_from=config.EMAIL_FROM,
            html=JinjaTemplate(html_template).render(
                username=username,
                reset_link=reset_link,
                year=datetime.now().year,
                app_name=config.APP_NAME
            ),
            text=text_template
        )

        # Отправка через SMTP
        response = message.send(
            to=to_email,
            smtp={
                "host": config.SMTP_HOST,
                "port": config.SMTP_PORT,
                "user": config.SMTP_USERNAME,
                "password": config.SMTP_PASSWORD,
                "tls": True
            }
        )
        print(response.error)
        return response.success

    except Exception as e:
        config.logger.error(f"Ошибка отправки email {to_email}: {e}")
        return False


# Отправка email для подтверждения создания секретаря
def send_confirm_create_secretary_email(
    to_email: str,
    confirm_token: str,
    department: str,
    judge_name: str,
    secretary_name: str
):
    confirm_link = f"{config.FRONTEND_URL}/confirm-create-secretary?token={confirm_token}"

    # HTML шаблон письма
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
            .content { padding: 30px; background: #f9f9f9; border-radius: 0 0 8px 8px; }
            .info-box { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; 
                       border-left: 4px solid #667eea; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .button { display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }
            .button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3); }
            .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
            .detail { margin: 10px 0; }
            .detail-label { font-weight: bold; color: #4a5568; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Подтверждение создания аккаунта</h1>
                <p style="margin-top: 10px;">Секретарь судьи</p>
            </div>
            <div class="content">
                <p>Здравствуйте, <strong>{{ judge_name }}</strong>!</p>
                <p>Для судебного участка <strong>{{ department }}</strong> создана учетная запись секретаря судьи.</p>

                <div class="info-box">
                    <h3 style="margin-top: 0; color: #4F46E5;">Детали учетной записи:</h3>
                    <div class="detail">
                        <span class="detail-label">👨‍⚖️ Судья:</span> {{ judge_name }}
                    </div>
                    <div class="detail">
                        <span class="detail-label">🏛️ Судебный участок:</span> {{ department }}
                    </div>
                    <div class="detail">
                        <span class="detail-label">👤 Секретарь:</span> {{ secretary_name }}
                    </div>
                </div>

                <p>Для активации учетной записи нажмите на кнопку ниже:</p>
                <p style="text-align: center;">
                    <a href="{{ confirm_link }}" class="button">Подтвердить создание аккаунта</a>
                </p>

                <p>Если вы не ожидали это письмо или считаете, что оно было отправлено по ошибке, 
                пожалуйста, проигнорируйте его. Аккаунт будет автоматически удален через 24 часа 
                без подтверждения.</p>
                <p>Ссылка действительна в течение <strong>24 часов</strong>.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Текстовый вариант письма
    text_template = f"""
        Подтверждение создания аккаунта секретаря судьи
        
        Здравствуйте, {judge_name}!
        
        Для судебного участка { department } создана учетная запись секретаря судьи.
        
        Детали учетной записи:
        - Судья: {judge_name}
        - Судебный участок: {department}
        - Секретарь: {secretary_name}
        
        Для активации учетной записи перейдите по ссылке:
        {confirm_link}
        
        Если вы не ожидали это письмо или считаете, что оно было отправлено по ошибке, 
        пожалуйста, проигнорируйте его. Аккаунт будет автоматически удален через 24 часа 
        без подтверждения.
        
        Ссылка действительна в течение 24 часов.
        
        ---
        С уважением,
        Команда {config.APP_NAME}
        
        Это автоматическое сообщение, пожалуйста, не отвечайте на него.
    """

    try:
        message = Message(
            subject="Подтверждение создания аккаунта секретаря судьи",
            mail_from=config.EMAIL_FROM,
            html=JinjaTemplate(html_template).render(
                secretary_name=secretary_name,
                judge_name=judge_name,
                department=department,
                confirm_link=confirm_link,
                year=datetime.now().year,
                app_name=config.APP_NAME
            ),
            text=text_template
        )

        # Отправка через SMTP
        response = message.send(
            to=to_email,
            smtp={
                "host": config.SMTP_HOST,
                "port": config.SMTP_PORT,
                "user": config.SMTP_USERNAME,
                "password": config.SMTP_PASSWORD,
                "tls": True
            }
        )

        if response.success:
            config.logger.info(f"Email подтверждения отправлен на {to_email}")
        else:
            config.logger.error(f"Ошибка отправки email на {to_email}: {response.error}")

        return response.success

    except Exception as e:
        config.logger.error(f"Ошибка отправки email {to_email}: {e}")
        return False
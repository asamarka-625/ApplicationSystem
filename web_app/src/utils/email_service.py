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
            <div class="footer">
                <p>© {{ year }} {{ app_name }}. Все права защищены.</p>
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
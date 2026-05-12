# Внешние зависимости
import asyncio
import pandas as pd
# Внутренние модули
from web_app.src.utils import get_password_hash
from web_app.src.crud import sql_add_user_judge, sql_add_user


async def init_users():
    df = pd.read_excel("users.xlsx")

    # Цикл по строкам таблицы
    for index, row in df.iterrows():
        # Обращение к данным по имени колонки
        username = row["Логин"]

        department_code = None
        if "msud" in username:
            department_code = int(username.replace("msud", ""))

        email = row["Почта"]
        password = row["Пароль"]
        full_name = row["ФИО"]

        data = {
            "username": username,
            "email": email,
            "password": password,
            "password_hash": get_password_hash(password),
            "full_name": full_name
        }

        if department_code is not None:
            await sql_add_user_judge(
                department_code=department_code,
                data=data
            )

        else:
            await sql_add_user(data=data)


if __name__ == "__main__":
    asyncio.run(init_users())




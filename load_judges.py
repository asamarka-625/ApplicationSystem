# Внешние зависимости
from typing import Dict
import re
import secrets
import asyncio
from passlib.context import CryptContext
import pandas as pd
from sqlalchemy.util import await_only

# Внутренние модули
from web_app.src.crud import sql_add_user_judge


pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    # Опциональные настройки для большей безопасности
    argon2__time_cost=2,
    argon2__memory_cost=1024,
    argon2__parallelism=2,
)


def get_emails() -> Dict[int, str]:
    df = pd.read_excel("judge_emails.xlsx")

    result = {}
    for row in df.itertuples():
        match = re.search(r'\d+', str(row[1]))

        if match:
            number_department = int(match.group())

        else:
            raise ValueError("Number not found")

        result[number_department] = row[2].strip()

    return result


def get_judges() -> Dict[int, str]:
    df = pd.read_excel("judges.xlsx")

    result = {}
    for row in df.itertuples():
        match = re.search(r'\d+', str(row[2]))

        if match:
            number_department = int(match.group())

        else:
            raise ValueError("Number not found")

        result[number_department] = (" ".join(s for i, s in enumerate(row[3].strip().split()) if i < 3)).title()

    return result


async def generate_judges():
    emails = get_emails()
    judges = get_judges()

    insert_data = []
    for number_department, judge_name in judges.items():
        email = emails[number_department]
        username = email.split(".")[0]
        password = secrets.token_urlsafe(6)[:8]
        password_hash = pwd_context.hash(password)

        data = {
            "username": username,
            "email": email,
            "password": password,
            "password_hash": password_hash,
            "full_name": judge_name
        }

        insert_data.append(data)

        await sql_add_user_judge(
            department_code=number_department,
            data=data
        )

    df = pd.DataFrame(insert_data)
    df = df.drop(columns=["password_hash"])

    df = df.rename(columns={
        "username": "Логин",
        "email": "Почта",
        "password": "Пароль",
        "full_name": "ФИО Судьи"
    })

    df.to_excel("judge_users.xlsx", index=False)
    print("Файл успешно создан!")



if __name__ == "__main__":
    asyncio.run(generate_judges())




# Внешние зависимости
import asyncio
# Внутренние модули
from web_app.src.crud import sql_create_department


def get_department():
    with open("departments.txt", mode="r") as file:
        lines = file.readlines()

    content = " ".join(line.replace("\n", "") for line in lines)
    department_info = content.split("Санкт-Петербург,")

    postal_code = department_info[0].strip()
    result = {}
    for i in range(1, len(department_info)):
        address, court_number_postal_code = department_info[i].split("с/у")
        court_number_postal_code_words = court_number_postal_code.strip().split(" ")

        if i == (len(department_info) - 1):
            court_numbers = " ".join(court_number_postal_code_words)
            next_postal_code = "none"

        else:
            court_numbers = " ".join(court_number_postal_code_words[:-1])
            next_postal_code = court_number_postal_code_words[-1].strip()

        full_address = f"{postal_code} Санкт-Петербург, {address.strip()}".strip()
        court_numbers = court_numbers.replace("№", "").strip()
        court_numbers = court_numbers.split(",")
        list_court_numbers = []
        for number in court_numbers:
            number = number.strip()
            if "-" in number:
                start_number, end_number = number.split("-")
                for n in range(int(start_number), int(end_number) + 1):
                    list_court_numbers.append(n)

            elif number.isdigit():
                list_court_numbers.append(int(number))

            else:
                print(f"Error number: {number} ({court_numbers})")

        result[full_address] = list_court_numbers
        postal_code = next_postal_code

    for address, court_numbers in result.items():
        print(address, court_numbers)
    print(len(result))

    return result


async def main():
    department = get_department()
    for address, court_numbers in department.items():
        for court_number in court_numbers:
            await sql_create_department(
                name=f"Судебный участок № {court_number}",
                code=court_number,
                address=address,
                phone_numbers=["none"]
            )


if __name__ == "__main__":
    asyncio.run(main())

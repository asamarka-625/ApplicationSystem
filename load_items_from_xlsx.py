# Внешние зависимости
from typing import Dict
import pandas as pd
# Внутренние модули
from web_app.src.crud import sql_create_category_and_items


def parse_xlsx(filename: str) -> Dict[str, Dict[int, str]]:
    df = pd.read_excel(f"{filename}.xlsx")
    all_values = df.values.flatten().tolist()
    current_category = None
    current_items = {}
    current_item_id = None
    result = {}

    for value in all_values:
        if isinstance(value, str):
            if value.isupper():
                if current_category is not None:
                    result[current_category] = current_items
                    
                current_category = value.capitalize()
                current_items = {}
                
            else:
                if current_category is not None and current_item_id is not None:
                    if value.startswith("Штамп") or value.startswith("Угловой штамп"):
                        if value.startswith("Угловой штамп"):
                            item_name_part_1, last_part = value.split(" ", 1)
                            item_name_part_2, description_item = last_part.split("\n", 1)
                            item_name = f"{item_name_part_1} {item_name_part_2}"
                            
                        else:
                            item_name, description_item = value.split(" ", 1)
                            
                        if "Штемпель" in description_item:
                            start_index_shtempel = description_item.find("Штемпель") - 1
                            end_index_shtempel = description_item[start_index_shtempel:].rfind(")")
                            if end_index_shtempel >= 0:
                                end_index_shtempel += start_index_shtempel + 1
                                item_name = f"{item_name} {description_item[start_index_shtempel:end_index_shtempel]}"
                                description_item = f"{description_item[:start_index_shtempel]}{description_item[end_index_shtempel:]}"
                                
                            else:
                                item_name = f"{item_name} {description_item[start_index_shtempel:]})"
                                description_item = f"{description_item[:start_index_shtempel]}"
                        
                    else:
                        item_name, _, description_item = value.partition("(")
                        description_item = description_item.replace(")", "", 1).strip()
                    
                    item_name = item_name.strip()
                    description_item = description_item.strip()
                    current_items[current_item_id] = (item_name, description_item)
        
        elif isinstance(value, int):
            current_item_id = value
    
    if current_category is not None:
        result[current_category] = current_items
                    
    return result
    
    
if __name__ == "__main__":
    result = parse_xlsx(filename="items")
    import asyncio
    asyncio.run(sql_create_category_and_items(data=result))
        
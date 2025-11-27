# Внешние зависимости
from typing import Annotated, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
# Внутренние модули



# Схема данных для эмблемы pdf
class DucumentEmblem(BaseModel):
    owner: Annotated[str, Field(strict=True, strip_whitespace=True)]
    Thumbprint: Annotated[str, Field(strict=True, strip_whitespace=True)]
    valid_from: datetime
    valid_until: datetime


# Схема возвращаемых данных о файле pdf
class DocumentResponse(BaseModel):
    file_url: Annotated[str, Field(strict=True, strip_whitespace=True)]


# Схема предмета в документе
class DocumentItem(BaseModel):
    name: Annotated[str, Field(strict=True, strip_whitespace=True)]
    count: Annotated[int, Field(ge=1)]\


# Схема данных, которые вставляются в документ
class DocumentData(BaseModel):
    date: Annotated[str, Field(strict=True, strip_whitespace=True)]
    department_number: Annotated[int, Field(ge=1)]
    address: Annotated[str, Field(strict=True, strip_whitespace=True)]
    items: List[DocumentItem]
    fio_secretary: Annotated[str, Field(strict=True, strip_whitespace=True)]
    fio_judge: Annotated[str, Field(strict=True, strip_whitespace=True)]
    siganture: Optional[DucumentEmblem] = None
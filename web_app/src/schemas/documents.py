# Внешние зависимости
from typing import Annotated
from datetime import datetime
from pydantic import BaseModel, Field
# Внутренние модули



# Схема данных для эмблемы pdf
class DucumentEmblem(BaseModel):
    owner: Annotated[str, Field(strict=True, strip_whitespace=True)]
    publisher: Annotated[str, Field(strict=True, strip_whitespace=True)]
    Thumbprint: Annotated[str, Field(strict=True, strip_whitespace=True)]
    valid_from: datetime
    valid_until: datetime


# Схема возвращаемых данных о файле pdf
class DocumentResponse(BaseModel):
    file_url: Annotated[str, Field(strict=True, strip_whitespace=True)]
import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel

Schema = BaseModel | Dict[str, Any]


class ResponseBase(BaseModel):
    """
    ResponseBase - общая модель ответа
        msg - основные данные ответа
        detail - дополнительная информация
    """

    msg: Optional[BaseModel] = None
    details: Optional[str] = None


class VerboseBase(BaseModel):
    id: Optional[uuid.UUID]


class EntityBulkBase(BaseModel):
    count: int = 0
    entity_result: list[BaseModel] = []

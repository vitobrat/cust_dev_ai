from typing import Any

from pydantic import BaseModel

Schema = BaseModel | dict[str, Any]

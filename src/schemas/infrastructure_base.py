from typing import Any, Dict

from pydantic import BaseModel

Schema = BaseModel | Dict[str, Any]

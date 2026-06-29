from typing import Any, Optional

from pydantic import BaseModel


class ApiMeta(BaseModel):
    success: bool = True
    message: Optional[str] = None


class ApiResponse(BaseModel):
    meta: ApiMeta
    data: Optional[Any] = None
    error: Optional[Any] = None


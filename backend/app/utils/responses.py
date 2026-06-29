from typing import Any, Optional

from app.schemas.common import ApiMeta


def success_response(data: Any = None, message: Optional[str] = None) -> dict:
    return {
        "meta": ApiMeta(success=True, message=message).model_dump(),
        "data": data,
        "error": None,
    }


def error_response(message: str, code: str, details: Any = None) -> dict:
    return {
        "meta": ApiMeta(success=False, message=message).model_dump(),
        "data": None,
        "error": {"code": code, "details": details},
    }


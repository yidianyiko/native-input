# routers/cancel.py
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from services.request_registry import RequestRegistry

router = APIRouter()

_request_registry: RequestRegistry | None = None


def init_dependencies(rr: RequestRegistry) -> None:
    global _request_registry
    _request_registry = rr


def get_request_registry() -> RequestRegistry:
    if _request_registry is None:
        raise RuntimeError("RequestRegistry not initialized")
    return _request_registry


class CancelRequest(BaseModel):
    userId: str
    requestId: str


class CancelResponse(BaseModel):
    status: str


@router.post("/api/cancel", response_model=CancelResponse)
async def cancel(
    request: CancelRequest,
    rr: RequestRegistry = Depends(get_request_registry),
):
    if not rr.cancel(request.userId, request.requestId):
        raise HTTPException(
            status_code=404,
            detail=f"Request {request.requestId} not found for user {request.userId}"
        )

    return CancelResponse(status="ok")

"""
HTTP Server Routes

Defines the FastAPI endpoints for receiving external input.
"""

from typing import Callable, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter

router = APIRouter()

# Callback set by HttpServerService at startup
_on_text_received: Optional[Callable[[str, int, int], None]] = None


def set_text_callback(callback: Callable[[str, int, int], None]) -> None:
    """Register the callback invoked when text is received via POST."""
    global _on_text_received
    _on_text_received = callback


class InputRequest(BaseModel):
    """Request body for POST /api/input."""
    text: str = Field(..., description="The text content to send as input")
    button_number: int = Field(default=1, description="Button identifier")
    role_number: int = Field(default=1, description="Role identifier")


class InputResponse(BaseModel):
    """Response body for POST /api/input."""
    status: str
    message: str


@router.post("/api/input", response_model=InputResponse)
async def receive_input(request: InputRequest) -> InputResponse:
    """Receive text from an external client and forward it to the floating window."""
    if not request.text.strip():
        return InputResponse(status="error", message="Empty text")

    if _on_text_received:
        _on_text_received(request.text, request.button_number, request.role_number)

    return InputResponse(status="ok", message="Text received")


@router.get("/health")
async def health() -> dict:
    """Simple health-check endpoint."""
    return {"status": "ok"}

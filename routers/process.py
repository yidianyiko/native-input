# routers/process.py
import asyncio
import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from services.connection_manager import ConnectionManager
from services.request_registry import RequestRegistry
from services.prompt_loader import PromptLoader
from services.agent_service import AgentService
from services.constants import DEFAULT_USER_ID

router = APIRouter()

# Global instances
_connection_manager: ConnectionManager | None = None
_request_registry: RequestRegistry | None = None
_prompt_loader: PromptLoader | None = None
_agent_service: AgentService | None = None


def init_dependencies(
    cm: ConnectionManager,
    rr: RequestRegistry,
    pl: PromptLoader,
    agent: AgentService
) -> None:
    global _connection_manager, _request_registry, _prompt_loader, _agent_service
    _connection_manager = cm
    _request_registry = rr
    _prompt_loader = pl
    _agent_service = agent


def get_connection_manager() -> ConnectionManager:
    if _connection_manager is None:
        raise RuntimeError("ConnectionManager not initialized")
    return _connection_manager


def get_request_registry() -> RequestRegistry:
    if _request_registry is None:
        raise RuntimeError("RequestRegistry not initialized")
    return _request_registry


def get_prompt_loader() -> PromptLoader:
    if _prompt_loader is None:
        raise RuntimeError("PromptLoader not initialized")
    return _prompt_loader


def get_agent_service() -> AgentService:
    if _agent_service is None:
        raise RuntimeError("AgentService not initialized")
    return _agent_service


class ProcessRequest(BaseModel):
    text: str
    button_number: int
    role_number: int


class ProcessResponse(BaseModel):
    status: str
    requestId: str
    message: str


async def process_task(
    request: ProcessRequest,
    request_id: str,
    prompt: str,
    cancel_event: asyncio.Event,
    cm: ConnectionManager,
    rr: RequestRegistry,
    agent: AgentService,
):
    try:
        await cm.send_start(DEFAULT_USER_ID, request_id)

        seq = 0
        async for chunk in agent.process_stream(
            text=request.text,
            prompt_template=prompt,
            user_id=DEFAULT_USER_ID,
            request_id=request_id,
            cancel_event=cancel_event,
        ):
            if cancel_event.is_set():
                break
            seq += 1
            await cm.send_chunk(DEFAULT_USER_ID, request_id, seq, chunk)

        if not cancel_event.is_set():
            await cm.send_done(DEFAULT_USER_ID, request_id)

    except Exception as e:
        await cm.send_error(DEFAULT_USER_ID, request_id, "PROCESSING_ERROR", str(e))
    finally:
        rr.complete(DEFAULT_USER_ID, request_id)


@router.post("/api/process", response_model=ProcessResponse)
async def process(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    cm: ConnectionManager = Depends(get_connection_manager),
    rr: RequestRegistry = Depends(get_request_registry),
    pl: PromptLoader = Depends(get_prompt_loader),
    agent: AgentService = Depends(get_agent_service),
):
    # Check WebSocket connection exists
    if not cm.has_connection(DEFAULT_USER_ID):
        raise HTTPException(
            status_code=409,
            detail="No WebSocket connection"
        )

    # Get prompt template
    try:
        prompt = pl.get_prompt_by_numbers(request.button_number, request.role_number, "{text}")
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Generate request ID and register
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    cancel_event = rr.register(DEFAULT_USER_ID, request_id)

    # Start background processing
    background_tasks.add_task(
        process_task,
        request,
        request_id,
        prompt,
        cancel_event,
        cm,
        rr,
        agent,
    )

    return ProcessResponse(
        status="ok",
        requestId=request_id,
        message="Processing started"
    )

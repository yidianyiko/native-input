# main.py
from fastapi import FastAPI

from services.connection_manager import ConnectionManager
from services.request_registry import RequestRegistry
from services.prompt_loader import PromptLoader
from services.agent_service import AgentService

from routers import websocket as ws_router
from routers import process as process_router
from routers import cancel as cancel_router

app = FastAPI(title="Agent Service", version="0.1.0")

# Initialize shared dependencies
connection_manager = ConnectionManager()
request_registry = RequestRegistry()
prompt_loader = PromptLoader()
agent_service = AgentService()

# Inject dependencies into routers
ws_router.init_dependencies(connection_manager, request_registry)
process_router.init_dependencies(connection_manager, request_registry, prompt_loader, agent_service)
cancel_router.init_dependencies(request_registry)

# Include routers
app.include_router(ws_router.router)
app.include_router(process_router.router)
app.include_router(cancel_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

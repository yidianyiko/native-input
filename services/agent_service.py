# services/agent_service.py
import os
import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from agno.agent import Agent, RunEvent
from agno.db.sqlite import SqliteDb
from agno.models.deepseek import DeepSeek

from app.credentials import load_deepseek_api_key

key = load_deepseek_api_key()
if key and not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = key


class AgentService:
    def __init__(self, db_path: str = "agent_memory.db"):
        self._db_path = db_path
        self._db = SqliteDb(db_file=db_path)

    def _create_agent(self, user_id: str) -> Agent:
        return Agent(
            model=DeepSeek(id="deepseek-chat"),
            db=self._db,
            add_history_to_context=True,
            num_history_runs=5,
            markdown=True,
        )

    async def process_stream(
        self,
        text: str,
        prompt_template: str,
        user_id: str,
        request_id: str,
        cancel_event: asyncio.Event,
    ) -> AsyncGenerator[str, None]:
        prompt = prompt_template.format(text=text)
        agent = self._create_agent(user_id)

        # Use session_id to scope memory by user
        stream = agent.run(prompt, session_id=user_id, stream=True)

        for chunk in stream:
            if cancel_event.is_set():
                break

            if hasattr(chunk, 'event') and chunk.event == RunEvent.run_content:
                if chunk.content:
                    yield chunk.content
            elif hasattr(chunk, 'content') and chunk.content:
                # Fallback for simpler response format
                yield chunk.content

            # Allow other tasks to run
            await asyncio.sleep(0)

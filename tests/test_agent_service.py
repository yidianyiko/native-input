# tests/test_agent_service.py
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.agent_service import AgentService


@pytest.fixture
def agent_service():
    return AgentService()


class TestAgentService:
    @pytest.mark.asyncio
    async def test_process_stream_yields_chunks(self, agent_service):
        cancel_event = asyncio.Event()
        chunks = []

        with patch.object(agent_service, '_create_agent') as mock_create:
            # Mock the agent to return predictable chunks
            mock_agent = MagicMock()
            mock_stream = [
                MagicMock(event="run_content", content="Hello "),
                MagicMock(event="run_content", content="World"),
            ]
            mock_agent.run = MagicMock(return_value=iter(mock_stream))
            mock_create.return_value = mock_agent

            async for chunk in agent_service.process_stream(
                text="test",
                prompt_template="Process: {text}",
                user_id="user1",
                request_id="req1",
                cancel_event=cancel_event
            ):
                chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0] == "Hello "
        assert chunks[1] == "World"

    @pytest.mark.asyncio
    async def test_process_stream_stops_on_cancel(self, agent_service):
        cancel_event = asyncio.Event()
        chunks = []

        with patch.object(agent_service, '_create_agent') as mock_create:
            mock_agent = MagicMock()

            def slow_stream():
                yield MagicMock(event="run_content", content="First")
                cancel_event.set()  # Cancel after first chunk
                yield MagicMock(event="run_content", content="Second")

            mock_agent.run = MagicMock(return_value=slow_stream())
            mock_create.return_value = mock_agent

            async for chunk in agent_service.process_stream(
                text="test",
                prompt_template="Process: {text}",
                user_id="user1",
                request_id="req1",
                cancel_event=cancel_event
            ):
                chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0] == "First"

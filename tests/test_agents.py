from unittest.mock import Mock, patch

import pytest

from agentic_ai.agents.combiner_agent import CombinerAgent
from agentic_ai.agents.master_agent import MasterAgent
from agentic_ai.agents.order_agent import OrderAgent
from agentic_ai.agents.pdf_agent import PDFAgent
from agentic_ai.state.agent_state import AgentState
from agentic_ai.utils.llm_utils import LLMConfig


@pytest.fixture
def mock_llm_config():
    return Mock(spec=LLMConfig)


@pytest.fixture
def mock_qdrant_client():
    with patch("qdrant_client.QdrantClient") as mock:
        yield mock


@pytest.fixture
def base_state():
    return AgentState(
        query="test query",
        selected_agents=[],
        agent_queries={},
        agent_outputs={},
        dashboard_id=1,
        model_name="gpt-4",
        model_providers="openai",
        verbose={},
        pdf_file_path=[],
    )


@pytest.mark.asyncio
async def test_master_agent(mock_llm_config, base_state):
    # Setup
    agent = MasterAgent(mock_llm_config)
    mock_llm_config.get_llm().predict_messages.return_value.content = "order inventory"

    # Execute
    result = await agent.run(base_state)

    # Assert
    assert "selected_agents" in result
    assert isinstance(result["selected_agents"], list)


@pytest.mark.asyncio
async def test_order_agent(mock_llm_config, mock_qdrant_client, base_state):
    # Setup
    agent = OrderAgent(mock_llm_config)
    mock_qdrant_client.search.return_value = []
    base_state["agent_queries"]["order"] = "test order query"

    # Execute
    result = await agent.run(base_state)

    # Assert
    assert "agent_outputs" in result
    assert "order" in result["agent_outputs"]


@pytest.mark.asyncio
async def test_combiner_agent(mock_llm_config, base_state):
    # Setup
    agent = CombinerAgent(mock_llm_config)
    base_state["agent_outputs"] = {
        "order": "order response",
        "inventory": "inventory response",
    }
    mock_llm_config.get_llm().predict_messages.return_value.content = (
        "combined response"
    )

    # Execute
    result = await agent.run(base_state)

    # Assert
    assert "agent_outputs" in result
    assert "final" in result["agent_outputs"]
    assert isinstance(result["agent_outputs"]["final"], str)


@pytest.mark.asyncio
async def test_agent_chain(mock_llm_config, mock_qdrant_client, base_state):
    # Setup agents
    master = MasterAgent(mock_llm_config)
    order = OrderAgent(mock_llm_config)
    combiner = CombinerAgent(mock_llm_config)

    # Configure mocks
    mock_llm_config.get_llm().predict_messages.return_value.content = "test response"
    mock_qdrant_client.search.return_value = []

    # Execute chain
    state = await master.run(base_state)
    state = await order.run(state)
    final_state = await combiner.run(state)

    # Assert
    assert "agent_outputs" in final_state
    assert "final" in final_state["agent_outputs"]
    assert isinstance(final_state["agent_outputs"]["final"], str)

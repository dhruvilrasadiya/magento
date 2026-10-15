import operator
from typing import Annotated, TypedDict
from typing import List, Dict
from typing_extensions import NotRequired


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """Merge two dictionaries with custom logic for agent outputs."""

    result = dict1.copy()
    result.update(dict2)
    return result


class AgentState(TypedDict):
    """State management for AI agents."""

    query: Annotated[str, operator.add]
    language: Annotated[str, operator.add]
    selected_agents: Annotated[list[str], operator.add]
    agent_queries: Annotated[dict[str, str], merge_dicts]
    agent_outputs: Annotated[dict[str, str], merge_dicts]
    session_id: Annotated[str, operator.add]
    model_name: str
    model_providers: str
    verbose: NotRequired[dict[str, dict]]
    pdf_file_path: Annotated[list[str], operator.add]
    metadata: Annotated[dict[str, str], merge_dicts]
    chat_history: List[Dict[str, str]]
    agent_dependencies: Annotated[dict[str, list[str]], merge_dicts]
    next_agent: str
    is_email: bool
    email_output: dict
    inbox_output: dict
    auto_send_email: bool

import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from ..state.agent_state import AgentState
from ..utils.llm_utils import LLMConfig


class GreetAgent:
    """Agent that handles greeting and conversational queries."""

    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()
        self.system_prompt = """
        You are a friendly assistant that handles greetings and casual conversation.
        Your role is to be warm, welcoming, and helpful while directing users toward more specific queries.
        
        When responding to greetings:
        1. Be friendly and personable
        2. Acknowledge the greeting
        3. Briefly mention the capabilities of the system
        4. Encourage the user to ask specific questions about orders, products, customers, analytics, or documents
        
        Keep responses concise and friendly.
        """

    async def process_query(self, query: str, state: AgentState) -> Dict[str, Any]:
        """Process a greeting query."""
        print(f"[INFO] GreetAgent: Processing query")
        
        language = state.get("language", "en-US")
        
        # Prepare greeting templates based on language
        if language == "nl":
            messages = [
                SystemMessage(
                    content=self.system_prompt
                    + "\nBeantwoord alle vragen in het Nederlands."
                ),
                HumanMessage(content=f"Query: {query}"),
            ]
        else:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"Query: {query}"),
            ]

        response = self.llm.invoke(messages)
        print("[LLM] Greet Agent Response ---> \n", response.content)
        
        return {
            "response": response.content,
        }

    async def run(self, state: AgentState) -> AgentState:
        """Run the greeting agent and update the state."""
        print("-----" * 20)
        print(f"[START] Greet Agent")
        
        query = state["agent_queries"].get("greet_agent", state["query"])
        results = {}
        if isinstance(query, list):
            for q in query:
                result = await self.process_query(q, state)
                results[q] = result["response"]
        else:
            result = await self.process_query(query, state)
            results[query] = result["response"]
        
        state["agent_outputs"]["greet_agent"] = json.dumps(results)
        print(f"[END] Greet Agent")
        print("-----" * 20)
        
        return state
import json
import logging
from typing import List, Dict
from langchain.schema import HumanMessage, SystemMessage

from ..state.agent_state import AgentState
from ..utils.llm_utils import LLMConfig, create_system_prompt


class CombinerAgent:
    """Agent responsible for combining responses from multiple agents into a coherent answer."""

    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()
        self.system_prompt = create_system_prompt("combiner")

    async def run(self, state: AgentState) -> AgentState:
        """Run the combiner agent and update the shared agent state."""

        agent_outputs = {
            agent: response
            for agent, response in state["agent_outputs"].items()
            if agent != "final" and response
        }

        print("-----" * 20)
        print(f"[INFO] CombinerAgent: Agent outputs are {agent_outputs}")
        print("-----" * 20)

        # if len(agent_outputs) == 1:
        #     print("[INFO] CombinerAgent: Only one agent output, no need to combine.")
        #     state["agent_outputs"]["final"] = json.loads(list(agent_outputs.values())[0])[query]
        #     return state

        if not agent_outputs:
            logging.warning("[CombinerAgent] No agent responses available to combine.")
            state["agent_outputs"]["final"] = "No agent responses to combine."
            return state

        # Get the original query and dependencies for context
        query = state["query"]
        dependencies = state.get("agent_dependencies", {})

        # Add dependency information to the context
        dependency_info = ""
        if dependencies:
            dependency_info = "\nAgent Dependencies:\n"
            for agent, deps in dependencies.items():
                dependency_info += f"- {agent} depends on: {', '.join(deps)}\n"

        combined_response = await self.combine_responses(
            query=query, agent_outputs=agent_outputs, dependencies=dependencies
        )

        state["agent_outputs"]["final"] = combined_response
        return state

    async def combine_responses(
        self,
        query: str,
        agent_outputs: Dict[str, str],
        dependencies: Dict[str, List[str]],
    ) -> str:
        """
        Generate a unified response from multiple agent outputs using the LLM.

        Args:
            query (str): The original user query.
            agent_outputs (Dict[str, str]): A dictionary of agent responses.
            dependencies (Dict[str, List[str]]): A dictionary of agent dependencies.

        Returns:
            str: The final combined response.
        """

        context = self._format_agent_responses(agent_outputs)

        # Add dependency information to help the LLM understand the flow
        dependency_context = ""
        if dependencies:
            dependency_context = "\nAgent Dependencies:\n"
            for agent, deps in dependencies.items():
                if agent in agent_outputs and deps:
                    dependency_context += (
                        f"- {agent} used information from: {', '.join(deps)}\n"
                    )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=(
                    f"Original Query:\n{query}\n\n"
                    f"Agent Responses:\n{context}\n"
                    f"{dependency_context}\n\n"
                    "Provide a clear and unified response that integrates the key points from each agent, "
                    "respecting the dependencies between agents."
                )
            ),
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logging.error(f"[CombinerAgent] LLM invocation failed: {e}")
            return "An error occurred while generating the final response."

    def _format_agent_responses(self, agent_outputs: Dict[str, str]) -> str:
        """
        Format the outputs from individual agents for inclusion in the LLM context.

        Args:
            agent_outputs (Dict[str, str]): Agent names and their respective outputs.

        Returns:
            str: Formatted multi-agent response block.
        """

        return "\n\n".join(
            f"{agent.upper()} AGENT:\n{output.strip()}"
            for agent, output in agent_outputs.items()
            if output
        )

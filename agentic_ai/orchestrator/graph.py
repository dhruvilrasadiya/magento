from typing import Any, AsyncIterator, Dict, List, Tuple
from typing import Any, AsyncIterator, Dict, List, Tuple

from langgraph.graph import StateGraph
import traceback as tb
from ..agents.combiner_agent import CombinerAgent
from ..agents.master_agent import MasterAgent
from ..agents.order_agent import OrderAgent
from ..agents.product_agent import ProductAgent
from ..agents.pdf_agent import PDFAgent
from ..agents.customer_agent import CustomerAgent
from ..agents.analytics_agent import AnalyticsAgent
from ..agents.greet_agent import GreetAgent
from ..agents.email_agent import EmailAgent
from ..state.agent_state import AgentState
from ..utils.llm_utils import LLMConfig
from api.database.chat import fetch_chat_history


class AgentOrchestrator:
    """Orchestrates the flow of information between different AI agents."""

    def __init__(self, llm_config: LLMConfig, email_config: Dict[str, str]):
        # Initialize all agents
        self.master_agent = MasterAgent(llm_config)
        self.order_agent = OrderAgent(llm_config)
        self.product_agent = ProductAgent(llm_config)
        self.pdf_agent = PDFAgent(llm_config)
        self.customer_agent = CustomerAgent(llm_config)
        self.analytics_agent = AnalyticsAgent(llm_config)
        self.greet_agent = GreetAgent(llm_config)
        self.combiner_agent = CombinerAgent(llm_config)
        self.email_agent = EmailAgent(llm_config, email_config)

        # Create and compile the graph
        self.graph = self._build_graph()

    async def _route_to_next_agent(self, state: AgentState) -> str:
        """
        Determine the next agent to run based on dependencies and completion status.

        Args:
            state: The current agent state

        Returns:
            The name of the next agent to run, or "combiner_agent" if all agents are complete
        """
        # Get list of agents that have already completed
        completed_agents = list(state["agent_outputs"].keys())

        # Get dependencies for each agent
        dependencies = state.get("agent_dependencies", {})
        agent_query = state.get("agent_queries", {})

        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies(dependencies)
        if circular_deps:
            print(f"[WARNING] Detected circular dependencies: {circular_deps}")
            # Break circular dependencies by selecting the first agent in the cycle
            for agent_pair in circular_deps:
                agent1, agent2 = agent_pair
                if (
                    agent1 not in completed_agents
                    and agent1 in state["selected_agents"]
                ):
                    print(
                        f"[ROUTER] Breaking circular dependency by selecting: {agent1}"
                    )
                    state["next_agent"] = agent1
                    return state

        # Check each selected agent
        for agent in state["selected_agents"]:
            # Skip if agent has already completed
            if agent not in completed_agents:
                # Get dependencies for this agent
                agent_deps = dependencies.get(agent, [])

                # Check if all dependencies are satisfied
                deps_satisfied = all(dep in completed_agents for dep in agent_deps)

                # If all dependencies are satisfied, return this agent
                if deps_satisfied:
                    print(f"[ROUTER] Selected next agent: {agent}")
                    state["next_agent"] = agent
                    return state

        # If no agent is ready or all agents are complete, return combiner_agent
        print("[ROUTER] All agents complete or no agent ready, routing to combiner")
        state["next_agent"] = "combiner_agent"
        return state

    def _detect_circular_dependencies(
        self, dependencies: Dict[str, List[str]]
    ) -> List[Tuple[str, str]]:
        """
        Detect circular dependencies between agents.

        Args:
            dependencies: Dictionary of agent dependencies

        Returns:
            List of agent pairs with circular dependencies
        """
        circular_deps = []

        for agent, deps in dependencies.items():
            for dep in deps:
                # Check if the dependency also depends on this agent
                if dep in dependencies and agent in dependencies[dep]:
                    circular_deps.append((agent, dep))

        return circular_deps

    def _build_graph(self) -> StateGraph:
        """Build the agent interaction graph."""
        graph = StateGraph(AgentState)

        # Add nodes for each agent
        graph.add_node("master_agent", self.master_agent.run)
        graph.add_node("order_agent", self.order_agent.run)
        graph.add_node("product_agent", self.product_agent.run)
        graph.add_node("pdf_agent", self.pdf_agent.run)
        graph.add_node("customer_agent", self.customer_agent.run)
        graph.add_node("analytics_agent", self.analytics_agent.run)
        graph.add_node("greet_agent", self.greet_agent.run)
        graph.add_node("combiner_agent", self.combiner_agent.run)
        graph.add_node("email_agent", self.email_agent.run)

        # Add router node
        graph.add_node("router", self._route_to_next_agent)

        # Add edge from master agent to router
        graph.add_edge("master_agent", "router")

        # Add edges from router to each agent
        graph.add_conditional_edges(
            "router",
            lambda state: state["next_agent"],
            {
                "order_agent": "order_agent",
                "product_agent": "product_agent",
                "pdf_agent": "pdf_agent",
                "customer_agent": "customer_agent",
                "analytics_agent": "analytics_agent",
                "combiner_agent": "combiner_agent",
                "email_agent": "email_agent",
                "greet_agent": "greet_agent",
            },
        )

        # Add edges from each agent back to router
        graph.add_edge("order_agent", "router")
        graph.add_edge("product_agent", "router")
        graph.add_edge("pdf_agent", "router")
        graph.add_edge("customer_agent", "router")
        graph.add_edge("analytics_agent", "router")
        graph.add_edge("greet_agent", "router")
        graph.add_edge("email_agent", "router")

        # Set entry and exit points
        graph.set_entry_point("master_agent")
        graph.set_finish_point("combiner_agent")

        return graph.compile()

    async def process_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """Process a user query through the agent graph."""
        # Initialize state
        try:
            print("-----")
            print("Inside Process Query")

            if query.startswith("/email"):
                kwargs["is_email"] = True

            initial_state = AgentState(
                query=query,
                language=kwargs.get("language", "en-US"),
                selected_agents=[],
                agent_queries={},
                agent_outputs={},
                session_id=kwargs.get("session_id"),
                model_name=kwargs.get("model_name", "gpt-4o-mini"),
                model_providers=kwargs.get("model_providers", "openai"),
                verbose=kwargs.get("verbose", {}),
                pdf_file_path=kwargs.get("pdf_file_path", []),
                chat_history=fetch_chat_history(kwargs.get("session_id")),
                is_email=kwargs.get("is_email", False),
                auto_send_email=kwargs.get("auto_send_email", False),
            )

            print(initial_state)
            print("-----")
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            print("-----")
            print("Complete Query")
            print("-----")
            # print(final_state)
            if query.startswith("/email"):
                return {
                    "response": final_state["agent_outputs"].get(
                        "final", "No response generated"
                    ),
                    "email_output": final_state["email_output"],
                    "is_email": True,
                    "metadata": {
                        "language": final_state["language"],
                        "selected_agents": final_state["selected_agents"],
                        "agent_queries": final_state["agent_queries"],
                        "sources": final_state.get("metadata", {}),
                    },
                }
            return {
                "response": final_state["agent_outputs"].get(
                    "final", "No response generated"
                ),
                "is_email": False,
                "metadata": {
                    "language": final_state["language"],
                    "selected_agents": final_state["selected_agents"],
                    "agent_queries": final_state["agent_queries"],
                    "sources": final_state.get("metadata", {}),
                },
            }
            # return  final_state
        except Exception as e:
            print("*" * 30)
            print(f"ERROR\n{e}\n{tb.format_exc()}")
            print("*" * 30)

    async def process_stream(self, query: str, **kwargs) -> AsyncIterator[str]:
        """Process a user query with streaming response."""
        # Initialize state similar to process_query

        initial_state = AgentState(
            query=query,
            language=kwargs.get("language", "en-US"),
            selected_agents=[],
            agent_queries={},
            agent_outputs={},
            session_id=kwargs.get("session_id"),
            model_name=kwargs.get("model_name", "gpt-4"),
            model_providers=kwargs.get("model_providers", "openai"),
            verbose=kwargs.get("verbose", {}),
            pdf_file_path=kwargs.get("pdf_file_path", []),
        )

        # Run the graph with streaming
        async for chunk in self.graph.astream(initial_state):
            if "agent_outputs" in chunk and "final" in chunk["agent_outputs"]:
                yield chunk["agent_outputs"]["final"]

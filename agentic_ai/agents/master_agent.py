import re
import json
import logging
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Union
from ..state.agent_state import AgentState
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from ..utils.llm_utils import LLMConfig, create_system_prompt

AGENT_NAMES = [
    "order_agent",
    "product_agent",
    "pdf_agent",
    "customer_agent",
    "analytics_agent",
    "greet_agent",
    "email_agent",
]


class MasterAgent:
    """
    Master Agent responsible for query analysis and agent coordination.
    """

    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()

    def parse_duplicate_keys_json(
        self, raw_content: str, agent_names: List[str]
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Parses raw JSON-like string with possible duplicate keys (agent names)
        and aggregates duplicates into lists.

        Args:
            raw_content (str): Raw JSON string from LLM output.
            agent_names (List[str]): List of all valid agent keys.

        Returns:
            Dict[str, Union[str, List[str]]]: A dict mapping each agent to its query/queries.
        """
        result = defaultdict(list)

        for agent in agent_names:
            # Find all occurrences of this agent key
            pattern = rf'"({agent})"\s*:\s*"([^"]+)"'
            matches = re.findall(pattern, raw_content)
            for _, value in matches:
                result[agent].append(value)

        # Fallback: if no matches found, try parsing normally
        if not result:
            try:
                return json.loads(raw_content)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse LLM output as JSON: {e}")
                return {}

        # If only one value, unwrap it from list
        return {
            key: values if len(values) > 1 else values[0]
            for key, values in result.items()
        }

    async def run(self, state: AgentState) -> AgentState:
        """
        Run the master agent analysis and update the state.
        """
        print("**" * 30)
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[START] MasterAgent processing query at {start_time}")

        query = state["query"]

        # Check if the query is a simple greeting
        if self._is_greeting(query):
            print(f"[INFO] Detected greeting query: '{query}'")
            return {
                "query": query,
                "agent_queries": {"greet_agent": query},
                "selected_agents": ["greet_agent"],
                "agent_dependencies": {},
            }

        selected_agents = {}
        agent_dependencies = {}

        classification_prompt = PromptCreation.get_agent_classification_prompt()
        dependency_prompt = PromptCreation.get_agent_dependency_prompt()

        chat_history = state["chat_history"]
        messages = [SystemMessage(content=classification_prompt.strip())]
        for chat in chat_history:
            if chat["role"] == "user":
                messages.append(HumanMessage(content=chat["content"].strip()))
            elif chat["role"] == "assistant":
                messages.append(AIMessage(content=chat["content"].strip()))

        # Now, include the current query as the latest human message
        messages.append(HumanMessage(content=query.strip()))

        try:
            response = self.llm.invoke(messages)

            print(response.content)
            agent_mapping = self.parse_duplicate_keys_json(
                response.content.strip(), AGENT_NAMES
            )
            print("----------agent_mapping-------------")
            print(agent_mapping)
            print("----------agent_mapping-------------")
            if not agent_mapping:
                selected_agents = {"order_agent": query}
            else:
                selected_agents.update(agent_mapping)

            # Determine agent dependencies
            if len(selected_agents) > 1:
                dependency_messages = [
                    SystemMessage(content=dependency_prompt.strip()),
                    HumanMessage(
                        content=f"User Query: {query}\n\nSelected Agents: {json.dumps(selected_agents)}"
                    ),
                ]

                dependency_response = self.llm.invoke(dependency_messages)
                print("**" * 30)
                print("dependency_response")
                print(dependency_response.content)
                print("**" * 30)
                try:
                    dependencies = json.loads(dependency_response.content.strip())
                    agent_dependencies = dependencies.get("agent_dependencies", {})

                    # Check for and resolve circular dependencies
                    agent_dependencies = self._resolve_circular_dependencies(
                        agent_dependencies
                    )

                except json.JSONDecodeError:
                    print(f"Error parsing dependencies: {dependency_response.content}")
                    agent_dependencies = {}

            print(f"Selected Agents: {selected_agents}")
            print(f"Agent Dependencies: {agent_dependencies}")
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            print(f"[END] MasterAgent completed at {end_time}")
            print("**" * 30)

            # Update state with analysis results
            state["selected_agents"] = list(selected_agents.keys())
            state["agent_queries"] = selected_agents
            state["agent_dependencies"] = agent_dependencies

            return state
        except Exception as e:
            logging.error(f"Error in MasterAgent: {str(e)}")
            return {
                "query": query,
                "agent_queries": {"order_agent": query},
                "selected_agents": ["order_agent"],
                "agent_dependencies": {},
            }

    def _resolve_circular_dependencies(
        self, dependencies: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Detect and resolve circular dependencies.

        Args:
            dependencies: Dictionary of agent dependencies

        Returns:
            Updated dependencies with circular dependencies resolved
        """
        resolved_deps = dependencies.copy()

        # Check for circular dependencies
        for agent, deps in dependencies.items():
            for dep in deps:
                # Check if the dependency also depends on this agent
                if dep in dependencies and agent in dependencies[dep]:
                    print(
                        f"[WARNING] Detected circular dependency between {agent} and {dep}"
                    )

                    # Resolve by keeping the dependency in only one direction
                    # We'll keep the dependency where the agent name comes first alphabetically
                    if agent < dep:
                        print(f"[INFO] Keeping dependency: {dep} depends on {agent}")
                        if dep in resolved_deps:
                            resolved_deps[dep] = [
                                d for d in resolved_deps[dep] if d != agent
                            ]
                    else:
                        print(f"[INFO] Keeping dependency: {agent} depends on {dep}")
                        if agent in resolved_deps:
                            resolved_deps[agent] = [
                                d for d in resolved_deps[agent] if d != dep
                            ]

        return resolved_deps

    def _is_greeting(self, query: str) -> bool:
        """
        Determine if a query is a simple greeting.

        Args:
            query: The user query

        Returns:
            True if the query is a greeting, False otherwise
        """
        # Normalize the query
        normalized_query = query.lower().strip()

        # List of common greetings
        greetings = [
            "hi",
            "hello",
            "hey",
            "greetings",
            "good morning",
            "good afternoon",
            "good evening",
            "howdy",
            "what's up",
            "sup",
            "hiya",
            "yo",
            "hallo",
            "hoi",
            "goedemorgen",
            "goedemiddag",
            "goedenavond",  # Dutch greetings
        ]

        # Check if the query is just a greeting
        if any(normalized_query == greeting for greeting in greetings):
            return True

        # Check if the query starts with a greeting and is short (less than 5 words)
        if any(normalized_query.startswith(greeting) for greeting in greetings):
            word_count = len(normalized_query.split())
            if word_count < 5:
                return True

        return False


class PromptCreation:
    """Generates structured prompts for query classification and sub-agent selection."""

    @staticmethod
    def get_agent_classification_prompt() -> str:
        return f"""
            You are an intelligent query router tasked with breaking down a user's query into minimal sub-queries and 
            assigning each to the most suitable agent based on its data source.

            **IMPORTANT INSTRUCTIONS**

            1. **DO NOT** guess or assume agent capabilities beyond the descriptions provided.
            2. A single user query may contain **multiple sub-questions** — break them down clearly.
            3. A **sub-question may require input from multiple agents** — assign it to all relevant agents.
            4. Output MUST be a valid **JSON object**: {{ "agent_name": "sub-query", ... }}.
            - If multiple agents are required, list each separately
            5. DO NOT include any additional text or comments. Output **only the raw JSON**.
            6. If you're unsure, default to:
                {{ "order_agent": "<entire user query>", "analytics_agent": "<entire user query>", "product_agent": "<entire user query>" }}
            7. For simple greetings or casual conversation, use the greet_agent.
            8. If query is related to analytics of total products, total orders, total customers etc. use the analytics_agent.
            9. **Email Agent Priority**: If query starts with /email or /inbox, contains email-related keywords, or mentions email tasks, use email_agent.
            10. **Contextual Email Handling**: Pay attention to contextual references like "above information", "this conversation", "previous response", "our chat", etc. when routing email queries.

            AVAILABLE AGENTS & THEIR DATA SOURCES

            order_agent: Order ID, item list, shipping status, order totals, fulfillment, order-specific data.
            product_agent: Stock levels, price, brand, supplier, attributes, image, general product info (excluding PDF specs).
            pdf_agent: Product specifications, datasheets, manuals, documents.
            customer_agent: Customer profile, name, address, order history, invoices, cart details.
            analytics_agent: Business-level KPIs, sales trends, revenue analysis, product performance, customer metrics.
            greet_agent: Handles greetings, casual conversation, and general assistance.
            email_agent: Handles all email-related queries and tasks including - Composing and sending emails
                - **CONTEXTUAL EMAIL TASKS**: Sending conversation summaries, previous responses, chat history, or any referenced information from the current session
                - **CONTEXTUAL REFERENCES**: "above information", "this conversation", "our chat", "previous response", "summary", "discussed", "mentioned"

            FEW-SHOT EXAMPLES

            [Greeting]
            Query: Hello there!
            {{
                "greet_agent": "Hello there!"
            }}
            
            [Single Sub-query]
            Query: What is the price of iPhone 13?
            {{
                "product_agent": "What is the price of iPhone 13?"
            }}
            Query: What are the specs for JBL Bluetooth speaker?
            {{
                "pdf_agent": "What are the specs for JBL Bluetooth speaker?"
            }}

            [Email Agent Examples]
            Query: /email Send order confirmation to customer
            {{
                "email_agent": "Send order confirmation to customer"
            }}

            [Contextual Email Examples - Chat History References]
            Query: Please send summary of our conversation to john.doe@company.com
            {{
                "email_agent": "Send summary of our conversation to john.doe@company.com"
            }}

            Query: /email Email the above information to niral.patel@enlightvision.com
            {{
                "email_agent": "Email the above information to niral.patel@enlightvision.com"
            }}

            Query: Email this order details to the customer
            {{
                "email_agent": "Email this order details to the customer"
            }}

            Query: /inbox get latest 5 emails
            {{
                "email_agent": "/inbox get latest 5 emails"
            }}

            [Contextual Email Examples - Previous Response References]
            Query: Email the order status we just checked to the customer
            {{
                "email_agent": "Email the order status we just checked to the customer"
            }}

            [Contextual Email + Data Retrieval Combined]
            Query: Check order 242509174 status and email the details to customer
            {{
                "order_agent": "Check order 242509174 status",
                "email_agent": "Email the order details to customer"
            }}

            Query: Get customer info for ID 157743 and send welcome email
            {{
                "customer_agent": "Get customer info for ID 157743",
                "email_agent": "Send welcome email to customer"
            }}

            Query: Find product specs for iPhone and email them to customer
            {{
                "pdf_agent": "Find product specs for iPhone",
                "email_agent": "Email the product specs to customer"
            }}

            [Email + Other Agents Combined]
            Query: Send order confirmation email for order 12345 and check its shipping status
            {{
                "email_agent": "Send order confirmation email for order 12345",
                "order_agent": "Check shipping status for order 12345"
            }}

            Query: Email the customer about their order and update their profile
            {{
                "email_agent": "Email the customer about their order",
                "customer_agent": "Update customer profile"
            }}

            Query: Send stock alert email for low inventory items and show current stock levels
            {{
                "email_agent": "Send stock alert email for low inventory items",
                "product_agent": "Show current stock levels for low inventory items"
            }}


            [Multiple Sub-queries to One Agent]
            Query: What's the address and cart contents of customer ID 2201?
            {{
                "customer_agent": "What's the address of customer ID 2201?",
                "customer_agent": "What are the cart contents of customer ID 2201?"
            }}

            [Multiple Agents]
            Query: What is the spec sheet for Sony TV and how much stock is available?
            {{
                "pdf_agent": "What is the spec sheet for Sony TV?",
                "product_agent": "How much stock is available for Sony TV?"
            }}

            [Same Sub-query, Multiple Agents]
            Query: How many MacBooks were sold last month and how many are currently in stock?
            {{
                "analytics_agent": "How many MacBooks were sold last month?",
                "product_agent": "How many MacBooks are currently in stock?"
            }}

            [Analytics + Specific Data]
            Query: Show me the top 5 most ordered products last quarter with their current stock.
            {{
                "analytics_agent": "What are the top 5 most ordered products last quarter?",
                "product_agent": "What is the current stock of those top 5 products?"
            }}

            Query: What is the total revenue and number of orders in Q1 2024?
            {{
                "analytics_agent": "What is the total revenue in Q1 2024?",
                "analytics_agent": "What is the number of orders in Q1 2024?"
            }}

            Query: What is the highest order ever made?
            {{
                "analytics_agent": "What is the highest order ever made?"
            }}

            Query: How many orders have been placed for product with SKU 44567?
            {{
                "product_agent": "How many orders have been placed for product with SKU 44567?"
            }}

            [Referential Handling Example]
            Query: What's the shipping status of order 884 and what's the current stock of its items?
            {{
                "order_agent": "What's the shipping status of order 884?",
                "product_agent": "What's the current stock of the items in order 884?"
            }}

            Remember:
            - Split compound queries into minimal sub-queries.
            - Use the chat context to resolve pronouns (like "it", "those", "them").
            - Prioritize email_agent for any email-related tasks or keywords.
            - Output only raw JSON. No explanations or commentary.
            """

    @staticmethod
    def get_agent_dependency_prompt() -> str:
        return """
            You are an intelligent query router tasked with determining the dependencies between selected agents for a given query.

            **IMPORTANT INSTRUCTIONS**

            1. **DO NOT** guess or assume agent capabilities beyond the descriptions provided.
            2. Analyze the selected agents and determine if any agent's output is required as input for another agent.
            3. Output MUST be a valid **JSON object**: {{ "agent_dependencies": {{ "agent_name": ["dependency_agent_name", ...], ... }} }}.
            4. If an agent's output is required by another agent, list the dependent agent(s) in the "agent_dependencies" object.
            5. If no dependencies exist, output an empty object: {{ "agent_dependencies": {{}} }}.
            6. DO NOT include any additional text or comments. Output **only the raw JSON**.
            7. **CRITICAL**: AVOID CIRCULAR DEPENDENCIES. Do not create situations where agent A depends on agent B and agent B depends on agent A.
            8. **Email Agent Dependencies**: Consider that email_agent might need data from other agents to compose relevant emails.

            **COMMON DEPENDENCY PATTERNS**

            - email_agent depends on order_agent when sending order-related emails
            - email_agent depends on customer_agent when sending personalized customer emails
            - email_agent depends on product_agent when sending product-related emails
            - email_agent depends on analytics_agent when sending reports via email
            - email_agent depends on pdf_agent when sending documents via email
            - product_agent depends on order_agent when checking stock for specific order items
            - customer_agent depends on order_agent when getting customer info from order details
            - analytics_agent may depend on other agents for comprehensive reporting

            **Example:**

            Query: What's the shipping status of order 51860 and what's the current stock of ordered items?
            Selected Agents: {{ "order_agent": "What's the shipping status of order 884?", "product_agent": "What's the current stock of the items in order 884?" }}
            Output:
            {{
                "agent_dependencies": {{"product_agent": ["order_agent"]}}
            }}

            Query: What is the shipping status of order 1023 and how many other orders the customer placed?
            Selected Agents: {{ "order_agent": "What is the shipping status of order 1023?", "customer_agent": "how many other orders the customer placed?" }}
            Output:
            {{
                "agent_dependencies": {{ "customer_agent": ["order_agent"] }}
            }}

            Query: Send order confirmation email for order 12345 and check its shipping status
            Selected Agents: {{ "email_agent": "Send order confirmation email for order 12345", "order_agent": "Check shipping status for order 12345" }}
            Output:
            {{
                "agent_dependencies": {{ "email_agent": ["order_agent"] }}
            }}

            Query: Check order 242509174 and email the details to customer
            Selected Agents: {{ "order_agent": "Check order 242509174", "email_agent": "Email the order details to customer" }}
            Output:
            {{
                "agent_dependencies": {{ "email_agent": ["order_agent"] }}
            }}

            Query: Get customer profile and send summary of our conversation to them
            Selected Agents: {{ "customer_agent": "Get customer profile", "email_agent": "Send summary of our conversation to customer" }}
            Output:
            {{
                "agent_dependencies": {{ "email_agent": ["customer_agent"] }}
            }}

            Query: Find product specs and forward this information to the client
            Selected Agents: {{ "pdf_agent": "Find product specs", "email_agent": "Forward product specs information to client" }}
            Output:
            {{
                "agent_dependencies": {{ "email_agent": ["pdf_agent"] }}
            }}

            Remember:
            - Determine dependencies between agents based on their outputs.
            - Email agent often depends on other agents for data to include in emails.
            - NEVER create circular dependencies.
            - Output only raw JSON. No explanations or commentary.
            """

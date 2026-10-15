import os
import json
import logging
from typing import Any, Dict
from qdrant_client import QdrantClient
from ..state.agent_state import AgentState
from langchain_qdrant import QdrantVectorStore
from langchain.schema import HumanMessage, SystemMessage
from ..utils.llm_utils import LLMConfig, create_system_prompt
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

QDRANT_HOST = os.environ.get("QDRANT_HOST", "")
QDRANT_PORT = os.environ.get("QDRANT_PORT", "")


class CustomerAgent:
    """Agent specialized in handling customer-related queries."""

    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()
        self.system_prompt = create_system_prompt("customer")
        self.qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.collection_name = "customer_data"
        self.model = llm_config.get_embedding_model()
        self.vector_store = QdrantVectorStore(
            client=self.qdrant,
            collection_name=self.collection_name,
            embedding=self.model,
        )
        self.metadata_extractor = CustomerMetadataFilterExtractor(llm_config)

    async def process_query(self, query: str, state: AgentState) -> Dict[str, Any]:

        # Check if this agent depends on other agents
        dependencies = state.get("agent_dependencies", {}).get("customer_agent", [])
        dependency_context = ""

        # If we have dependencies, extract relevant information from their outputs
        if dependencies:
            dependency_context = "Information from dependent agents:\n\n"
            for dep in dependencies:
                if dep in state["agent_outputs"]:
                    dependency_context += f"--- {dep.upper()} OUTPUT ---\n"
                    dependency_context += state["agent_outputs"][dep] + "\n\n"

        # Combine the original query with dependency context
        enhanced_query = query
        if dependency_context:
            enhanced_query = (
                f"{query}\n\nContext from other agents:\n{dependency_context}"
            )

        language = state["language"]

        filters = self.metadata_extractor.extract_customer_metadata_filters(
            enhanced_query
        )
        state["metadata"]["customer_filters"] = filters
        print(f"[DEBUG] Extracted filters: {filters}")

        search_results = []
        try:
            if filters:
                for filter_obj in filters:
                    customer_id = filter_obj.get("customer_id")
                    customer_email = filter_obj.get("customer_email")
                    doc_type = filter_obj.get("type")

                    filter_conditions = []
                    if customer_id:
                        filter_conditions.append(
                            FieldCondition(
                                key="metadata.customer_id",
                                match=MatchValue(value=customer_id),
                            )
                        )
                    if customer_email:
                        filter_conditions.append(
                            FieldCondition(
                                key="metadata.customer_email",
                                match=MatchValue(value=customer_email),
                            )
                        )
                    if doc_type:
                        filter_conditions.append(
                            FieldCondition(
                                key="metadata.type",
                                match=MatchValue(value=doc_type),
                            )
                        )

                    query_filter = Filter(must=filter_conditions)

                    filtered_results = self.vector_store.similarity_search(
                        query=enhanced_query,
                        k=10,
                        filter=query_filter,
                    )
                    search_results.extend(filtered_results)
            else:
                search_results = self.vector_store.similarity_search_by_vector(
                    embedding=self._embed_query(enhanced_query),
                    k=10,
                )

            print(f"[DEBUG] Found {len(search_results)} search results")
        except Exception as e:
            print("[ERROR] Vector Search Failed")
            print(e)

        context = self._prepare_context(search_results)

        if language == "nl":
            messages = [
                SystemMessage(
                    content=self.system_prompt
                    + "\nBeantwoord alle vragen in het Nederlands."
                ),
                HumanMessage(content=f"Context: {context}\n\nQuery: {enhanced_query}"),
            ]
        else:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"Context: {context}\n\nQuery: {enhanced_query}"),
            ]

        response = self.llm.invoke(messages)
        return {
            "response": response.content,
        }

    def _embed_query(self, query: str) -> list[float]:
        """Convert query to vector embedding."""
        embedding = self.model.embed_query(query)
        return embedding

    def _prepare_context(self, search_results: list) -> str:
        """Prepare context from vector search results."""
        context_items = []
        for result in search_results:
            context_items.append(result.page_content)
        return "\n".join(context_items)

    async def run(self, state: AgentState) -> AgentState:
        """Run the customer agent and update the state."""
        query = state["agent_queries"].get("customer_agent", state["query"])
        results = {}
        if isinstance(query, list):
            for q in query:
                result = await self.process_query(q, state)
                results[q] = result["response"]
        else:
            result = await self.process_query(query, state)
            results[query] = result["response"]

        state["agent_outputs"]["customer_agent"] = json.dumps(results)
        return state


class CustomerMetadataFilterExtractor:

    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()

    def extract_customer_metadata_filters(self, user_query: str):
        """
        Uses an LLM to extract metadata filters for customer documents based on the user query.
        The filters will be used to identify document types such as 'profile', 'orders', etc.

        Returns a list of metadata filters, each being a dict with keys like:
        - "customer_id"
        - "customer_email"
        - "type"
        """

        few_shot_examples = """
        Examples:

        Query: "What is the profile information for customer with ID 123?"
        Output: [{"customer_id": "123", "type": "customer_profile"}]

        Query: "Show me the order history for john.doe@example.com"
        Output: [{"customer_email": "john.doe@example.com", "type": "customer_orders"}]

        Query: "What addresses does customer 456 have on file?"
        Output: [{"customer_id": "456", "type": "customer_addresses"}]

        Query: "Show me the invoices for customer jane.smith@example.com"
        Output: [{"customer_email": "jane.smith@example.com", "type": "customer_invoices"}]

        Query: "What's in the shopping cart for customer ID 789?"
        Output: [{"customer_id": "789", "type": "customer_cart"}]

        Query: "What is the customer information for DGE customer with ID 471?"
        Output: [{"customer_id": "471", "type": "dge_customer", "source": "dge"}]

        Query: "Give me all information about customer with email alice@example.com"
        Output: [{"customer_email": "alice@example.com", "type": "customer_profile"}, {"customer_email": "alice@example.com", "type": "customer_orders"}, {"customer_email": "alice@example.com", "type": "customer_addresses"}]
        """

        system_prompt = f"""
        You are an intelligent assistant responsible for extracting structured metadata from user queries related to customer data.
        Based on the user query, output a list of metadata filters in JSON format.

        Only use these valid `type` values:
        - "customer_profile"
        - "customer_addresses"
        - "customer_orders"
        - "customer_invoices"
        - "customer_cart"
        - "dge_customer"

        Rules:
        - Extract `customer_id` or `customer_email` from the query if mentioned.
        - If multiple customer identifiers are mentioned, return multiple filter objects.
        - If no customer identifier is found, return an empty list.
        - Only return filters relevant to the query — no assumptions.
        - Only return valid JSON. No explanations or surrounding text.

        {few_shot_examples}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f'Query: "{user_query}"\nOutput:'),
        ]

        try:
            response = self.llm.invoke(messages).content.strip()

            if not response.startswith("["):
                logging.error(f"Expected list format but got: {response}")
                return None

            filters = json.loads(response)

            if not isinstance(filters, list):
                logging.warning(f"Unexpected format: {filters}")
                return None

            valid_types = {
                "customer_profile",
                "customer_addresses",
                "customer_orders",
                "customer_invoices",
                "customer_cart",
                "dge_customer",
            }

            return [
                f
                for f in filters
                if isinstance(f, dict)
                and ("customer_id" in f or "customer_email" in f)
                and "type" in f
                and f["type"] in valid_types
            ]

        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding failed: {e} | Response: {response}")
            return None
        except Exception as e:
            logging.error(f"Error extracting customer metadata filters: {e}")
            return None

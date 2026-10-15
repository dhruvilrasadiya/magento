import os
import json
import logging
from typing import Any, Dict, List
from qdrant_client import QdrantClient
from ..state.agent_state import AgentState
from langchain_qdrant import QdrantVectorStore
from langchain.schema import HumanMessage, SystemMessage
from ..utils.llm_utils import LLMConfig, create_system_prompt
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

QDRANT_HOST = os.environ.get("QDRANT_HOST", "")
QDRANT_PORT = os.environ.get("QDRANT_PORT", "")


class AnalyticsAgent:
    """Agent specialized in handling analytics and business intelligence queries."""

    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()
        self.system_prompt = create_system_prompt("analytics")
        self.qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.collection_name = "analysis_data"
        self.model = llm_config.get_embedding_model()
        self.vector_store = QdrantVectorStore(
            client=self.qdrant,
            collection_name=self.collection_name,
            embedding=self.model,
        )
        self.metadata_extractor = AnalyticsMetadataFilterExtractor(llm_config)

    async def process_query(self, query: str, state: AgentState) -> Dict[str, Any]:
        """Process an analytics-related query using vector search and LLM."""
        print(f"[INFO] AnalyticsAgent: Processing query")
        language = state["language"]
        print(f"[INFO] AnalyticsAgent: Language is {language}")

        dependencies = state.get("agent_dependencies", {}).get("analytics_agent", [])
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

        language = state.get("language", "en-US")

        filters = self.metadata_extractor.extract_analytics_metadata_filters(
            enhanced_query
        )
        state["metadata"]["analytics_filters"] = filters
        print(f"[DEBUG] Extracted filters: {filters}")

        # Pull document UUIDs from existing metadata state
        search_results = []

        if filters:
            for f in filters:
                insight_type = f.get("insight_type")
                print(f"[INFO] AnalyticsAgent: Insight type is {insight_type}")
                if not insight_type:
                    continue
                try:

                    query_filter = Filter(
                        must=[
                            FieldCondition(
                                key="metadata.insight_type",
                                match=MatchValue(value=insight_type),
                            )
                        ]
                    )
                    print(f"[INFO] AnalyticsAgent: Query filter is {query_filter}")
                    results = self.vector_store.similarity_search(
                        query=enhanced_query,
                        k=6,
                        filter=query_filter,
                    )
                    print(f"[INFO] AnalyticsAgent: Found {len(results)} results")
                    search_results.extend(results)
                except Exception as e:
                    print(
                        f"[ERROR] Vector search failed for UUID: {insight_type} | Error: {e}"
                    )

        context = self._prepare_context(search_results)
        print(f"[DEBUG] Extracted context: {context}")

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
        print("[LLM] Analytics Agent Response ---> \n", response)

        return {"response": response.content}

    def _prepare_context(self, search_results: list) -> str:
        """Prepare context from vector search results."""
        context_items = [r.page_content for r in search_results]
        return "\n".join(context_items)

    async def run(self, state: AgentState) -> AgentState:
        """Run the analytics agent and update the state."""
        print("-----" * 20)
        print(f"[START] Analytics Agent")

        query = state["agent_queries"].get("analytics_agent", state["query"])
        results = {}
        if isinstance(query, list):
            for q in query:
                result = await self.process_query(q, state)
                results[q] = result["response"]
        else:
            result = await self.process_query(query, state)
            results[query] = result["response"]

        state["agent_outputs"]["analytics_agent"] = json.dumps(results)
        print(f"[END] Analytics Agent")
        print("-----" * 20)
        return state


class AnalyticsMetadataFilterExtractor:
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()

    def extract_analytics_metadata_filters(self, user_query: str):
        """
        Extract structured metadata filters for analytics queries.
        Output is a list of filters with `insight_type` (e.g., "revenue", "customer", etc.)
        """

        few_shot_examples = """
        Query: "How has our revenue changed over time?"
        Output: [{"insight_type": "order_insights"}]

        Query: "What is the most ordered product?"
        Output: [{"insight_type": "order_insights"}]

        Query: "who has placed Highest number of orders ?"
        Output: [{"insight_type": "order_insights"}]

        Query: "total products?"
        Output: [{"insight_type": "product_insights"}]

        Query: "total order by customer ?" 
        Output: [{"insight_type": "customer_insights"}] (Due to this "2. Customer Analysis" section order_insights)
        """

        system_prompt = f"""
        You are an assistant that extracts the correct analytics `insight_type` based on the user query.
        Match user intent to the most relevant document category.

        Valid `insight_type` values:
        - "order_insights"
        - "customer_insights"
        - "product_insights"

        while each insight_type has subtypes, based on that take desision that query is related to which section and return that associated insight_type.

        "order_insights" has subtypes like 
            - "1. Sales & Revenue Analytics"
            - "2. Customer Analysis"
            - "3. Product & Inventory Insights"
            - "4. Order Status and Processing"
            - "5. Shipping and Fulfillment"
            - "6. Time-based Order and Revenue Breakdown"
        "customer_insights" has subtypes like "customer_profile"
        "product_insights" has subtypes like "Product & Inventory Insights"

        [EXCEPTION] for best selling product return "order_insights" or any such related queries.
        Return a list of JSON objects, each with one key: "insight_type".
        Only include valid values — no free text or explanations.
        {few_shot_examples}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f'Query: "{user_query}"\nOutput:'),
        ]

        try:
            response = self.llm.invoke(messages).content.strip()
            if not response.startswith("["):
                logging.error(f"Expected JSON list format, got: {response}")
                return []

            filters = json.loads(response)

            valid_insight_types = {
                "order_insights",
                "customer_insights",
                "product_insights",
            }

            return [
                f
                for f in filters
                if isinstance(f, dict)
                and "insight_type" in f
                and f["insight_type"] in valid_insight_types
            ]

        except Exception as e:
            logging.error(f"[AnalyticsMetadataFilterExtractor] Failed to extract: {e}")
            return []

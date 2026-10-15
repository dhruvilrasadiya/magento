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


class OrderAgent:
    """Agent specialized in handling Magento order-related queries."""

    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()
        self.system_prompt = create_system_prompt("order")
        self.qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.collection_name = "order_data"
        self.model = llm_config.get_embedding_model()
        self.vector_store = QdrantVectorStore(
            client=self.qdrant,
            collection_name=self.collection_name,
            embedding=self.model,
        )
        self.metadata_extractor = OrderMetadataFilterExtractor(llm_config)

    async def process_query(self, query: str, state: AgentState) -> Dict[str, Any]:
        """Process an order-related query."""

        # Check if this agent depends on other agents
        dependencies = state.get("agent_dependencies", {}).get("order_agent", [])
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
        search_results = []

        try:
            # Extract metadata filters
            metadata_filter = self.metadata_extractor.extract_order_metadata_filters(
                enhanced_query
            )
            print(f"[DEBUG] Metadata filter: {metadata_filter}")

            search_results = self.search_order_docs_with_escalating_filters(
                enhanced_query, metadata_filter, self.vector_store, self._embed_query
            )

            print(len(search_results))
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
        print("[LLM] Order Agent Response ---> \n", response)
        return {
            "response": response.content,
        }

    def _print_vector_data(self):
        points, next_page = self.qdrant.scroll(
            collection_name="order_data",
            limit=5,
            with_payload=True,
            with_vectors=False,  # Set True if you want the vectors too
        )
        # Print payloads (metadata)
        for p in points:
            print(p.id, p.payload)

    def _embed_query(self, query: str) -> list[float]:
        """Convert query to vector embedding."""

        embedding = self.model.embed_query(query)
        return embedding

    def _prepare_context(self, search_results: list) -> str:
        """Prepare context from vector search results."""

        context_items = []
        for result in search_results:
            context_items.append(
                f"{result.page_content} with items_skus {result.metadata.get('item_skus', [])}"
            )
        return "\n".join(context_items)

    async def run(self, state: AgentState) -> AgentState:
        """Run the order agent and update the state."""

        print("-----" * 20)
        print(f"[START] Order Agent")
        print(self.qdrant.count(collection_name="order_data", exact=True))
        # self._print_vector_data()
        query = state["agent_queries"].get("order_agent", state["query"])

        results = {}
        if isinstance(query, list):
            for q in query:
                result = await self.process_query(q, state)
                results[q] = result["response"]
        else:
            result = await self.process_query(query, state)
            results[query] = result["response"]

        state["agent_outputs"]["order_agent"] = json.dumps(results)
        print(f"[END] Order Agent")
        print("-----" * 20)
        return state

    def search_order_docs_with_escalating_filters(
        self, enhanced_query, metadata_filter, vector_store, embed_query_fn
    ):
        """
        Performs a similarity search for order documents with escalating metadata filters.

        Args:
            enhanced_query (str): The processed user query.
            metadata_filter (List[Dict]): Extracted metadata filters.
            vector_store: The vector store instance with similarity search methods.
            embed_query_fn (Callable): Function to embed the query into a vector.

        Returns:
            List: Search results from the vector store.
        """

        def build_filter(filters_subset):
            filter_conditions = []
            for filter_obj in filters_subset:
                for key, value in filter_obj.items():
                    if isinstance(value, list):
                        for v in value:
                            filter_conditions.append(
                                FieldCondition(
                                    key=f"metadata.{key}",
                                    match=MatchValue(value=v),
                                )
                            )
                    else:
                        filter_conditions.append(
                            FieldCondition(
                                key=f"metadata.{key}",
                                match=MatchValue(value=value),
                            )
                        )
            return Filter(must=filter_conditions) if filter_conditions else None

        print(f"[DEBUG] Metadata filter: {metadata_filter}")
        search_results = []

        if metadata_filter:
            # Define filter priority (high to low)
            filter_priority = [
                "order_id",
                "type",
                "source",
                "customer_firstname",
                "customer_lastname",
            ]

            # Merge all metadata filter dicts into one
            combined_filter = {}
            for item in metadata_filter:
                combined_filter.update(item)

            # Try filtering by progressively removing lowest priority filters
            for i in range(len(filter_priority)):
                # Build subset by keeping only top-N priority filters
                filtered_subset = [
                    {k: combined_filter[k]}
                    for k in filter_priority[: len(filter_priority) - i]
                    if k in combined_filter
                ]
                if not filtered_subset:
                    continue

                query_filter = build_filter(filtered_subset)
                print(f"[DEBUG] Trying with filters: {filtered_subset}")

                filtered_results = vector_store.similarity_search(
                    query=enhanced_query,
                    k=20,
                    filter=query_filter,
                )

                if filtered_results:
                    print(
                        f"[DEBUG] Found {len(filtered_results)} results with filters: {filtered_subset}"
                    )
                    return filtered_results  # Early return on success
                else:
                    print(f"[DEBUG] No results with filters: {filtered_subset}")

        # Fallback: no filters
        print(
            "[DEBUG] No results from metadata filtering, performing vector search without filters"
        )
        return vector_store.similarity_search_by_vector(
            embedding=embed_query_fn(enhanced_query),
            k=18,
        )


class OrderMetadataFilterExtractor:

    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()

    def extract_order_metadata_filters(
        self, user_query: str, order_ids: list[int] = None
    ):
        """
        Uses an LLM to extract metadata filters for order documents based on the user query.
        The filters will be used to identify document types such as 'shipping', 'payment', etc.

        Returns a list of metadata filters, each being a dict with keys like:
        - "customer_name"
        - "order_id"
        - "type"
        """

        few_shot_examples = """
        Examples:

        Query: "What is the status of order 28?"
        Output: [{"order_id": 28, "type": "status_history"}]

        Query: "Show me the shipping details of order 15"
        Output: [{"order_id": 15, "type": "shipping"}]

        Query: "What items were included in order 43?"
        Output: [{"order_id": 43, "type": "item"}]

        Query: "Give me the billing address for order 32"
        Output: [{"order_id": 32, "type": "billing_address"}]

        Query: "What is the payment information for dge order 242512323"
        Output: [{"order_id": 242512323, "source": "dge", "type": "dge_sales_order_summary"}, 
        {"order_id": 242512323, "source": "dge", "type": "dge_backorder_summary"}]

        Query: "Tell me about the payment info for order 50"
        Output: [{"order_id": 50, "type": "payment"}]

        Query: "Summarize order 8"
        Output: [{"order_id": 8, "type": "order_summary"}]

        Query: "Give me the order ID and details for the order placed by John Doe"
        Output: [{"customer_firstname": "John", "customer_lastname": "Doe", "type": "order_summary"}]
        """

        system_prompt = f"""
        You are an intelligent assistant responsible for extracting structured metadata from user queries related to order data.
        Based on the user query, output a list of metadata filters in JSON format.

        Only use these valid `type` values:
        - "status_history"
        - "dge_sales_order_summary"
        - "dge_backorder_summary"
        - "shipping"
        - "payment"
        - "billing_address"
        - "item"
        - "order_summary"

        Rules:
        - Avoid assigning unnecessary units to values retrieved from the context.
        - Extract `order_id` from the query if mentioned.
        - If multiple order_ids are mentioned, return multiple filter objects.
        - If no `order_id` is found, skip that query.
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
                "status_history",
                "shipping",
                "payment",
                "billing_address",
                "item",
                "order_summary",
                "dge_sales_order_summary",
                "dge_backorder_summary",
            }

            return [
                f
                for f in filters
                if isinstance(f, dict)
                and ("order_id" in f or "customer_name" in f)
                and "type" in f
                and f["type"] in valid_types
            ]

        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding failed: {e} | Response: {response}")
            return None

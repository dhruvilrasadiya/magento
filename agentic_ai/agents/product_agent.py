import json
import os
import re
import logging
from typing import Dict, List, Any, Callable, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
from langchain_qdrant import QdrantVectorStore

QDRANT_HOST = os.environ.get("QDRANT_HOST", "")
QDRANT_PORT = os.environ.get("QDRANT_PORT", "")


class ProductAgent:
    """Agent specialized in handling product-related queries with enhanced DGE/Magento data support."""

    def __init__(self, llm_config):
        self.llm = llm_config.get_llm()
        self.system_prompt = create_system_prompt("product")
        self.qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.model = llm_config.get_embedding_model()
        self.collection_name = "product_data"
        self.vector_store = QdrantVectorStore(
            client=self.qdrant,
            collection_name=self.collection_name,
            embedding=self.model,
        )
        self.metadata_extractor = ProductMetadataFilterExtractor(llm_config)

    async def process_query(self, query: str, state) -> Dict[str, Any]:
        """Process a product-related query with enhanced context handling."""

        # Check if this agent depends on other agents
        dependencies = state.get("agent_dependencies", {}).get("product_agent", [])
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

        print(f"[INFO] ProductAgent: Processing query: {enhanced_query}")

        try:
            # Extract metadata filters with enhanced DGE/Magento support
            metadata_filter = self.metadata_extractor.extract_product_metadata_filters(
                enhanced_query
            )
            print(f"[DEBUG] Extracted metadata filter: {metadata_filter}")

            # Enhanced search with better filter escalation
            search_results = self.search_with_escalating_filters(
                enhanced_query, metadata_filter, self.vector_store, self._embed_query
            )

            print(f"[DEBUG] Found {len(search_results)} search results")

            # Log sample results for debugging
            if search_results:
                print(f"[DEBUG] Sample result metadata: {search_results[0].metadata}")

        except Exception as e:
            print(f"[ERROR] Vector Search Failed: {e}")
            import traceback

            traceback.print_exc()

        context = self._prepare_context(search_results)

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Context: {context}\n\nQuery: {enhanced_query}"),
        ]

        response = self.llm.invoke(messages)
        print(f"[LLM] Product Agent Response:\n{response.content}")

        return {
            "response": response.content,
            "search_results_count": len(search_results),
            "metadata_filters_used": metadata_filter,
        }

    def _embed_query(self, query: str) -> List[float]:
        """Convert query to vector embedding."""
        return self.model.embed_query(query)

    def _prepare_context(self, search_results: List) -> str:
        """Prepare context from vector search results with enhanced formatting."""
        if not search_results:
            return "No relevant product information found."

        print("----" * 30)
        print("Search Results:")
        for i, result in enumerate(search_results[:3]):  # Log first 3 results
            print(
                f"Result {i+1}: {result.metadata.get('type', 'unknown')} - {result.metadata.get('source', 'unknown')}"
            )
        print("----" * 30)

        # Group results by source for better organization
        context_parts = []
        dge_results = []
        magento_results = []
        merged_results = []

        for result in search_results:
            source = result.metadata.get("source", "unknown")
            if source == "dge" or source == "dge_index":
                dge_results.append(result)
            elif source == "magento":
                magento_results.append(result)
            elif source == "merged":
                merged_results.append(result)
            else:
                context_parts.append(result.page_content)

        # Add organized sections
        if merged_results:
            context_parts.append("=== MERGED PRODUCT DATA ===")
            context_parts.extend([r.page_content for r in merged_results[:5]])

        if dge_results:
            context_parts.append("=== DGE PRODUCT DATA ===")
            context_parts.extend([r.page_content for r in dge_results[:5]])

        if magento_results:
            context_parts.append("=== MAGENTO PRODUCT DATA ===")
            context_parts.extend([r.page_content for r in magento_results[:5]])

        context = "\n\n".join(context_parts)

        # Enhanced image URL processing
        staging_url = os.getenv("MAGENTO_API_URL", "")
        if staging_url:
            # Replace relative paths with full URLs
            def replacer(match):
                path = match.group(1)
                return path

            context = re.sub(
                r"(?<!http)(/[\w/-]+\.(?:jpg|jpeg|png|webp|gif))",
                replacer,
                context,
                flags=re.IGNORECASE,
            )

            # Deduplicate images
            context = self._deduplicate_images(context)

        return context

    def _deduplicate_images(self, context: str) -> str:
        """Remove duplicate image references from context."""
        seen_urls = set()

        # Remove duplicate Markdown images
        def dedup_markdown_images(match):
            alt = match.group(1)
            url = match.group(2)
            if url in seen_urls:
                return ""
            seen_urls.add(url)
            return f"![{alt}]({url})"

        context = re.sub(
            r"!\[([^\]]*)\]\((https?://[^\)]+)\)", dedup_markdown_images, context
        )

        # Remove duplicate HTML <img> tags
        def dedup_html_images(match):
            url = match.group(1)
            if url in seen_urls:
                return ""
            seen_urls.add(url)
            return f'<img src="{url}" style="width:189px; height:189px; object-fit:contain;" />'

        context = re.sub(r'<img\s+[^>]*src="([^"]+)"[^>]*>', dedup_html_images, context)

        return context

    async def run(self, state) -> dict:
        print("-----" * 20)
        print(f"[START] Product Agent")

        query = state["agent_queries"].get("product_agent", state["query"])
        results = {}

        if isinstance(query, list):
            for q in query:
                result = await self.process_query(q, state)
                response = result["response"]
                if isinstance(response, str):
                    response = (
                        self.metadata_extractor.replace_website_ids_with_store_names(
                            response
                        )
                    )
                results[q] = response
        else:
            result = await self.process_query(query, state)
            response = result["response"]
            if isinstance(response, str):
                response = self.metadata_extractor.replace_website_ids_with_store_names(
                    response
                )
            results[query] = response

        state["agent_outputs"]["product_agent"] = json.dumps(results)

        print(f"[END] Product Agent")
        print("-----" * 20)
        return state

    def search_with_escalating_filters(
        self,
        enhanced_query: str,
        metadata_filter: List[Dict],
        vector_store,
        embed_query_fn: Callable,
    ) -> List:
        """
        Enhanced similarity search with escalating metadata filters for DGE/Magento data.
        """

        def build_filter(filters_subset: List[Dict]) -> Optional[Filter]:
            """Build Qdrant filter from metadata filters."""
            filter_conditions = []

            for filter_obj in filters_subset:
                for key, value in filter_obj.items():
                    if key == "type":
                        # Handle document type filtering
                        filter_conditions.append(
                            FieldCondition(
                                key=f"metadata.{key}",
                                match=MatchValue(value=value),
                            )
                        )
                    elif key in ["sku", "dge_id", "productcode"]:
                        # Handle product identifier filtering
                        if isinstance(value, list):
                            filter_conditions.append(
                                FieldCondition(
                                    key=f"metadata.{key}",
                                    match=MatchAny(any=value),
                                )
                            )
                        else:
                            # Try both string and integer representations
                            match = MatchValue(value=value)
                            filter_conditions.append(
                                FieldCondition(
                                    key=f"metadata.{key}",
                                    match=match,
                                )
                            )
                    elif key == "source":
                        # Handle source filtering (dge, magento, merged)
                        filter_conditions.append(
                            FieldCondition(
                                key=f"metadata.{key}",
                                match=MatchValue(value=value),
                            )
                        )
                    elif key == "website_id":
                        # Handle website ID filtering
                        filter_conditions.append(
                            FieldCondition(
                                key=f"metadata.{key}",
                                match=MatchValue(value=int(value)),
                            )
                        )
                    elif key == "name":
                        # Handle name filtering with partial matching
                        filter_conditions.append(
                            FieldCondition(
                                key=f"metadata.{key}",
                                match=MatchValue(value=value),
                            )
                        )
                    else:
                        # Handle other metadata fields
                        if isinstance(value, list):
                            filter_conditions.append(
                                FieldCondition(
                                    key=f"metadata.{key}",
                                    match=MatchAny(any=value),
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

        print(f"[DEBUG] Starting search with metadata filters: {metadata_filter}")

        search_results = []

        if metadata_filter:
            # Enhanced filter priority for DGE/Magento data
            filter_priority = [
                "dge_id",  # DGE product ID
                "sku",  # Magento SKU
                "name",  # Product name
                "type",  # document type (description, pricing, etc.)
                "source",  # dge, magento, merged
                "productcode",  # DGE product code
                "website_id",  # Store/website identifier
                "category",  # Product category
                "brand",  # Product brand
            ]

            # Merge all metadata filter dicts into one
            combined_filter = {}
            for item in metadata_filter:
                combined_filter.update(item)

            print(f"[DEBUG] Combined filter: {combined_filter}")

            # Try filtering by progressively removing lowest priority filters
            for i in range(len(filter_priority) + 1):
                if i == 0:
                    # First try: Use all available filters
                    filtered_subset = [combined_filter]
                else:
                    # Progressive removal: Keep only top-priority filters
                    remaining_keys = filter_priority[: len(filter_priority) - i + 1]
                    filtered_subset = [
                        {k: combined_filter[k]}
                        for k in remaining_keys
                        if k in combined_filter
                    ]

                if not filtered_subset or not any(filtered_subset):
                    continue

                try:
                    query_filter = build_filter(filtered_subset)
                    print(f"[DEBUG] Trying search with filters: {filtered_subset}")

                    if query_filter:
                        filtered_results = vector_store.similarity_search(
                            query=enhanced_query,
                            k=25,  # Increased for better coverage
                            filter=query_filter,
                        )
                    else:
                        filtered_results = []

                    if filtered_results:
                        print(
                            f"[DEBUG] Found {len(filtered_results)} results with filters: {filtered_subset}"
                        )
                        return filtered_results[:20]  # Return top 20 results
                    else:
                        print(f"[DEBUG] No results with filters: {filtered_subset}")

                except Exception as e:
                    print(f"[DEBUG] Filter search failed: {e}")
                    continue

        # Fallback: Vector search without filters
        print(
            "[DEBUG] No results from metadata filtering, performing vector search without filters"
        )
        try:
            fallback_results = vector_store.similarity_search_by_vector(
                embedding=embed_query_fn(enhanced_query),
                k=20,
            )
            print(f"[DEBUG] Fallback search returned {len(fallback_results)} results")
            return fallback_results
        except Exception as e:
            print(f"[ERROR] Fallback search failed: {e}")
            return []


class ProductMetadataFilterExtractor:
    """Enhanced metadata filter extractor for DGE/Magento product data."""

    def __init__(self, llm_config):
        self.llm = llm_config.get_llm()

        # Enhanced store mapping
        self.store_map = {
            "terrasheater": 1,
            "gereedschapskist": 2,
            "heaterdirect": 3,
            "cilinders": 9,
        }

        # Inverted mapping for replacement (website_id → store_name)
        self.website_id_to_store_name = {v: k for k, v in self.store_map.items()}

    def replace_website_ids_with_store_names(self, text: str) -> str:
        """Replace website IDs with store names in the text."""
        id_to_store = {
            str(wid): store_name for store_name, wid in self.store_map.items()
        }

        for website_id, store_name in id_to_store.items():
            patterns = [
                f"website ID {website_id}",
                f"website ID: {website_id}",
                f"Website ID {website_id}",
                f"Website ID: {website_id}",
                f"website_id {website_id}",
                f"store {website_id}",
            ]

            for pattern in patterns:
                text = text.replace(pattern, f"from {store_name}")

        return text

    def extract_product_metadata_filters(self, user_query: str) -> List[Dict[str, Any]]:
        """
        Enhanced metadata extraction for DGE/Magento integrated product data.
        """

        store_website_mapping = """
        Store Name to website_id mapping:
        - 1 → "terrasheater"
        - 2 → "gereedschapskist" 
        - 3 → "heaterdirect"
        - 9 → "cilinders"
        """

        enhanced_examples = """
        Enhanced Examples for DGE/Magento Integration:

        Query: "Show me the description of product with SKU 10232"
        Output: [{"sku": "10232", "type": "description"}]

        Query: "What is the DGE ID for product 12345?"
        Output: [{"sku": "12345", "type": "merged", "source": "merged"}]

        Query: "Give me pricing details from DGE for product 10105"
        Output: [{"dge_id": "10105", "type": "dge_price", "source": "dge"}]

        Query: "Show me the Magento description for Nike Air Zoom"
        Output: [{"name": "Nike Air Zoom", "type": "description", "source": "magento"}]

        Query: "What is available in DGE for productcode 10110?"
        Output: [{"productcode": "10110", "source": "dge"}]

        Query: "Find the merged data for SKU 44567"
        Output: [{"sku": "44567", "type": "merged", "source": "merged"}]

        Query: "Is Eurom Golden 2000 available in DGE?"
        Output: [{"name": "Eurom Golden 2000", "source": "dge"}]

        Query: "Show me DGE basic info for product 10015"
        Output: [{"dge_id": "10015", "type": "basic", "source": "dge"}]

        Query: "What is the logistics info for productcode 10022?"
        Output: [{"productcode": "10022", "type": "logistics", "source": "dge"}]

        Query: "Give me the unit details from DGE for product 10012"
        Output: [{"dge_id": "10012", "type": "unit", "source": "dge"}]

        Query: "Show me all merged products with EAN 8720174265709"
        Output: [{"ean": "8720174265709", "source": "merged"}]

        Query: "Find manufacturer code NUKI BRIDGE in DGE"
        Output: [{"manufacturer_code": "NUKI BRIDGE", "source": "dge"}]

        Query: "What Magento products are linked to DGE supplier 157544?"
        Output: [{"supplier_id": "157544", "source": "merged"}]

        Query: "Show me the index data for D4E GEREEDSCHAPSGORDEL"
        Output: [{"name": "D4E GEREEDSCHAPSGORDEL", "type": "index_product", "source": "dge_index"}]
        """

        enhanced_system_prompt = f"""
        You are an intelligent assistant for extracting metadata filters from product queries in a DGE/Magento integrated system.
        
        IMPORTANT DATA STRUCTURE:
        - If nothing is provide with value, consider it sku and dge_id both and try to fetch data from both the sources.
        - DGE products: Original supplier data with fields like productcode, basic info, unit, price, logistics
        - Magento products: E-commerce data with SKU, name, description, pricing, categories
        - Merged products: Combined DGE/Magento data linking both systems
        - Index products: DGE index entries with metadata like EAN, manufacturer codes, supplier info

        SOURCE TYPES:
        - "dge": Pure DGE data
        - "magento": Pure Magento data  
        - "merged": Combined DGE/Magento data
        - "dge_index": DGE index entries

        DOCUMENT TYPES:
        DGE: "basic", "unit", "price", "logistics", "index_product", "full_product"
        Magento: "name", "description", "pricing", "brand", "category", "summary"
        Merged: "merged"

        KEY FIELDS:
        - sku: Magento SKU (string)
        - dge_id: DGE product ID (string)  
        - productcode: DGE product code (int)
        - name: Product name
        - ean: European Article Number
        - manufacturer_code: DGE manufacturer code
        - supplier_code: DGE supplier code
        - supplier_id: DGE supplier ID

        {store_website_mapping}

        RULES:
        1. For DGE queries: Use dge_id/productcode + source="dge"
        2. For Magento queries: Use sku + source="magento"  
        3. For mapping/linking queries: Use source="merged"
        4. For availability checks: Specify appropriate source
        5. Extract specific identifiers (SKU, DGE ID, productcode) when mentioned
        6. Return ONLY valid JSON - no explanations

        {enhanced_examples}
        """

        messages = [
            SystemMessage(content=enhanced_system_prompt),
            HumanMessage(content=f'Query: "{user_query}"\nOutput:'),
        ]

        try:
            response = self.llm.invoke(messages).content.strip()
            print(f"[DEBUG] Raw metadata filter response: {response}")

            # Parse JSON response
            if not isinstance(response, list):
                if "metadata_filters" in response:
                    filters = json.loads(response["metadata_filters"])
                elif isinstance(response, dict):
                    filters = [response]
                else:
                    filters = json.loads(response)
            else:
                filters = response

            print(f"[DEBUG] Parsed metadata filters: {filters}")

            # Enhanced validation for DGE/Magento fields
            valid_types = [
                # DGE types
                "basic",
                "unit",
                "dge_price",
                "logistics",
                "index_product",
                "full_product",
                # Magento types
                "name",
                "description",
                "pricing",
                "brand",
                "category",
                "summary",
                # Merged/common types
                "merged",
                "stock_info",
                "custom_attributes",
                "extension_attributes",
            ]

            valid_sources = ["dge", "magento", "merged", "dge_index"]

            refined = []
            for f in filters:
                if isinstance(f, dict):
                    # Validate and clean filter
                    cleaned_filter = {}

                    for key, value in f.items():
                        if key == "type" and value in valid_types:
                            cleaned_filter[key] = value
                        elif key == "source" and value in valid_sources:
                            cleaned_filter[key] = value
                        elif key in [
                            "sku",
                            "dge_id",
                            "productcode",
                            "name",
                            "ean",
                            "manufacturer_code",
                            "supplier_code",
                            "supplier_id",
                            "website_id",
                            "category",
                            "brand",
                        ]:
                            cleaned_filter[key] = value
                        elif key == "store_name" and value in self.store_map:
                            cleaned_filter[key] = value
                            # Auto-add website_id
                            cleaned_filter["website_id"] = self.store_map[value]

                    if cleaned_filter:
                        refined.append(cleaned_filter)

            print(f"[DEBUG] Refined metadata filters: {refined}")
            return refined

        except Exception as e:
            logging.error(
                f"Metadata filter extraction failed: {e} | Response: {response}"
            )
            return []


def create_system_prompt(agent_type: str) -> str:
    """Create enhanced system prompt for product agent."""
    return f"""
    You are a specialized {agent_type} agent working with an integrated DGE/Magento product database.
    
    DATA SOURCES:
    - DGE: Supplier product data with detailed specifications, logistics, pricing
    - Magento: E-commerce platform data with SKUs, descriptions, categories
    - Merged: Combined data linking DGE and Magento products
    
    CAPABILITIES:
    - Search across all product data sources
    - Link DGE products to Magento SKUs
    - Provide detailed product specifications
    - Check product availability and stock status
    - Compare data between systems
    
    RESPONSE GUIDELINES:
    - Always specify which system(s) the information comes from
    - Provide complete, accurate product information
    - Include relevant identifiers (SKU, DGE ID, productcode)
    - Format responses clearly with proper sections
    - Handle multi-source queries intelligently
    
    Be helpful, accurate, and comprehensive in your responses.
    """

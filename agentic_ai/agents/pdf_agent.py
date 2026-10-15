import os
import json
from typing import Any, Dict
from qdrant_client import QdrantClient
from ..state.agent_state import AgentState
from langchain_qdrant import QdrantVectorStore
from langchain.schema import HumanMessage, SystemMessage
from ..utils.llm_utils import LLMConfig, create_system_prompt


QDRANT_HOST = os.environ.get("QDRANT_HOST", "")
QDRANT_PORT = os.environ.get("QDRANT_PORT", "")


class PDFAgent:
    """Agent specialized in handling queries about PDF documents."""

    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()
        self.model = llm_config.get_embedding_model()
        self.system_prompt = create_system_prompt("pdf")
        self.collection_name = "pdf_data"
        self.qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.vector_store = QdrantVectorStore(
            client=self.qdrant,
            collection_name=self.collection_name,
            embedding=self.model,
        )

    async def process_query(self, query: str, state: AgentState) -> Dict[str, Any]:
        """Process a PDF document query."""

        # Check if this agent depends on other agents
        dependencies = state.get("agent_dependencies", {}).get("pdf_agent", [])
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
            # Perform vector search
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
        print("[LLM] PDF Agent Response ---> \n", response.content)
        return {
            "response": response.content,
        }

    def _prepare_context(self, search_results: list) -> str:
        """Prepare context by combining page contents of matched documents."""
        return "\n".join([doc.page_content for doc in search_results])

    def _embed_query(self, query: str) -> list[float]:
        """Convert query to vector embedding."""
        embedding = self.model.embed_query(query)
        return embedding

    async def run(self, state: AgentState) -> AgentState:
        print("-----" * 20)
        print(f"[START] PDF Agent")
        print(self.qdrant.count(collection_name=self.collection_name, exact=True))

        query = state["agent_queries"].get("pdf_agent", state["query"])
        results = {}
        if isinstance(query, list):
            for q in query:
                result = await self.process_query(q, state)
                results[q] = result["response"]
        else:
            result = await self.process_query(query, state)
            results[query] = result["response"]

        state["agent_outputs"]["pdf_agent"] = json.dumps(results)
        print(f"[END] PDF Agent")
        print("-----" * 20)
        return state

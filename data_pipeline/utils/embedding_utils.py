import os
from typing import Any, Dict, List

import openai
import yaml
from qdrant_client import QdrantClient
from qdrant_client.http import models


class EmbeddingManager:
    """Manages the creation and storage of embeddings."""

    def __init__(self, config_path: str = "configs/qdrant_config.yaml"):
        self.config = self._load_config(config_path)
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._initialize_qdrant_clients()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _initialize_qdrant_clients(self):
        """Initialize Qdrant clients for different data types."""
        self.qdrant_clients = {
            "order": QdrantClient(
                host=self.config["order_qdrant"]["host"],
                port=self.config["order_qdrant"]["port"],
            ),
            "product": QdrantClient(
                host=self.config["product_qdrant"]["host"],
                port=self.config["product_qdrant"]["port"],
            ),
            "pdf": QdrantClient(
                host=self.config["pdf_qdrant"]["host"],
                port=self.config["pdf_qdrant"]["port"],
            ),
            "crm": QdrantClient(
                host=self.config["crm_qdrant"]["host"],
                port=self.config["crm_qdrant"]["port"],
            ),
        }

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts using OpenAI's API."""
        batch_size = self.config["embedding_config"]["batch_size"]
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002", input=batch
            )
            embeddings.extend([e.embedding for e in response.data])

        return embeddings

    def store_embeddings(
        self, data_type: str, texts: List[str], metadata: List[Dict[str, Any]]
    ) -> bool:
        """Store embeddings in the appropriate Qdrant collection."""
        if data_type not in self.qdrant_clients:
            raise ValueError(f"Invalid data type: {data_type}")

        # Create embeddings
        embeddings = self.create_embeddings(texts)

        # Prepare points for Qdrant
        points = []
        for i, (embedding, meta) in enumerate(zip(embeddings, metadata)):
            points.append(models.PointStruct(id=i, vector=embedding, payload=meta))

        # Store in appropriate collection
        client = self.qdrant_clients[data_type]
        collection_name = f"{data_type}_data"

        try:
            # Ensure collection exists
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=self.config[f"{data_type}_qdrant"]["vector_size"],
                    distance=models.Distance.COSINE,
                ),
            )

            # Upload points
            client.upsert(collection_name=collection_name, points=points)
            return True

        except Exception as e:
            print(f"Error storing embeddings: {str(e)}")
            return False

    def search_similar(
        self, data_type: str, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar items in the vector database."""
        if data_type not in self.qdrant_clients:
            raise ValueError(f"Invalid data type: {data_type}")

        # Create query embedding
        query_embedding = self.create_embeddings([query])[0]

        # Search in appropriate collection
        client = self.qdrant_clients[data_type]
        collection_name = f"{data_type}_data"

        try:
            results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
            )
            return [{"score": hit.score, "payload": hit.payload} for hit in results]
        except Exception as e:
            print(f"Error searching embeddings: {str(e)}")
            return []

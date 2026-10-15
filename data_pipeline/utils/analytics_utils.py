import os
import time
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from database.analytics import AnalyticsDocumentLog

embedding_model = OpenAIEmbeddings(
    model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
    openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
)
# Qdrant client for vector DB
QDRANT_HOST = os.environ.get("QDRANT_HOST", "")
QDRANT_PORT = os.environ.get("QDRANT_PORT", "")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def embed_and_upsert_insights(
    docs: list,
    all_doc_log: dict,
    insight_type: str,
    time_id: str,
    batch_size: int = 50,
    collection_name: str = "analytics_data",
):
    """
    Embed and upsert analytics insights documents to Qdrant and MongoDB.

    Parameters:
    - docs: List of Langchain Document objects
    - all_doc_log: Dict of section_name -> list of doc_ids
    - insight_type: Type of insight (e.g., 'order_insights')
    - time_id: ISO timestamp string
    - batch_size: Number of docs to process per Qdrant batch
    - collection_name: Qdrant collection name
    """

    vectorstore = QdrantVectorStore(
        client=qdrant,
        collection_name=collection_name,
        embedding=embedding_model,
    )

    # Step 1: Check if time_id already exists in Mongo
    existing_log = AnalyticsDocumentLog.objects(insights_type=insight_type).first()

    if existing_log:
        # Step 2: Collect all existing UUIDs to delete from Qdrant
        existing_doc_ids = []
        for ids in existing_log.document_ids.values():
            existing_doc_ids.extend(ids)

        if existing_doc_ids:
            try:
                print(f"[INFO] Deleting existing docs for time_id: {time_id}")
                qdrant.delete(
                    collection_name=collection_name,
                    points_selector=existing_doc_ids,
                )
            except Exception as e:
                print(
                    f"[WARNING] Failed to delete old docs from Qdrant for time_id {time_id}: {e}"
                )

    # Step 3: Upsert new log in MongoDB
    AnalyticsDocumentLog.objects(time_id=time_id).update_one(
        set__document_ids=all_doc_log,
        set__insights_type=insight_type,
        upsert=True,
    )
    print(f"[INFO] MongoDB updated for time_id: {time_id}")

    # Step 4: Embed and upsert in batches to Qdrant
    uuids = [doc.metadata["doc_id"] for doc in docs]

    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i : i + batch_size]
        batch_ids = uuids[i : i + batch_size]
        try:
            vectorstore.add_documents(documents=batch_docs, ids=batch_ids)
            print(
                f"[INFO] Upserted batch {i // batch_size + 1}: {len(batch_docs)} docs"
            )
            time.sleep(5)
        except Exception as e:
            print(f"[WARNING] Failed to upsert batch {i // batch_size + 1}: {e}")

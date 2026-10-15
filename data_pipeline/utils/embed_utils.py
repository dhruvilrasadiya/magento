import os
import json
import time
from typing import Dict, List
from qdrant_client import QdrantClient, models  # Added models import
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from database.orders import OrderDocumentLog
from database.products import ProductDocumentLog
from database.customer import CustomerDocumentLog
from database.pdfs import PDFDocumentLog


embedding_model = OpenAIEmbeddings(
    model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
    openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
)
# Qdrant client for vector DB
QDRANT_HOST = os.environ.get("QDRANT_HOST", "")
QDRANT_PORT = os.environ.get("QDRANT_PORT", "")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def embed_and_upsert_orders(docs: list, all_doc_log: dict, batch_size: int = 50):

    vectorstore = QdrantVectorStore(
        client=qdrant,
        collection_name="order_data",
        embedding=embedding_model,
    )
    for order_id, doc_log in all_doc_log.items():
        #  Step 1: Check if order_id already exists
        existing_log = OrderDocumentLog.objects(order_id=order_id).first()

        if existing_log:
            #  Step 2: If yes, collect all existing UUIDs
            existing_doc_ids = []
            for ids in existing_log.document_ids.values():
                existing_doc_ids.extend(ids)

            if existing_doc_ids:
                #  Step 3: Delete existing documents from Qdrant
                try:
                    print({order_id: existing_doc_ids})
                    qdrant.delete(
                        collection_name="order_data",
                        points_selector=existing_doc_ids,
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to delete old documents from Qdrant for order_id {order_id}: {e}"
                    )

        #  Step 4: Now upsert new document_ids in MongoDB
        OrderDocumentLog.objects(order_id=order_id).update_one(
            set__document_ids=doc_log,
            upsert=True,
        )

    uuids = [doc.metadata["doc_id"] for doc in docs]
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i : i + batch_size]
        batch_ids = uuids[i : i + batch_size]
        try:
            vectorstore.add_documents(documents=batch_docs, ids=batch_ids)
            print(
                f"Upserted batch {i // batch_size + 1} successfully: {len(batch_docs)} documents"
            )
            time.sleep(5)
        except Exception as e:
            print(f"Warning: Failed to upsert batch {i // batch_size + 1}: {e}")

    return True


def embed_and_upsert_products(
    docs: list,
    all_doc_log: dict,
    batch_size: int = 50,
    is_stock_info: bool = False,
):
    """
    Embed and upsert product documents to Qdrant and MongoDB.

    Args:
        docs: List of Document objects to embed
        all_doc_log: Dictionary mapping SKUs to document type logs
        batch_size: Number of documents to process in each batch
        is_stock_info: Whether these are stock info documents only

    Returns:
        bool: True if successful, False otherwise
    """
    if not docs:
        print("[ERROR] No documents provided for embedding")
        return False

    try:
        # Extract UUIDs from documents
        uuids = [doc.metadata["doc_id"] for doc in docs]
        print(f"[DEBUG] Processing {len(docs)} documents with {len(uuids)} unique IDs")

        # Initialize vectorstore
        vectorstore = QdrantVectorStore(
            client=qdrant,
            collection_name="product_data",
            embedding=embedding_model,
        )

        # Ensure collection exists
        if not qdrant.collection_exists(collection_name="product_data"):
            print("[INFO] Creating product_data collection in Qdrant")
            # Get embedding dimension from a sample embedding
            sample_embedding = embedding_model.embed_documents(["sample text"])[0]
            embedding_dim = len(sample_embedding)

            qdrant.recreate_collection(
                collection_name="product_data",
                vectors_config=models.VectorParams(
                    size=embedding_dim,
                    distance=models.Distance.COSINE,
                ),
            )

        # Process each SKU's document log
        for sku, doc_log in all_doc_log.items():
            print(
                f"[DEBUG] Processing SKU {sku} with document types: {list(doc_log.keys())}"
            )

            if is_stock_info:
                # Only update stock_info field in document_ids
                stock_doc_ids = doc_log.get("stock_info", [])
                if stock_doc_ids:
                    try:
                        ProductDocumentLog.objects(sku=sku).update_one(
                            set__document_ids__stock_info=stock_doc_ids,
                            upsert=True,
                        )
                        print(f"[MongoDB] Upserted stock_info for SKU {sku}")
                    except Exception as e:
                        print(f"[ERROR] Failed to update MongoDB for SKU {sku}: {e}")
            else:
                # Full product insertion flow
                existing_log = ProductDocumentLog.objects(sku=sku).first()

                if existing_log:
                    # Get all existing document IDs for this SKU
                    existing_doc_ids = []
                    for doc_type, ids in existing_log.document_ids.items():
                        if isinstance(ids, list):  # Ensure ids is a list
                            if (
                                doc_type != "stock_info" or is_stock_info
                            ):  # Don't delete stock_info unless updating it
                                existing_doc_ids.extend(ids)
                        else:
                            print(
                                f"[WARNING] Invalid document IDs format for {sku}, {doc_type}: {ids}"
                            )

                    # Delete old embeddings from Qdrant
                    if existing_doc_ids:
                        try:
                            # Use models.PointIdsList for proper point selection
                            qdrant.delete(
                                collection_name="product_data",
                                points_selector=models.PointIdsList(
                                    points=existing_doc_ids
                                ),
                            )
                            print(
                                f"[Qdrant] Deleted {len(existing_doc_ids)} old documents for SKU {sku}"
                            )
                        except Exception as e:
                            print(
                                f"[WARNING] Failed to delete old Qdrant docs for SKU {sku}: {e}"
                            )

                # Update MongoDB document log
                try:
                    # If updating stock info only, merge with existing document IDs
                    if is_stock_info and existing_log:
                        existing_doc_ids = existing_log.document_ids
                        existing_doc_ids["stock_info"] = doc_log.get("stock_info", [])
                        ProductDocumentLog.objects(sku=sku).update_one(
                            set__document_ids=existing_doc_ids,
                            upsert=True,
                        )
                    else:
                        # Overwrite all document_ids with the new ones
                        ProductDocumentLog.objects(sku=sku).update_one(
                            set__document_ids=doc_log,
                            upsert=True,
                        )
                    print(
                        f"[MongoDB] Upserted document log for SKU {sku} with types: {list(doc_log.keys())}"
                    )
                except Exception as e:
                    print(f"[ERROR] Failed to update MongoDB for SKU {sku}: {e}")

        # Add new documents to Qdrant in batches
        success_count = 0
        for i in range(0, len(docs), batch_size):
            batch_docs = docs[i : i + batch_size]
            batch_ids = uuids[i : i + batch_size]
            try:
                vectorstore.add_documents(documents=batch_docs, ids=batch_ids)
                success_count += len(batch_docs)
                print(
                    f"[Qdrant] Upserted batch {i // batch_size + 1}: {len(batch_docs)} documents"
                )
                time.sleep(5)  # To avoid rate limiting
            except Exception as e:
                print(f"[ERROR] Failed to upsert batch {i // batch_size + 1}: {e}")
                # Continue with next batch instead of failing completely

        print(f"[SUCCESS] Successfully embedded {success_count}/{len(docs)} documents")
        return success_count > 0

    except Exception as e:
        print(f"[ERROR] Failed to embed and upsert products: {e}")
        import traceback

        traceback.print_exc()
        return False


def embed_and_upsert_customers(docs: list, all_doc_log: dict, batch_size: int = 50):
    """Embed and upsert customer documents to Qdrant and MongoDB."""

    # Extract doc IDs
    uuids = [doc.metadata["doc_id"] for doc in docs]

    vectorstore = QdrantVectorStore(
        client=qdrant,
        collection_name="customer_data",
        embedding=embedding_model,
    )

    # Process customer logs
    for customer_key, doc_log in all_doc_log.items():
        existing_log = CustomerDocumentLog.objects(customer_id=customer_key).first()

        if existing_log:
            existing_doc_ids = []
            for ids in existing_log.document_ids.values():
                existing_doc_ids.extend(ids)

            if existing_doc_ids:
                try:
                    qdrant.delete(
                        collection_name="customer_data",
                        points_selector=existing_doc_ids,
                    )
                    print(f"[Qdrant] Deleted old documents for customer {customer_key}")
                except Exception as e:
                    print(f"Warning: Failed to delete old docs for {customer_key}: {e}")

        # Overwrite document log
        CustomerDocumentLog.objects(customer_id=customer_key).update_one(
            set__document_ids=doc_log, upsert=True
        )
        print(f"[MongoDB] Upserted customer document log for {customer_key}")

    # Add new documents in batches
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i : i + batch_size]
        batch_ids = uuids[i : i + batch_size]
        try:
            vectorstore.add_documents(documents=batch_docs, ids=batch_ids)
            print(
                f"[Qdrant] Upserted batch {i // batch_size + 1}: {len(batch_docs)} docs"
            )
            time.sleep(5)
        except Exception as e:
            print(f"Warning: Failed to upsert batch {i // batch_size + 1}: {e}")


def embed_and_upsert(
    documents, collection_name: str, doc_logs: Dict[str, List[str]]
) -> bool:
    """
    Embed documents and upsert them to Qdrant.

    Args:
        documents: List of Document objects to embed
        collection_name: Name of the Qdrant collection
        doc_logs: Dictionary mapping document types to lists of document IDs

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract UUIDs from documents
        uuids = [doc.metadata["doc_id"] for doc in documents]

        vectorstore = QdrantVectorStore(
            client=qdrant,
            collection_name=collection_name,
            embedding=embedding_model,
        )

        # Add new documents to Qdrant
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            batch_ids = uuids[i : i + batch_size]
            try:
                vectorstore.add_documents(documents=batch_docs, ids=batch_ids)
                print(
                    f"[Qdrant] Upserted batch {i // batch_size + 1}: {len(batch_docs)} documents"
                )
                time.sleep(5)  # Avoid rate limiting
            except Exception as e:
                print(f"Warning: Failed to upsert batch {i // batch_size + 1}: {e}")

        # Log document IDs
        with open(f"/tmp/{collection_name}_doc_logs.json", "w") as f:
            json.dump(doc_logs, f)

        return True

    except Exception as e:
        print(f"Error embedding and upserting documents: {e}")
        return False


def embed_and_upsert_pdfs(docs: list, all_doc_log: dict, batch_size: int = 50):
    """Embed and upsert PDF documents into Qdrant and log in MongoDB."""

    # Extract UUIDs for each document
    uuids = [doc.metadata["doc_id"] for doc in docs]

    # Initialize vectorstore
    vectorstore = QdrantVectorStore(
        client=qdrant,
        collection_name="pdf_data",
        embedding=embedding_model,
    )

    for file_name, doc_log in all_doc_log.items():
        # Step 1: Check if this PDF file was already processed
        existing_log = PDFDocumentLog.objects(file_name=file_name).first()

        if existing_log:
            # Step 2: Get old document IDs
            existing_doc_ids = []
            for ids in existing_log.document_ids.values():
                existing_doc_ids.extend(ids)

            # Step 3: Delete old embeddings from Qdrant
            if existing_doc_ids:
                try:
                    qdrant.delete(
                        collection_name="pdf_data",
                        points_selector=existing_doc_ids,
                    )
                    print(f"[INFO] Removed old embeddings for {file_name}")
                except Exception as e:
                    print(f"[WARN] Failed to delete old vectors for {file_name}: {e}")

        # Step 4: Update or insert new doc IDs into MongoDB
        PDFDocumentLog.objects(file_name=file_name).update_one(
            set__document_ids=doc_log,
            upsert=True,
        )
        print(f"[MONGO] Log updated for {file_name}")

    # Step 5: Upsert new documents to Qdrant
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i : i + batch_size]
        batch_ids = uuids[i : i + batch_size]
        try:
            vectorstore.add_documents(documents=batch_docs, ids=batch_ids)
            print(
                f"[QDRANT] Batch {i // batch_size + 1} upserted: {len(batch_docs)} docs"
            )
            time.sleep(5)  # To reduce overload or rate limit risk
        except Exception as e:
            print(f"[ERROR] Failed to upsert batch {i // batch_size + 1}: {e}")


##########################################################################################################################

import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()


class BaseMagentoClient:
    """Base client for interacting with Magento API."""

    def __init__(self):
        self.base_url = os.environ.get("MAGENTO_API_URL")
        self.api_token = os.environ.get("MAGENTO_API_TOKEN")

        if not self.base_url or not self.api_token:
            raise ValueError("Magento API configuration missing")

    def get_headers(self) -> Dict[str, str]:
        """Get headers for Magento API requests."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

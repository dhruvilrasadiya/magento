import uuid
import json
from typing import Dict, List, Any
from langchain_core.documents import Document
from utils.embed_utils import embed_and_upsert_products

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def preprocess_dge_product_data(**context):
    """Process DGE product data and prepare it for vector storage."""
    ti = context["task_instance"]
    data = ti.xcom_pull(task_ids="fetch_dge_products")

    if not data or "products" not in data:
        print("[ERROR] No products found in XCom pull.")
        return False

    products = data.get("products", [])
    print(f"[PROCESS] Processing {len(products)} DGE products")

    all_docs = []
    all_doc_log = {}
    processed_productcodes = set()

    for product in products:
        if "basic" in product:
            productcode = product.get("basic", {}).get("productcode", "")
            name = product.get("basic", {}).get("description", "")
        else:
            productcode = product.get("productcode", "")
            name = product.get("name", "")

        if not productcode:
            print(f"[WARNING] Product missing productcode, skipping: {product.get('id', 'unknown')}")
            continue

        if productcode in processed_productcodes:
            print(f"[INFO] Skipping duplicate productcode: {productcode}")
            continue

        processed_productcodes.add(productcode)

        doc_log = {}
        single_product_docs = []

        metadata_base = {
            "productcode": productcode,
            "name": name,
            "fetched_store_key": "dge",
            "website_id": 10,
        }

        source = "dge"

        # 1. Basic document
        basic_info = product.get("basic", {})
        if basic_info:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"DGE Basic Info: {json.dumps(basic_info, indent=2)}",
                metadata={**metadata_base, "type": "basic", "doc_id": doc_uuid, "source": source}
            )
            single_product_docs.append(doc)
            doc_log["basic"] = [doc_uuid]
            print(f"[INFO] Created basic document for productcode {productcode}")

        # 2. Unit document
        unit_info = product.get("unit", {})
        if unit_info:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"DGE Unit Info: {json.dumps(unit_info, indent=2)}",
                metadata={**metadata_base, "type": "unit", "doc_id": doc_uuid, "source": source}
            )
            single_product_docs.append(doc)
            doc_log["unit"] = [doc_uuid]
            print(f"[INFO] Created unit document for productcode {productcode}")

        # 3. Price document
        price_info = product.get("price", {})
        if price_info:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"DGE Price Info: {json.dumps(price_info, indent=2)}",
                metadata={**metadata_base, "type": "price", "doc_id": doc_uuid, "source": source}
            )
            single_product_docs.append(doc)
            doc_log["price"] = [doc_uuid]
            print(f"[INFO] Created price document for productcode {productcode}")

        # 4. Logistics document
        logistics_info = product.get("logistics", {})
        if logistics_info:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"DGE Logistics Info: {json.dumps(logistics_info, indent=2)}",
                metadata={**metadata_base, "type": "logistics", "doc_id": doc_uuid, "source": source}
            )
            single_product_docs.append(doc)
            doc_log["logistics"] = [doc_uuid]
            print(f"[INFO] Created logistics document for productcode {productcode}")

        all_doc_log[productcode] = doc_log
        all_docs.extend(single_product_docs)
        print(f"[INFO] Processed product {productcode} with {len(single_product_docs)} documents")

    if not all_docs:
        print("[WARNING] No documents created for embedding")
        return False

    print(f"[INFO] Embedding {len(all_docs)} documents for {len(all_doc_log)} products")
    result = embed_and_upsert_products(all_docs, all_doc_log, is_stock_info=False)

    if result:
        print(f"[SUCCESS] Successfully processed and embedded {len(all_doc_log)} DGE products")
        return True
    else:
        print(f"[ERROR] Failed to embed products")
        return False

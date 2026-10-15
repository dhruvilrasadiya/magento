import json
import uuid
import os
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from langchain_core.documents import Document
from utils.embed_utils import embed_and_upsert_orders
from scripts.order_data.fetch_dge_orders import DGEClient


def preprocess_dge_order_data(**context):
    """Process DGE order data and prepare it for vector storage."""
    ti = context["task_instance"]
    data = ti.xcom_pull(task_ids="fetch_dge_orders")

    if not data or "orders" not in data:
        print("[ERROR] No orders found in XCom pull.")
        return False

    orders = data["orders"]
    sales_orders = data.get("sales_orders", False)

    if not orders:
        print("[WARNING] No orders found in DGE data")
        return False

    print(f"[INFO] Processing {len(orders)} DGE orders...")

    all_docs = []
    all_doc_log = {}

    if sales_orders:
        key_type = "dge_sales_order_summary"
    else:
        key_type = "dge_backorder_summary"

    for order in orders:
        order_id = order.get("id")
        print("++++++++++++++++++++++++++++  ORDER ID   ++++++++++++++++ :", order_id)
        doc_log: dict[str, list[str]] = {}
        single_order_docs = []

        metadata_base = {
            "order_id": order_id,
            "customer_id": order.get("customerParty", {}).get("id"),
            "customer_name": order.get("customerParty", {}).get("name"),
            "created_at": order.get("date"),
            "status": order.get("status"),
            "source": "dge",
        }

        doc_uuid = str(uuid.uuid4())
        summary_doc = Document(
            page_content=f"for order of DGE platform {order_id} order_summary details are {json.dumps(order, indent=2)}",
            metadata={**metadata_base, "type": key_type, "doc_id": doc_uuid},
        )
        single_order_docs.append(summary_doc)
        doc_log[key_type] = [doc_uuid]

        all_doc_log[order_id] = doc_log
        all_docs.extend(single_order_docs)

    print(f"[INFO] Embedding {len(all_docs)} documents for {len(all_doc_log)} orders")
    result = embed_and_upsert_orders(all_docs, all_doc_log)

    if result:
        print(
            f"[SUCCESS] Successfully processed and embedded {len(all_doc_log)} DGE orders"
        )
        return True
    else:
        print(f"[ERROR] Failed to embed orders")
        return False

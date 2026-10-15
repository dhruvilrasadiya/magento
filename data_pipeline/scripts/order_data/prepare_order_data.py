import json
import uuid
import json
from typing import Any, Dict, List, Tuple
from langchain_core.documents import Document
from utils.embed_utils import embed_and_upsert_orders


def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """
    Flattens a nested dictionary into a single level using dot notation.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def find_values_by_key(data, key):
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key:
                yield v
            if isinstance(v, (dict, list)):
                yield from find_values_by_key(v, key)
    elif isinstance(data, list):
        for item in data:
            yield from find_values_by_key(item, key)


def extract_order_summary(order: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    def get_nested(d: Dict[str, Any], keys: List[str], default=None):
        for key in keys:
            if isinstance(d, dict) and key in d:
                d = d[key]
            else:
                return default
        return d

    order_id = order.get("entity_id", "unknown")

    # Basic Info
    summary = {
        "order_id": order.get("entity_id"),
        "increment_id": order.get("increment_id"),
        "created_at": order.get("created_at"),
        "status": order.get("status"),
        "state": order.get("state"),
        "currency": order.get("order_currency_code"),
        "customer_email": order.get("customer_email"),
        "customer_name": f"{order.get('customer_firstname', '')} {order.get('customer_lastname', '')}".strip(),
        "subtotal": order.get("subtotal"),
        "tax": order.get("tax_amount"),
        "shipping": order.get("shipping_amount"),
        "discount": order.get("discount_amount"),
        "grand_total": order.get("grand_total"),
    }

    # Billing Address
    billing = order.get("billing_address", {})
    summary["billing_address"] = {
        "name": f"{billing.get('firstname', '')} {billing.get('lastname', '')}".strip(),
        "street": billing.get("street"),
        "city": billing.get("city"),
        "postcode": billing.get("postcode"),
        "country": billing.get("country_id"),
        "telephone": billing.get("telephone"),
    }

    # Shipping Address (if available)
    shipping = (
        order.get("extension_attributes", {})
        .get("shipping_assignments", [])[0]
        .get("shipping")
        .get("address")
    )

    print("shipping", shipping)
    if shipping:
        summary["shipping_address"] = {
            "name": f"{shipping.get('firstname', '')} {shipping.get('lastname', '')}".strip(),
            "street": shipping.get("street"),
            "city": shipping.get("city"),
            "postcode": shipping.get("postcode"),
            "country": shipping.get("country_id"),
            "telephone": shipping.get("telephone"),
        }

    # Payment Info
    payment = order.get("payment", {})
    summary["payment_method"] = payment.get("method")
    additional_info = payment.get("additional_information", [])
    if additional_info:
        summary["payment_label"] = additional_info[0]  # e.g. "Mastercard"

    # Items (summarized)
    summary["items"] = [
        {
            "sku": item.get("sku"),
            "name": item.get("name"),
            "qty": item.get("qty_ordered"),
            "price": item.get("price"),
            "price_incl_tax": item.get("price_incl_tax"),
        }
        for item in order.get("items", [])
    ]

    return summary, order_id


def preprocess_order_data(**context):

    ti = context["ti"]

    # Get the filename from upstream task
    filename = ti.xcom_pull(task_ids="fetch_orders", key="orders_file")
    orders_count = ti.xcom_pull(task_ids="fetch_orders", key="orders_count")
    
    print(f"[PROCESS] Processing {orders_count} orders from {filename}")
    
    # Read orders from file
    with open(filename, 'r') as f:
        orders = json.load(f)

    print(f"[PROCESS] Found {len(orders)} orders in {filename}")

    if not orders:
        print("[ERROR] No orders found in XCom pull.")
        return

    all_docs = []
    all_doc_logs = {}

    for order in orders:
        order_id = order.get("entity_id") or order.get("order_id")
        print("++++++++++++++++++++++++++++  ORDER ID   ++++++++++++++++ :", order_id)
        doc_log: dict[str, list[str]] = {}
        single_order_docs = []

        skus = list(find_values_by_key(order.get("items", []), "sku"))

        metadata_base = {
            "order_id": order_id,
            "customer_id": order.get("customer_id"),
            "customer_name": order.get("customer_name")
            or f"{order.get('customer_firstname', '')} {order.get('customer_lastname', '')}".strip(),
            "created_at": order.get("created_at"),
            "updated_at": order.get("updated_at"),
            "status": order.get("status"),
            "item_skus": skus,
            "source": "magento",
        }

        # 1. Shipping
        shipping = order.get("extension_attributes", {}).get("shipping_assignments", [])
        if shipping:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"for order {order_id} shipping details are {json.dumps(shipping, indent=2)}",
                metadata={**metadata_base, "type": "shipping", "doc_id": doc_uuid},
            )
            single_order_docs.append(doc)
            doc_log["shipping"] = [doc_uuid]

        # 2. Payment
        if "payment" in order:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"for order {order_id} payment details are {json.dumps(order["payment"], indent=2)}",
                metadata={**metadata_base, "type": "payment", "doc_id": doc_uuid},
            )
            single_order_docs.append(doc)
            doc_log["payment"] = [doc_uuid]

        # 3. Billing Address
        if "billing_address" in order:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"for order {order_id} billing_address details are {json.dumps(order["billing_address"], indent=2)}",
                metadata={
                    **metadata_base,
                    "type": "billing_address",
                    "doc_id": doc_uuid,
                },
            )
            single_order_docs.append(doc)
            doc_log["billing_address"] = [doc_uuid]

        # 4. Items
        items = order.get("items", [])
        if items:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"for order {order_id} item details are {json.dumps(items, indent=2)}",
                metadata={**metadata_base, "type": "item", "doc_id": doc_uuid},
            )
            single_order_docs.append(doc)
            doc_log["item"] = [doc_uuid]

        # 5. Order Summary (flattened)
        summary, order_id = extract_order_summary(order)
        doc_uuid = str(uuid.uuid4())
        summary_doc = Document(
            page_content=f"for order {order_id} order_summary details are {json.dumps(summary, indent=2)}",
            metadata={**metadata_base, "type": "order_summary", "doc_id": doc_uuid},
        )
        single_order_docs.append(summary_doc)
        doc_log["order_summary"] = [doc_uuid]

        # 6. Status Histories
        status_histories = order.get("status_histories", [])
        if status_histories:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"for order {order_id} status_history details are {json.dumps(status_histories, indent=2)}",
                metadata={
                    **metadata_base,
                    "type": "status_history",
                    "doc_id": doc_uuid,
                },
            )
            single_order_docs.append(doc)
            doc_log["status_history"] = [doc_uuid]

        print(
            f"[PREPROCESS] Processed order {order_id} with {len(single_order_docs)} documents."
        )
        all_doc_logs[order_id] = doc_log
        all_docs.extend(single_order_docs)

    print(
        f"[QDRANT] Final upsert of {len(all_docs)} total documents across {len(orders)} orders."
    )
    embed_and_upsert_orders(all_docs, all_doc_logs)

    return True

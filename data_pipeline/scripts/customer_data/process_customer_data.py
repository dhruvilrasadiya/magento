import json
import uuid
from typing import Any, Dict, List
from langchain_core.documents import Document
from scripts.customer_data.fetch_customers import CustomerClient
from utils.embed_utils import embed_and_upsert_customers


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


def process_customer_data(**context):
    """Process customer data and fetch related information."""
    ti = context["ti"]
    data = ti.xcom_pull(task_ids="fetch_customers")

    customers = data.get("customers", [])
    if not customers:
        print("[ERROR] No customers found in XCom pull.")
        return

    client = CustomerClient()
    all_docs = []
    all_doc_logs = {}

    # Process only first 10 customers for testing
    # customers = customers[:10]

    for customer in customers:
        customer_id = customer.get("id")
        customer_email = customer.get("email")
        print(
            f"++++++++++++++++++++++++++++  CUSTOMER ID: {customer_id}  ++++++++++++++++"
        )

        doc_log: dict[str, list[str]] = {}
        customer_docs = []

        # Base metadata for all customer documents
        metadata_base = {
            "customer_id": customer_id,
            "customer_email": customer_email,
            "customer_name": f"{customer.get('firstname', '')} {customer.get('lastname', '')}".strip(),
            "created_at": customer.get("created_at"),
            "updated_at": customer.get("updated_at"),
        }

        # 1. Customer Profile
        ignored_keys = ["addresses", "extension_attributes", "custom_attributes"]
        base_customer_info = {
            k: v for k, v in customer.items() if k not in ignored_keys
        }
        flattened = flatten_dict(base_customer_info)

        doc_uuid = str(uuid.uuid4())
        profile_doc = Document(
            page_content=f"Customer profile for {metadata_base['customer_name']} (ID: {customer_id}, Email: {customer_email}): {json.dumps(flattened, indent=2)}",
            metadata={**metadata_base, "type": "customer_profile", "doc_id": doc_uuid},
        )
        customer_docs.append(profile_doc)
        doc_log["customer_profile"] = [doc_uuid]

        # 2. Customer Addresses
        addresses = customer.get("addresses", [])
        if addresses:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"Customer addresses for {metadata_base['customer_name']} (ID: {customer_id}): {json.dumps(addresses, indent=2)}",
                metadata={
                    **metadata_base,
                    "type": "customer_addresses",
                    "doc_id": doc_uuid,
                },
            )
            customer_docs.append(doc)
            doc_log["customer_addresses"] = [doc_uuid]

        # 3. Customer Orders
        try:
            orders = client.fetch_customer_orders(customer_email)
            if orders:
                doc_uuid = str(uuid.uuid4())
                doc = Document(
                    page_content=f"Orders for customer {metadata_base['customer_name']} (Email: {customer_email}): {json.dumps([{'order_id': o.get('entity_id'), 'status': o.get('status'), 'created_at': o.get('created_at'), 'total': o.get('grand_total')} for o in orders], indent=2)}",
                    metadata={
                        **metadata_base,
                        "type": "customer_orders",
                        "doc_id": doc_uuid,
                        "order_count": len(orders),
                    },
                )
                customer_docs.append(doc)
                doc_log["customer_orders"] = [doc_uuid]

                # 4. Process invoices for each order
                for order in orders[
                    :3
                ]:  # Limit to first 3 orders to avoid too many API calls
                    order_id = order.get("entity_id")
                    invoices = client.fetch_customer_invoices(order_id)
                    if invoices:
                        doc_uuid = str(uuid.uuid4())
                        doc = Document(
                            page_content=f"Invoices for order {order_id} of customer {metadata_base['customer_name']}: {json.dumps([{'invoice_id': i.get('entity_id'), 'order_id': i.get('order_id'), 'created_at': i.get('created_at'), 'total': i.get('grand_total')} for i in invoices], indent=2)}",
                            metadata={
                                **metadata_base,
                                "type": "customer_invoices",
                                "doc_id": doc_uuid,
                                "order_id": order_id,
                            },
                        )
                        customer_docs.append(doc)
                        if "customer_invoices" not in doc_log:
                            doc_log["customer_invoices"] = []
                        doc_log["customer_invoices"].append(doc_uuid)
        except Exception as e:
            print(
                f"Error fetching orders/invoices for customer {customer_id}: {str(e)}"
            )

        # 5. Customer Cart
        try:
            carts = client.fetch_customer_cart(customer_email)
            if carts:
                doc_uuid = str(uuid.uuid4())
                doc = Document(
                    page_content=f"Shopping cart for customer {metadata_base['customer_name']} (Email: {customer_email}): {json.dumps([{'cart_id': c.get('id'), 'item_count': len(c.get('items', [])), 'created_at': c.get('created_at')} for c in carts], indent=2)}",
                    metadata={
                        **metadata_base,
                        "type": "customer_cart",
                        "doc_id": doc_uuid,
                    },
                )
                customer_docs.append(doc)
                doc_log["customer_cart"] = [doc_uuid]
        except Exception as e:
            print(f"Error fetching cart for customer {customer_id}: {str(e)}")

        print(
            f"[PREPROCESS] Processed customer {customer_id} with {len(customer_docs)} documents."
        )
        all_doc_logs[customer_id] = doc_log
        all_docs.extend(customer_docs)

    print(
        f"[QDRANT] Final upsert of {len(all_docs)} total documents across {len(customers)} customers."
    )
    embed_and_upsert_customers(all_docs, all_doc_logs)

    return True

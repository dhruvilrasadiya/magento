import json
import uuid
from langchain_core.documents import Document
from utils.embed_utils import embed_and_upsert_customers


def preprocess_dge_customer_data(**context):
    """Process DGE customer data and prepare it for vector storage."""
    ti = context["task_instance"]
    data = ti.xcom_pull(task_ids="fetch_dge_customers")

    if not data or "customers" not in data:
        print("[ERROR] No customers found in XCom pull.")
        return False

    customers = data["customers"]

    if not customers:
        print("[WARNING] No customers found in DGE data")
        return False

    print(f"[INFO] Processing {len(customers)} DGE customers...")

    all_docs = []
    all_doc_log = {}

    for customer in customers:
        print("++++++++++++++++++++++++++++ :", customer, type(customer))
        customer_id = customer.get("id")
        print(
            "++++++++++++++++++++++++++++  customer ID   ++++++++++++++++ :",
            customer_id,
        )
        doc_log: dict[str, list[str]] = {}
        single_customer_docs = []

        metadata_base = {
            "customer_id": customer_id,
            "customer_name": customer.get("name"),
            "matchcode": customer.get("matchcode"),
            "status": customer.get("visitingAddress").get("phone"),
            "source": "dge",
        }

        doc_uuid = str(uuid.uuid4())
        summary_doc = Document(
            page_content=f"for customer of DGE platform ID: {customer_id} and Name: {customer.get('name')} customer details are {json.dumps(customer, indent=2)}",
            metadata={**metadata_base, "type": "dge_customer", "doc_id": doc_uuid},
        )
        single_customer_docs.append(summary_doc)
        doc_log["dge_customer"] = [doc_uuid]

        all_doc_log[customer_id] = doc_log
        all_docs.extend(single_customer_docs)

    print(f"[INFO] Embedding {len(all_docs)} documents for {len(all_doc_log)} customer")
    result = embed_and_upsert_customers(all_docs, all_doc_log)

    if result:
        print(
            f"[SUCCESS] Successfully processed and embedded {len(all_doc_log)} DGE customer"
        )
        return True
    else:
        print(f"[ERROR] Failed to embed customer")
        return False

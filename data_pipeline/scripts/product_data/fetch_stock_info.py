import json
import uuid
import requests
from typing import Any, Dict, List
from langchain_core.documents import Document
from utils.embed_utils import embed_and_upsert_products, BaseMagentoClient

class MagentoClient(BaseMagentoClient):
    def fetch_stock_info(self, sku: str) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/rest/V1/stockItems/{sku}"
        response = requests.get(endpoint, headers=self.get_headers())
        # response.raise_for_status()
        if response.status_code == 404:
            return {"qty": 0, "is_in_stock": False}
        return response.json()

def stock_info_data_fetch(**context):
    ti = context["ti"]
    data = ti.xcom_pull(task_ids="fetch_products")

    # Get the filename from upstream task
    filename = ti.xcom_pull(task_ids="fetch_products", key="products_file")
    products_count = ti.xcom_pull(task_ids="fetch_products", key="products_count")

    with open(filename, 'r') as f:
        products = json.load(f)

    print(f"[PROCESS] Found {len(products)} products in {filename} and {products_count} orders")

    # products = data.get("products", [])
    store_key = data.get("store_key")
    store_id = data.get("store_id")

    all_docs = []
    all_doc_log = {}
    client = MagentoClient()

    for product in products:
        sku = product.get("sku")
        print("+++++++++++++++++++  SKU  ++++++++++++++++++++ :", sku)
        stock_info = client.fetch_stock_info(sku)

        doc_uuid = str(uuid.uuid4())
        metadata = {
            "sku": sku,
            "id": product.get("id"),
            "name": product.get("name"),
            "type_id": product.get("type_id"),
            "status": product.get("status"),
            "store_key": store_key,
            "website_id": store_id
        }

        doc = Document(
            page_content=f"Stock info for SKU {sku}: {json.dumps(stock_info, indent=2)}",
            metadata={**metadata, "type": "stock_info", "doc_id": doc_uuid, "qty": stock_info.get("qty"), "is_in_stock": stock_info.get("is_in_stock")},
        )
        all_docs.append(doc)
        all_doc_log[sku] = {"stock_info": [doc_uuid]}

    if all_docs:
        embed_and_upsert_products(all_docs, all_doc_log, is_stock_info=True)

    return True

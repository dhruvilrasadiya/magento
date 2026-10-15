import json
import uuid
from typing import Any, Dict
from langchain_core.documents import Document
from utils.embed_utils import embed_and_upsert_products

STORE_WEBSITE_IDS = {
    "terrasheater": 1,
    "gereedschapskist": 2,
    "heaterdirect": 3,
    "cilinders": 9,
}

def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def preprocess_product_data(**context):
    ti = context["ti"]
    product_orders_data = ti.xcom_pull(task_ids="fetch_product_orders", key="product_orders")

    # Get the filename from upstream task
    filename = ti.xcom_pull(task_ids="fetch_products", key="products_file")
    products_count = ti.xcom_pull(task_ids="fetch_products", key="products_count")

    with open(filename, 'r') as f:
        products = json.load(f)
    print(f"[PROCESS] Found {len(products)} products in {filename} and {products_count} orders")

    if not products:
        print("[ERROR] No products found in XCom pull.")
        return

    all_docs = []
    all_doc_log = {}
    processed_skus = set()

    for product in products:
        sku = product.get("sku")
        if not sku:
            continue

        doc_log: dict[str, list[str]] = {}
        single_product_docs = []

        fetched_store_key = product.get("fetched_store_key")
        website_id = STORE_WEBSITE_IDS.get(fetched_store_key)

        metadata_base = {
            "sku": sku,
            "id": product.get("id"),
            "name": product.get("name"),
            "type_id": product.get("type_id"),
            "status": product.get("status"),
            "visibility": product.get("visibility"),
            "fetched_store_key": fetched_store_key,
            "website_id": website_id,
        }

        # Always store pricing documents store-wise
        price = product.get("price")
        if price is not None and website_id is not None:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"For Product {product.get('name')}, sku --> {sku} pricing is {price} for website_id {website_id}",
                metadata={**metadata_base, "type": "pricing", "doc_id": doc_uuid},
            )
            single_product_docs.append(doc)
            doc_log.setdefault("pricing", []).append(doc_uuid)

        # Avoid duplicating other documents for the same SKU
        if sku in processed_skus:
            all_docs.extend(single_product_docs)
            all_doc_log[sku] = doc_log
            continue

        processed_skus.add(sku)

        custom_attributes = product.get("custom_attributes", [])
        if custom_attributes:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"For Product {product.get('name')}, sku --> {sku} custom_attributes are {json.dumps(custom_attributes, indent=2)}",
                metadata={**metadata_base, "type": "custom_attributes", "doc_id": doc_uuid},
            )
            single_product_docs.append(doc)
            doc_log["custom_attributes"] = [doc_uuid]

        if product_orders_data and sku in product_orders_data:
            orders = product_orders_data[sku]
            if orders:
                order_ids = set()
                order_summary = []
                for order in orders:
                    order_ids.add(order["order_id"])
                    order_summary.append({
                        "order_id": order["order_id"],
                        "item_id": order.get("item_id"),
                        "name": order.get("name"),
                        "created_at": order.get("created_at"),
                        "qty_ordered": order.get("qty_ordered"),
                        "price": order.get("price"),
                        "price_incl_tax": order.get("price_incl_tax"),
                        "row_total": order.get("row_total"),
                        "row_total_incl_tax": order.get("row_total_incl_tax"),
                        "tax_percent": order.get("tax_percent"),
                        "status": {
                            "qty_invoiced": order.get("qty_invoiced"),
                            "qty_shipped": order.get("qty_shipped"),
                            "qty_refunded": order.get("qty_refunded"),
                            "qty_canceled": order.get("qty_canceled"),
                        },
                    })
                doc_uuid = str(uuid.uuid4())
                doc = Document(
                    page_content=f"For Product {product.get('name')}, sku --> {sku} order details: Orders count: {len(orders)}, Order IDs: {list(order_ids)}, Order details: {json.dumps(order_summary, indent=2)}",
                    metadata={**metadata_base, "type": "orders_details", "doc_id": doc_uuid, "orders_count": len(orders), "order_ids": list(order_ids)},
                )
                single_product_docs.append(doc)
                doc_log["orders_details"] = [doc_uuid]

        extension_attributes = product.get("extension_attributes", {})
        if extension_attributes:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"For Product {product.get('name')}, sku --> {sku} extension_attributes are {json.dumps(extension_attributes, indent=2)}",
                metadata={**metadata_base, "type": "extension_attributes", "doc_id": doc_uuid},
            )
            single_product_docs.append(doc)
            doc_log["extension_attributes"] = [doc_uuid]

        description = next((attr["value"] for attr in custom_attributes if attr["attribute_code"] == "description"), None)
        if description:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"For Product {product.get('name')}, sku --> {sku} description is {description}",
                metadata={**metadata_base, "type": "description", "doc_id": doc_uuid},
            )
            single_product_docs.append(doc)
            doc_log["description"] = [doc_uuid]

        categories = product.get("category_ids", [])
        if categories:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"For Product {product.get('name')}, sku --> {sku} category are {categories}",
                metadata={**metadata_base, "type": "category", "doc_id": doc_uuid},
            )
            single_product_docs.append(doc)
            doc_log["category"] = [doc_uuid]

        brand = next((attr["value"] for attr in custom_attributes if attr["attribute_code"] == "brand"), None)
        if brand:
            doc_uuid = str(uuid.uuid4())
            doc = Document(
                page_content=f"Product {product.get('name')} belongs to Brand: {brand}",
                metadata={**metadata_base, "type": "brand", "doc_id": doc_uuid},
            )
            single_product_docs.append(doc)
            doc_log["brand"] = [doc_uuid]

        ignored_keys = ["custom_attributes", "extension_attributes"]
        base_product_info = {k: v for k, v in product.items() if k not in ignored_keys}
        flattened = flatten_dict(base_product_info)
        doc_uuid = str(uuid.uuid4())
        summary_doc = Document(
            page_content=f"For Product {product.get('name')}, sku --> {sku} summary is {json.dumps(flattened, indent=2)}",
            metadata={**metadata_base, "type": "summary", "doc_id": doc_uuid},
        )
        single_product_docs.append(summary_doc)
        doc_log["summary"] = [doc_uuid]

        all_doc_log[sku] = doc_log
        all_docs.extend(single_product_docs)

    embed_and_upsert_products(all_docs, all_doc_log, is_stock_info=False)
    return True

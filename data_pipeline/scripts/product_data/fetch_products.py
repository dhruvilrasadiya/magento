import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Any, Dict, List
from utils.embed_utils import BaseMagentoClient

load_dotenv()

STORE_WEBSITE_KEYS = {
    "terrasheater": "terrasheater_nederlands",
    "gereedschapskist": "gereedschapskist_nederlands",
    "heaterdirect": "heaterdirect_nederlands",
    "cilinders": "cilinders_nederlands",
}

STORE_WEBSITE_IDS = {
    "terrasheater": 1,
    "gereedschapskist": 2,
    "heaterdirect": 3,
    "cilinders": 9,
}


class MagentoClient(BaseMagentoClient):
    """Client for interacting with Magento API for product data."""

    def fetch_products(
        self,
        since: datetime,
        current_page: int = 1,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch products updated since a given date from all websites/stores."""

        all_products = []

        for store_key, rest_key in STORE_WEBSITE_KEYS.items():
            endpoint = f"{self.base_url.rstrip('/')}/rest/{rest_key}/V1/products"
            current_page_store = current_page
            store_products = []

            print(f"[FETCH] Store: {store_key}, Endpoint: {endpoint}")

            while True:
                params = {
                    "searchCriteria[filterGroups][0][filters][0][field]": "created_at",
                    "searchCriteria[filterGroups][0][filters][0][value]": since.isoformat(),
                    "searchCriteria[filterGroups][0][filters][0][condition_type]": "gteq",
                    "searchCriteria[currentPage]": current_page_store,
                    "searchCriteria[pageSize]": page_size,
                }

                try:
                    response = requests.get(
                        endpoint, headers=self.get_headers(), params=params
                    )
                    response.raise_for_status()
                    data = response.json()

                    total_count = data.get("total_count", 0)
                    items = data.get("items", [])

                    if not items:
                        print(
                            f"[INFO] No more products from page {current_page_store} in store {store_key}"
                        )
                        break

                    print(
                        f"[INFO] Retrieved {len(items)} products from page {current_page_store} in store {store_key}"
                    )

                    for item in items:
                        item["fetched_store_key"] = store_key
                        item["website_id"] = STORE_WEBSITE_IDS.get(store_key)

                    store_products.extend(items)

                    if len(store_products) < page_size:
                        break

                    current_page_store += 1

                except requests.RequestException as e:
                    print(f"[ERROR] Failed to fetch from {store_key}: {e}")
                    break

            print(
                f"[INFO] Total products fetched from {store_key}: {len(store_products)}"
            )
            all_products.extend(store_products)  # truncate per-store

        print(f"[FETCH] Fetched {len(all_products)} total products across all stores.")
        return all_products, total_count

    def fetch_product_by_sku(self, sku: str) -> List[Dict[str, Any]]:
        """
        Fetch product by SKU from all websites/stores (to get pricing and data per store).
        Returns a list of store-specific product data with store key annotated.
        """

        all_store_products = []

        for store_key, rest_key in STORE_WEBSITE_KEYS.items():
            endpoint = f"{self.base_url.rstrip('/')}/rest/{rest_key}/V1/products/{sku}"
            print(f"[FETCH BY SKU] Store: {store_key}, Endpoint: {endpoint}")

            try:
                response = requests.get(endpoint, headers=self.get_headers())
                response.raise_for_status()
                product_data = response.json()

                # Add store identifier and website_id
                product_data["fetched_store_key"] = store_key
                product_data["website_id"] = STORE_WEBSITE_IDS.get(store_key)

                print(f"[INFO] Successfully fetched SKU {sku} for store {store_key}")
                all_store_products.append(product_data)

            except requests.HTTPError as e:
                print(f"[ERROR] Failed to fetch SKU {sku} for store {store_key}: {e}")
                error_data = {
                    "sku": sku,
                    "fetched_store_key": store_key,
                    "website_id": STORE_WEBSITE_IDS.get(store_key),
                    "error": str(e),
                }
                all_store_products.append(error_data)

            except requests.RequestException as e:
                print(f"[ERROR] Request failed for SKU {sku} at store {store_key}: {e}")
                error_data = {
                    "sku": sku,
                    "fetched_store_key": store_key,
                    "website_id": STORE_WEBSITE_IDS.get(store_key),
                    "error": str(e),
                }
                all_store_products.append(error_data)

        print(
            f"[FETCH BY SKU] Fetched {len(all_store_products)} records for SKU: {sku}"
        )
        return all_store_products

    def fetch_product_orders(self, sku: str) -> List[Dict[str, Any]]:
        """Fetch orders for a specific product by SKU."""

        endpoint = f"{self.base_url}/rest/V1/orders/items"
        params = {
            "searchCriteria[filterGroups][0][filters][0][field]": "sku",
            "searchCriteria[filterGroups][0][filters][0][value]": sku,
            "searchCriteria[filterGroups][0][filters][0][condition_type]": "eq",
        }

        response = requests.get(endpoint, headers=self.get_headers(), params=params)
        response.raise_for_status()

        return response.json().get("items", [])


def fetch_magento_products(**context):
    skus = context["params"].get("skus", [])
    is_initial = context["params"].get("is_initial", False)

    ti = context["ti"]

    # Create data directory if it doesn't exist
    data_dir = "/tmp/airflow_data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate unique filename based on run_id
    run_id = context["dag_run"].run_id
    filename = f"{data_dir}/products_{run_id.replace(':', '_')}.json"

    execution_date = context.get("execution_date", datetime.utcnow())
    prev_execution_date = context.get("prev_execution_date_success")

    client = MagentoClient()

    try:
        products = []

        if skus:
            # Fetch by SKU list
            for sku in skus:
                store_product_data = client.fetch_product_by_sku(sku)
                for product in store_product_data:
                    product.setdefault("sku", sku)
                    products.append(product)

            print(
                f"[FETCH] Fetched {len(products)} store-specific product documents by SKU."
            )

        else:
            # Fetch all or by modified timestamps
            if is_initial:
                since = datetime(2000, 1, 1)
            else:
                if prev_execution_date:
                    since = prev_execution_date
                else:
                    since = execution_date - timedelta(days=1)

            print(f"[FETCH] Fetching products modified since: {since.isoformat()}")

            products, total_count = client.fetch_products(
                since=since, page_size=1000 if is_initial else 500
            )
            print(f"[FETCH] Fetched {len(products)} products from Magento.")

        # Save to file instead of XCom
        with open(filename, 'w') as f:
            json.dump(products, f, default=str)  # default=str handles datetime objects
        
        print(f"[FETCH] products saved to {filename}")

        # Store only metadata in XCom
        ti.xcom_push(key="products_file", value=filename)
        ti.xcom_push(key="products_count", value=len(products))
        
        return {"products_file": filename, "products_count": len(products)}

    except Exception as e:
        print(f"Error fetching products from Magento: {str(e)}")
        raise


def fetch_product_orders(**context):
    ti = context["ti"]

    # Get the filename from upstream task
    filename = ti.xcom_pull(task_ids="fetch_products", key="products_file")
    products_count = ti.xcom_pull(task_ids="fetch_products", key="products_count")
    
    print(f"[PROCESS] Processing {products_count} orders from {filename}")
    
    # Read orders from file
    with open(filename, 'r') as f:
        products = json.load(f)

    print(f"[PROCESS] Found {len(products)} orders in {filename}")

    if not products:
        print("[ERROR] No products found in XCom pull.")
        return

    client = MagentoClient()
    product_orders = {}

    try:
        for product in products:
            sku = product.get("sku")
            if not sku:
                continue

            print(f"[FETCH] Fetching orders for product SKU: {sku}")
            orders = client.fetch_product_orders(sku)

            if orders:
                product_orders[sku] = orders
                print(f"[FETCH] Found {len(orders)} orders for product SKU: {sku}")
            else:
                print(f"[FETCH] No orders found for product SKU: {sku}")

        context["task_instance"].xcom_push(key="product_orders", value=product_orders)
        return {"product_orders": product_orders}

    except Exception as e:
        print(f"Error fetching product orders from Magento: {str(e)}")
        raise

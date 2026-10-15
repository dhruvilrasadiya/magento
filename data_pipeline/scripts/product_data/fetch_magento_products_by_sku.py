import os
import requests
from typing import Dict, List, Any, Union


class MagentoClient:
    """Simplified Magento client for global product fetching only."""

    def __init__(self):
        self.base_url = os.environ.get("MAGENTO_API_URL")
        self.token = os.environ.get("MAGENTO_API_TOKEN")

        if not self.base_url or not self.token:
            raise ValueError(
                "MAGENTO_API_URL or MAGENTO_API_TOKEN not set in environment variables."
            )

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def fetch_products(
        self, page_size: int = 100, current_page: int = 1
    ) -> Union[Dict[str, Any], None]:
        """Fetch a list of products from global Magento API using search criteria."""
        endpoint = f"{self.base_url}/rest/V1/products"
        params = {
            "searchCriteria[pageSize]": page_size,
            "searchCriteria[currentPage]": current_page,
        }
        print(f"[FETCH] Global URL: {endpoint} with params {params}")

        try:
            response = requests.get(endpoint, headers=self.get_headers(), params=params)
            response.raise_for_status()
            product_data = response.json()
            print(
                f"[INFO] Successfully fetched page {current_page} with {page_size} products."
            )
            print("++++++++++++++++++++++ :", product_data)
            return product_data
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch products: {e}")
            return {"error": str(e)}


import os
import json
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime


def fetch_magento_products_by_sku(**context):
    """
    Fetch all products from Magento using pagination, extract 'dge_id',
    and save valid product data to a JSON file. Push the file path to XCom.
    """
    ti = context["task_instance"]
    client = MagentoClient()
    page_size = 3500
    current_page = 1
    all_products = []
    invalid_values = {"", "null", "none", None}

    print("[INFO] Starting Magento product fetch...")

    while True:
        print(f"[INFO] Fetching page {current_page}")
        result = client.fetch_products(page_size=page_size, current_page=current_page)

        items = result.get("items", [])
        if not items:
            break

        all_products.extend(items)
        if len(items) < page_size:
            break

        current_page += 1

    print(f"[INFO] Total products fetched: {len(all_products)}")

    # Normalize into DataFrame
    df = pd.json_normalize(all_products)

    # Extract 'dge_id' from 'custom_attributes'
    def extract_dge_id(attrs: List[Dict[str, Any]]) -> str:
        for attr in attrs:
            if attr.get("attribute_code") == "dge_id":
                val = str(attr.get("value")).strip().lower()
                return val if val and val not in invalid_values else None
        return None

    df["dge_id"] = df["custom_attributes"].apply(extract_dge_id)

    # Save DataFrame to JSON
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    output_filename = f"magento_products_{timestamp}.json"
    output_path = os.path.join(os.getcwd(), output_filename)

    df.to_json(output_path, orient="records", indent=2)
    print(f"[INFO] Saved products to file: {output_path}")

    # Push file path to XCom
    ti.xcom_push(key="magento_products_file", value=output_path)

    return {"total_products": len(all_products), "output_file": output_path}

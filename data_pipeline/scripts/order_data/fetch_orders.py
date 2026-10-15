import os
import json
import requests
from dotenv import load_dotenv
from typing import Any, Dict, List
from datetime import datetime, timedelta
from utils.embed_utils import BaseMagentoClient

load_dotenv()


class MagentoClient(BaseMagentoClient):
    """Client for interacting with Magento API for order data."""

    def fetch_all_orders_paginated(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Fetch all orders using pagination."""
        endpoint = f"{self.base_url}/rest/V1/orders"
        current_page = 1
        all_orders = []

        while True:
            params = {
                "searchCriteria[pageSize]": page_size,
                "searchCriteria[currentPage]": current_page,
            }

            response = requests.get(endpoint, headers=self.get_headers(), params=params)
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])
            all_orders.extend(items)

            if len(items) < page_size:
                break
            current_page += 1

        return all_orders

    def fetch_orders(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch orders created between start_date and end_date."""
        endpoint = f"{self.base_url}/rest/V1/orders"
        params = {
            "searchCriteria[filterGroups][0][filters][0][field]": "created_at",
            "searchCriteria[filterGroups][0][filters][0][value]": start_date.isoformat(),
            "searchCriteria[filterGroups][0][filters][0][condition_type]": "gteq",
            "searchCriteria[filterGroups][1][filters][0][field]": "created_at",
            "searchCriteria[filterGroups][1][filters][0][value]": end_date.isoformat(),
            "searchCriteria[filterGroups][1][filters][0][condition_type]": "lteq",
        }

        response = requests.get(endpoint, headers=self.get_headers(), params=params)
        response.raise_for_status()
        return response.json().get("items", [])

    def fetch_order_by_id(self, order_id: int) -> Dict[str, Any]:
        """Fetch a single order by its ID."""
        endpoint = f"{self.base_url}/rest/V1/orders/{order_id}"
        response = requests.get(endpoint, headers=self.get_headers())
        response.raise_for_status()
        return response.json()


def fetch_magento_orders(**context):
    """Airflow task to fetch Magento orders."""
    client = MagentoClient()
    ti = context["ti"]

    # Create data directory if it doesn't exist
    data_dir = "/tmp/airflow_data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate unique filename based on run_id
    run_id = context["dag_run"].run_id
    filename = f"{data_dir}/orders_{run_id.replace(':', '_')}.json"

    # Params from DAG conf or runtime
    params = context.get("params", {})
    dag_run_conf = context.get("dag_run").conf if context.get("dag_run") else {}
    order_ids = dag_run_conf.get("order_ids", params.get("order_ids", []))
    is_initial = dag_run_conf.get("is_initial", params.get("is_initial", False))

    try:
        if order_ids:
            print(f"[FETCH] Fetching specific orders by IDs: {order_ids}")
            orders = [client.fetch_order_by_id(order_id) for order_id in order_ids]

        elif is_initial:
            print("[FETCH] Initial load: Fetching all orders via pagination.")
            orders = client.fetch_all_orders_paginated()
            orders = orders  # Limit to 10 orders for initial load (optional)

        else:
            # Fetch orders from the last day (can adjust granularity as needed)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            print(
                f"[FETCH] Incremental run: Fetching orders from {start_date} to {end_date}"
            )
            orders = client.fetch_orders(start_date, end_date)

        print(f"[FETCH] Retrieved {len(orders)} orders.")

        # Save to file instead of XCom
        with open(filename, 'w') as f:
            json.dump(orders, f, default=str)  # default=str handles datetime objects
        
        print(f"[FETCH] Orders saved to {filename}")

        # Store only metadata in XCom
        ti.xcom_push(key="orders_file", value=filename)
        ti.xcom_push(key="orders_count", value=len(orders))
        
        return {"orders_file": filename, "orders_count": len(orders)}

    except Exception as e:
        print(f"[ERROR] Failed to fetch Magento orders: {str(e)}")
        raise

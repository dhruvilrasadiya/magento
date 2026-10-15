import os
import requests
from typing import Any, Dict, List
from datetime import datetime
from utils.embed_utils import BaseMagentoClient


class CustomerClient(BaseMagentoClient):
    """Client for interacting with Magento API for customer data."""

    def fetch_customers_paginated(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Fetch all customers using pagination."""
        endpoint = f"{self.base_url}/rest/all/V1/customers/search"
        customers = []
        current_page = 1

        while True:
            params = {
                "searchCriteria[pageSize]": page_size,
                "searchCriteria[currentPage]": current_page,
            }

            response = requests.get(endpoint, headers=self.get_headers(), params=params)
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])
            customers.extend(items)

            if len(items) < page_size:
                break
            current_page += 1

        return customers

    def fetch_customers_by_date_range(
        self, start: str, end: str, page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch customers created or updated between two timestamps using searchCriteria."""
        endpoint = f"{self.base_url}/rest/all/V1/customers/search"
        customers = []
        current_page = 1

        while True:
            params = {
                "searchCriteria[filter_groups][0][filters][0][field]": "updated_at",
                "searchCriteria[filter_groups][0][filters][0][value]": start,
                "searchCriteria[filter_groups][0][filters][0][condition_type]": "from",
                "searchCriteria[filter_groups][0][filters][1][field]": "updated_at",
                "searchCriteria[filter_groups][0][filters][1][value]": end,
                "searchCriteria[filter_groups][0][filters][1][condition_type]": "to",
                "searchCriteria[pageSize]": page_size,
                "searchCriteria[currentPage]": current_page,
            }

            response = requests.get(endpoint, headers=self.get_headers(), params=params)
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])
            customers.extend(items)

            if len(items) < page_size:
                break
            current_page += 1

        return customers

    def fetch_customers(
        self, page_size: int = 10, current_page: int = 1, max_items: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch customers from Magento API."""
        endpoint = f"{self.base_url}/rest/all/V1/customers/search"
        customers = []

        while True:
            params = {
                "searchCriteria[pageSize]": page_size,
                "searchCriteria[currentPage]": current_page,
            }

            response = requests.get(endpoint, headers=self.get_headers(), params=params)
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])
            customers.extend(items)

            if len(customers) >= max_items or len(items) == 0:
                break
            current_page += 1

        return customers[:max_items]

    def fetch_customer_orders(self, customer_email: str) -> List[Dict[str, Any]]:
        """Fetch orders for a specific customer by email."""
        endpoint = f"{self.base_url}/rest/all/V1/orders"

        params = {
            "searchCriteria[filterGroups][0][filters][0][field]": "customer_email",
            "searchCriteria[filterGroups][0][filters][0][value]": customer_email,
            "searchCriteria[filterGroups][0][filters][0][conditionType]": "eq",
        }

        response = requests.get(endpoint, headers=self.get_headers(), params=params)
        response.raise_for_status()

        return response.json().get("items", [])

    def fetch_customer_cart(self, customer_email: str) -> List[Dict[str, Any]]:
        """Fetch cart information for a specific customer by email."""
        endpoint = f"{self.base_url}/rest/all/V1/carts/search"

        params = {
            "searchCriteria[filterGroups][0][filters][0][field]": "customer_email",
            "searchCriteria[filterGroups][0][filters][0][value]": customer_email,
            "searchCriteria[filterGroups][0][filters][0][conditionType]": "eq",
        }

        response = requests.get(endpoint, headers=self.get_headers(), params=params)
        response.raise_for_status()

        return response.json().get("items", [])

    def fetch_customer_invoices(self, order_id: str) -> List[Dict[str, Any]]:
        """Fetch invoices for a specific order."""
        endpoint = f"{self.base_url}/rest/all/V1/invoices"

        params = {
            "searchCriteria[filterGroups][0][filters][0][field]": "order_id",
            "searchCriteria[filterGroups][0][filters][0][value]": order_id,
            "searchCriteria[filterGroups][0][filters][0][conditionType]": "eq",
        }

        response = requests.get(endpoint, headers=self.get_headers(), params=params)
        response.raise_for_status()

        return response.json().get("items", [])


import pendulum
from typing import List, Dict, Any


def fetch_magento_customers(**context):
    is_initial = context["params"].get("is_initial", False)
    client = CustomerClient()
    ti = context["ti"]

    if is_initial:
        print("[INFO] Running in INITIAL mode — fetching all customers")
        customers = client.fetch_customers_paginated()
        # customers = customers[:100]
    else:
        execution_time = context["execution_date"]
        prev_execution_time = context.get("prev_execution_date")
        now = pendulum.instance(execution_time).to_iso8601_string()
        if not prev_execution_time:
            print("[INFO] No previous execution — fallback to full fetch")
            customers = client.fetch_customers_paginated()
        else:
            start_time = pendulum.instance(prev_execution_time).to_iso8601_string()
            customers = client.fetch_customers_by_date_range(start_time, now)

    print(f"[FETCH] Retrieved {len(customers)} customers")
    ti.xcom_push(key="customers", value={"items": customers})
    return {"customers": customers}

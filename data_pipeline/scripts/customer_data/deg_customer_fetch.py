import os
import logging
from typing import List, Dict, Any
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DGEClient:
    """Client for interacting with DGE API for customer data."""

    def __init__(self):
        self.base_url = os.environ.get("DGE_API_URL")
        self.download_url = os.environ.get("DGE_DOWNLOAD_URL")
        self.username = os.environ.get("DGE_USERNAME")
        self.password = os.environ.get("DGE_PASSWORD")
        self.auth_key = None
        self.dge_token = None
        self.uid = None

        if not self.authenticate():
            raise Exception("Primary authentication with DGE API failed")
        if not self.authenticate_dge():
            raise Exception("Secondary DGE token authentication failed")

    def authenticate(self) -> bool:
        """Authenticate with primary DGE API and set auth_key and uid."""
        endpoint = f"{self.base_url}/v1/tokens"
        headers = {"Content-Type": "application/json"}
        payload = {
            "auth": {
                "methods": "password",
                "password": {
                    "user": {"username": self.username, "password": self.password}
                },
            }
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            self.auth_key = data.get("token", {}).get("auth_key")
            self.uid = data.get("services", [{}])[0].get("UID")

            if not self.auth_key or not self.uid:
                logger.error("Missing auth_key or UID in authentication response.")
                return False

            logger.info("Primary authentication with DGE API successful.")
            return True

        except Exception as e:
            logger.error(f"Primary authentication failed: {str(e)}")
            return False

    def authenticate_dge(self) -> bool:
        """Authenticate with DGE token endpoint."""
        endpoint = f"{self.download_url}/v1/dge/v1/tokens"
        headers = self._default_headers()
        payload = {
            "username": os.environ.get("DGE_API_USERNAME"),
            "password": os.environ.get("DGE_API_PASSWORD"),
            "appKey": os.environ.get("DGE_API_APP_KEY"),
            "deviceId": "TESS",
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            self.dge_token = data.get("id", "")
            if not self.dge_token:
                logger.error("Missing DGE token in response.")
                return False

            logger.info("Secondary authentication (DGE token) successful.")
            return True

        except Exception as e:
            logger.error(f"DGE token authentication failed: {str(e)}")
            return False

    def _default_headers(self) -> Dict[str, str]:
        """Return base headers for DGE requests."""
        return {
            "x-auth-token": self.auth_key,
            "x-service-token": self.uid,
            "application-context": "TESS",
            "Content-Type": "application/json",
        }

    def _get(self, path: str) -> List[Dict[str, Any]]:
        """Helper to send GET request and return data."""
        if not self.dge_token and not self.authenticate_dge():
            raise Exception("DGE token authentication required")

        headers = self._default_headers()
        headers["x-dge-token"] = self.dge_token

        try:
            response = requests.get(f"{self.download_url}{path}", headers=headers)
            response.raise_for_status()
            print("++++++++++++++++++++++++++++ :", response.status_code)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to GET {path}: {str(e)}")
            return []

    def fetch_list_customers(self) -> List[Dict[str, Any]]:
        """Fetch list of customers from DGE API."""
        return self._get("/v1/dge/v1/parties")

    def fetch_customer_id(self, id: str) -> List[Dict[str, Any]]:
        """Fetch customer by id from DGE API."""
        customer = self._get(f"/v1/dge/v1/parties/{id}")
        return customer


def fetch_dge_customers_task(**context):
    """Airflow task to fetch customers from DGE API."""
    client = DGEClient()
    customers_list = client.fetch_list_customers()
    customers = []
    is_initial = context["params"].get("is_initial", False)
    if is_initial:
        customers_list = customers_list  # Limit to 10 customers for initial load (optional)
    for customer in customers_list:
        customer_id = customer.get("id")
        customer = client.fetch_customer_id(customer_id)
        customers.append(customer)
        logger.info(f"Fetched customer {customer_id} from DGE API")

    logger.info(f"Fetched {len(customers)} customers from DGE API")
    context["task_instance"].xcom_push(key="customers", value={"customers": customers})
    return {"customers": customers}

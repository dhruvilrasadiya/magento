import os
import logging
from typing import List, Dict, Any
import requests
import pendulum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DGEClient:
    """Client for interacting with DGE API for product data."""

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
            return {}

    def fetch_sales_orders(self) -> List[Dict[str, Any]]:
        """Fetch sales orders from DGE API."""
        return self._get("/v1/dge/v1/salesorders")

    def fetch_backorders(self) -> List[Dict[str, Any]]:
        """Fetch backorders from DGE API."""
        return self._get("/v1/dge/v1/backorders")

    def fetch_backorders_id(self, id: str) -> List[Dict[str, Any]]:
        """Fetch backorder by id from DGE API."""
        backorder = self._get(f"/v1/dge/v1/backorders/{id}")
        return backorder


# ============================
# Airflow Task Functions
# ============================


def fetch_dge_sales_orders_task(**context):
    """Airflow task to fetch sales orders from DGE API."""
    client = DGEClient()
    orders = client.fetch_sales_orders()
    logger.info(f"Fetched {len(orders)} sales orders from DGE API")
    is_initial = context["params"].get("is_initial", False)
    if is_initial:
        sales_orders = orders  # Limit to 10 orders for initial load (optional)
    else:
        execution_time = context["execution_date"]
        prev_execution_time = context.get("prev_execution_date")

        logger.info(
            f"Execution time: {execution_time}, Previous execution: {prev_execution_time}"
        )

        if not prev_execution_time:
            logger.info("[INFO] No previous execution — fallback to full fetch")
            sales_orders = sales_orders  # Optionally limit if no history
        else:
            start_time = pendulum.instance(prev_execution_time).start_of("day")
            end_time = pendulum.instance(execution_time).end_of("day")

            logger.info(f"Filtering sales orders from {start_time} to {end_time}")

            # Filter sales orders by date range
            filtered_orders = []
            for so in orders:
                so_date_str = so.get("date")
                try:
                    so_date = pendulum.parse(so_date_str)
                    if start_time <= so_date <= end_time:
                        filtered_orders.append(so)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse date '{so_date_str}' for sales order {so.get('id')}: {e}"
                    )

            sales_orders = filtered_orders

    logger.info(f"Fetched {len(sales_orders)} sales orders from DGE API")
    context["task_instance"].xcom_push(key="orders", value={"orders": sales_orders})
    return {"orders": sales_orders, "sales_orders": True}


def fetch_dge_backorders_orders_task(**context):
    """Airflow task to fetch backorders from DGE API."""
    client = DGEClient()
    backorders = client.fetch_backorders()
    orders = []
    is_initial = context["params"].get("is_initial", False)
    if is_initial:
        backorders = backorders # Limit to 10 orders for initial load (optional)
    else:
        execution_time = context["execution_date"]
        prev_execution_time = context.get("prev_execution_date")
        print()
        print(
            "++++++++++++++++++++++++++++ :\n",
            execution_time,
            " ----> ",
            prev_execution_time,
            "\n++++++++++++++++++++++++++++ :",
        )
        print()
        now = pendulum.instance(execution_time).to_iso8601_string()
        if not prev_execution_time:
            print("[INFO] No previous execution — fallback to full fetch")
            backorders = backorders  # Limit to 10 orders for initial load (optional)

        else:
            start_time = pendulum.instance(prev_execution_time).start_of("day")
            end_time = pendulum.instance(execution_time).end_of("day")

            logger.info(f"Filtering backorders from {start_time} to {end_time}")

            # Filter backorders by date range
            filtered_backorders = []
            for bo in backorders:
                bo_date_str = bo.get("date")
                try:
                    bo_date = pendulum.parse(bo_date_str)
                    if start_time <= bo_date <= end_time:
                        filtered_backorders.append(bo)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse date '{bo_date_str}' for backorder {bo.get('id')}: {e}"
                    )

            backorders = filtered_backorders

    for backorder in backorders:
        order_id = backorder.get("id")
        order = client.fetch_backorders_id(order_id)
        print("++++++++++++++++++++++++++++ :", order, type(order))
        order["totalGrossAmountWithoutVat"] = backorder.get(
            "totalGrossAmountWithoutVat"
        )
        orders.append(order)
        logger.info(f"Fetched backorder {order_id} from DGE API")

    logger.info(f"Fetched {len(orders)} backorders from DGE API")
    context["task_instance"].xcom_push(key="orders", value={"orders": orders})
    return {"orders": orders}

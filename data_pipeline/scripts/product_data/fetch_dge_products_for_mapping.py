import os
import json
import requests
import pandas as pd
import shutil
import zipfile
from typing import Dict, List, Any


class DGEClient:
    """Client for interacting with DGE API for product data."""

    def __init__(self):
        self.base_url = os.environ.get("DGE_API_URL")
        self.download_url = os.environ.get("DGE_DOWNLOAD_URL")
        self.username = os.environ.get("DGE_USERNAME")
        self.password = os.environ.get("DGE_PASSWORD")
        self.auth_key = None
        self.uid = None

    def authenticate(self) -> bool:
        """Authenticate with DGE API and get tokens."""
        endpoint = f"{self.base_url}/v1/tokens"
        headers = {"content-type": "application/json"}
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
                print("[ERROR] Failed to extract auth tokens from response")
                return False

            print(f"[AUTH] Successfully authenticated with DGE API")
            return True

        except Exception as e:
            print(f"[ERROR] Authentication failed: {str(e)}")
            return False

    def download_product_bundle(self) -> str:
        """Download product bundle ZIP file and return path to extracted directory."""
        if not self.auth_key or not self.uid:
            if not self.authenticate():
                raise Exception("Authentication required before downloading")

        endpoint = f"{self.download_url}/v1/META/bundles/PRODUCT_nl-NL_DR3-002_DEFAULT_O102265_S102265_T0.zip"
        headers = {
            "x-auth-token": self.auth_key,
            "x-service-token": self.uid,
            "application-context": "TESS",
        }

        try:
            print(f"[DOWNLOAD] Downloading product bundle from {endpoint}")

            # Use the specific path provided
            base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            product_bundle_dir = os.path.join(base_dir, "data", "product_bundle")

            # Ensure the directory exists
            os.makedirs(product_bundle_dir, exist_ok=True)
            print(f"[INFO] Using product bundle directory: {product_bundle_dir}")

            zip_path = os.path.join(product_bundle_dir, "product_bundle.zip")
            extract_dir = os.path.join(product_bundle_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)

            print(f"[INFO] Zip file will be saved to: {zip_path}")
            print(f"[INFO] Files will be extracted to: {extract_dir}")

            # Download the ZIP file
            response = requests.get(endpoint, headers=headers, stream=True)
            response.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(
                f"[INFO] Zip file downloaded, size: {os.path.getsize(zip_path)} bytes"
            )

            # Extract the ZIP file with error handling
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    file_list = zip_ref.namelist()
                    print(f"[INFO] ZIP contents: {file_list}")

                    # Extract files one by one with error handling
                    for file in file_list:
                        try:
                            zip_ref.extract(file, extract_dir)
                        except Exception as e:
                            print(f"[WARNING] Failed to extract file {file}: {str(e)}")
                            # Continue with other files
                            continue
            except zipfile.BadZipFile:
                print("[ERROR] The downloaded file is not a valid ZIP file")

                # Check if we already have extracted files from a previous run
                if os.path.exists(extract_dir) and os.listdir(extract_dir):
                    print("[INFO] Using previously extracted files")

                    # Check if index file exists
                    index_exists = False
                    for root, dirs, files in os.walk(extract_dir):
                        if "__index__.json" in files or "index.json" in files:
                            index_exists = True
                            break

                    if index_exists:
                        return extract_dir

                raise

            print(f"[INFO] Extraction complete to: {extract_dir}")

            # Check if index.json is in the root of the extracted directory
            if os.path.exists(os.path.join(extract_dir, "index.json")):
                return extract_dir

            # If not, look for it in subdirectories
            for item in os.listdir(extract_dir):
                item_path = os.path.join(extract_dir, item)
                if os.path.isdir(item_path) and os.path.exists(
                    os.path.join(item_path, "__index__.json")
                ):
                    print(f"[INFO] Found index.json in subdirectory: {item}")
                    return item_path

            # If we couldn't find index.json, return the extract directory anyway
            return extract_dir

        except Exception as e:
            print(f"[ERROR] Failed to download product bundle: {str(e)}")

            # Check if we already have extracted files from a previous run
            if os.path.exists(extract_dir) and os.listdir(extract_dir):
                print("[INFO] Using previously extracted files despite download error")
                return extract_dir

            raise

    def get_total_product_count(self) -> int:
        """Get total number of products in DGE by downloading and reading the product bundle index."""
        try:
            # Step 1: Download and extract product bundle
            extract_dir = self.download_product_bundle()
            print(f"[INFO] Product bundle extracted to: {extract_dir}")

            # Step 2: Look for index file
            index_path = None
            candidate_files = ["__index__.json", "index.json"]

            # Search in extract_dir
            for file in candidate_files:
                candidate_path = os.path.join(extract_dir, file)
                if os.path.exists(candidate_path):
                    index_path = candidate_path
                    break

            # If not found, search in subdirectories
            if not index_path:
                for root, _, files in os.walk(extract_dir):
                    for file in candidate_files:
                        if file in files:
                            index_path = os.path.join(root, file)
                            break
                    if index_path:
                        break

            if not index_path:
                print("[ERROR] Could not find index file in extracted product bundle")
                return 0

            # Step 3: Load index and count products
            with open(index_path, "r", encoding="utf-8") as f:
                index_data = json.load(f)

            if isinstance(index_data, list):
                count = len(index_data)
            elif isinstance(index_data, dict):
                # Try common patterns like "products", "items", etc.
                for key in ["products", "items", "data"]:
                    if key in index_data and isinstance(index_data[key], list):
                        count = len(index_data[key])
                        break
                else:
                    # Fallback: count top-level keys if it's a dict of SKUs
                    count = len(index_data)
            else:
                count = 0

            print(f"[INFO] Found {count} products in index")
            return count

        except Exception as e:
            print(f"[ERROR] Failed to get total product count: {str(e)}")
            return 0


def fetch_dge_products_for_mapping(**context):
    """
    Airflow task to download and extract DGE product bundle, and return the path to filtered/extracted data.
    On incremental runs, filters __index__.json based on last DAG run timestamp using the 't' field.
    """
    try:
        client = DGEClient()
        extract_dir = client.download_product_bundle()
        print(f"[FETCH] Extracted DGE product files to: {extract_dir}")

        is_initial = context["params"].get("is_initial", False)

        file_paths = {}
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if (
                    file.startswith("data_") and file.endswith(".json")
                ) or file == "__index__.json":
                    full_path = os.path.join(root, file)
                    file_paths[file] = full_path

        index_path = file_paths.get("__index__.json")
        if index_path and not is_initial:
            # Load and filter index file by last DAG run timestamp
            with open(index_path, "r", encoding="utf-8") as f:
                index_data = json.load(f)

            df = pd.DataFrame(index_data)

            # DAG execution time: current and previous
            execution_date = context["execution_date"]
            prev_execution_date = context.get(
                "prev_execution_date_success", execution_date - pd.Timedelta(days=1)
            )

            print(
                f"[FILTER] Filtering index from {prev_execution_date.isoformat()} to {execution_date.isoformat()}"
            )

            df["t"] = pd.to_datetime(df["t"])
            filtered_df = df[df["t"] > prev_execution_date]

            print(
                f"[FILTER] Filtered down to {len(filtered_df)} records from {len(df)}"
            )

            # Save filtered index back to the same path
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(filtered_df.to_dict(orient="records"), f, indent=2)

        # Push file paths to XCom for downstream tasks
        context["task_instance"].xcom_push(key="dge_files", value=file_paths)
        return {"path": extract_dir}

    except Exception as e:
        print(f"[ERROR] Failed to fetch DGE product bundle: {str(e)}")
        raise


def cleanup_product_bundle(**context):
    """Delete downloaded zip and extracted product bundle directory after DAG run."""
    try:
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        product_bundle_dir = os.path.join(base_dir, "data", "product_bundle")

        if os.path.exists(product_bundle_dir):
            print(f"[CLEANUP] Removing product bundle directory: {product_bundle_dir}")
            shutil.rmtree(product_bundle_dir)
        else:
            print(
                f"[CLEANUP] Nothing to clean. Directory does not exist: {product_bundle_dir}"
            )

    except Exception as e:
        print(f"[ERROR] Cleanup failed: {str(e)}")
        raise

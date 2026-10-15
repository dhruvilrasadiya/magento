import os
import json
import requests
import zipfile
import tempfile
from typing import Any, Dict, List
from datetime import datetime
from dotenv import load_dotenv
from utils.embed_utils import BaseMagentoClient

load_dotenv()

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
                    "user": {
                        "username": self.username,
                        "password": self.password
                    }
                }
            }
        }
        
        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            print("++++++++++++++++++++++++++++ :", data)
            
            self.auth_key = data.get("token", {}).get("auth_key")
            print("++++++++++++++++++++++++++++ :", self.auth_key)
            self.uid = data.get("services", [{}])[0].get("UID")
            print("++++++++++++++++++++++++++++ :", self.uid)
            
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
            "application-context": "TESS"
        }
        
        try:
            print(f"[DOWNLOAD] Downloading product bundle from {endpoint}")
            
            # Use the specific path provided
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[INFO] Zip file downloaded, size: {os.path.getsize(zip_path)} bytes")

            # Extract the ZIP file with error handling
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
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
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "__index__.json")):
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
    
    def process_product_data(self, extract_dir: str, max_products: int = 20) -> List[Dict[str, Any]]:
        """Process extracted product data files and return list of products.
        
        Args:
            extract_dir: Path to the directory containing extracted product data
            max_products: Maximum number of products to process (default: 20)
        
        Returns:
            List of processed product data dictionaries
        """
        try:
            # Add debugging to check the actual path and directory contents
            print(f"[DEBUG] Extract directory path: {extract_dir}")
            print(f"[DEBUG] Directory exists: {os.path.exists(extract_dir)}")
            
            if os.path.exists(extract_dir):
                print(f"[DEBUG] Contents of extract directory: {os.listdir(extract_dir)}")
                
                # Check subdirectories if they exist
                for item in os.listdir(extract_dir):
                    item_path = os.path.join(extract_dir, item)
                    if os.path.isdir(item_path):
                        print(f"[DEBUG] Contents of subdirectory {item}: {os.listdir(item_path)}")
            
            # Look for index.json or __index__.json
            index_path = None
            possible_index_files = ["index.json", "__index__.json"]
            
            for index_file in possible_index_files:
                possible_path = os.path.join(extract_dir, index_file)
                if os.path.exists(possible_path):
                    index_path = possible_path
                    print(f"[INFO] Found index file at: {index_path}")
                    break
            
            # If not found in root, search in subdirectories
            if not index_path:
                for root, dirs, files in os.walk(extract_dir):
                    for index_file in possible_index_files:
                        if index_file in files:
                            index_path = os.path.join(root, index_file)
                            print(f"[INFO] Found index file at: {index_path}")
                            break
                    if index_path:
                        break
            
            if not index_path:
                raise FileNotFoundError(f"Could not find index.json in {extract_dir} or its subdirectories")
            
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            print(f"[DEBUG] Index data type: {type(index_data)}")
            
            products = []
            data_files = {}
            
            # Handle both list and dictionary formats
            product_list = []
            if isinstance(index_data, list):
                product_list = index_data
            elif isinstance(index_data, dict) and "products" in index_data:
                product_list = index_data.get("products", [])
            else:
                print(f"[WARNING] Unexpected index data format: {type(index_data)}")
                print(f"[DEBUG] Index data sample: {str(index_data)[:500]}...")
            
            # Limit the number of products to process
            product_list = product_list[:max_products]
            print(f"[INFO] Processing up to {max_products} products from index")
            
            # Process each product in the index
            for product_meta in product_list:
                file_name = product_meta.get("file")
                if not file_name:
                    print(f"[WARNING] No file name for product: {product_meta}")
                    continue
                
                # Load data file if not already loaded
                if file_name not in data_files:
                    data_path = os.path.join(os.path.dirname(index_path), file_name)
                    print(f"[INFO] Loading data file: {data_path}")
                    
                    if not os.path.exists(data_path):
                        print(f"[WARNING] Data file not found: {data_path}")
                        continue
                        
                    with open(data_path, 'r', encoding='utf-8') as f:
                        data_file_content = json.load(f)
                        
                        # Handle the case where data is under a "PRODUCT" key
                        if isinstance(data_file_content, dict) and "PRODUCT" in data_file_content:
                            data_files[file_name] = data_file_content["PRODUCT"]
                            print(f"[INFO] Found products under 'PRODUCT' key in {file_name}")
                        else:
                            data_files[file_name] = data_file_content
            
                # Get product data from the appropriate data file
                product_id = product_meta.get("i")  # ID in the index file
                
                # Handle both list and dictionary formats for data files
                product_data = None
                if isinstance(data_files[file_name], list):
                    # Look for product by productcode in the basic section
                    product_data = next(
                        (p for p in data_files[file_name] if p.get("basic", {}).get("productcode") == product_id), 
                        None
                    )
                    
                    # If not found by productcode, try to find by index if available
                    if not product_data and "idx" in product_meta:
                        idx = product_meta.get("idx")
                        if isinstance(idx, int) and 0 <= idx < len(data_files[file_name]):
                            product_data = data_files[file_name][idx]
                            print(f"[INFO] Found product with ID {product_id} by index {idx}")
            
                if product_data:
                    # Add metadata from index to the product data
                    product_data["fetched_store_key"] = "dge"
                    product_data["website_id"] = 10  # Assign a unique website ID for DGE
                    
                    # Map fields from index to product data if they don't exist
                    for key, value in product_meta.items():
                        if key not in product_data and key != "file" and key != "idx":
                            product_data[key] = value
                    
                    # Ensure we have a SKU
                    if "sku" not in product_data:
                        # Try to use EAN as SKU, or product ID if EAN is not available
                        ean = product_meta.get("ean")
                        if ean:
                            product_data["sku"] = ean
                        else:
                            product_data["sku"] = str(product_id)
                    
                    products.append(product_data)
                    print(f"[INFO] Added product with ID {product_id} to results")
                else:
                    print(f"[WARNING] Could not find product with ID {product_id} in file {file_name}")
            
            print(f"[PROCESS] Processed {len(products)} products from DGE API")
            return products
            
        except Exception as e:
            print(f"[ERROR] Failed to process product data: {str(e)}")
            raise


def fetch_dge_products(**context):
    """Airflow task to fetch products from DGE API."""
    client = DGEClient()
    max_products = context["params"].get("max_products", 20)  # Default to 20 if not specified
    
    try:
        # Download and extract product bundle
        extract_dir = client.download_product_bundle()
        
        # Process product data (limit to max_products)
        products = client.process_product_data(extract_dir, max_products=max_products)
        
        print(f"[FETCH] Fetched {len(products)} products from DGE API")
        
        # Store the results for the next task
        context["task_instance"].xcom_push(key="products", value={"products": products})
        
        return {"products": products}
        
    except Exception as e:
        print(f"Error fetching products from DGE API: {str(e)}")
        raise













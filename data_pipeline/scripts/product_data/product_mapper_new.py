import json
import uuid
import os
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from langchain_core.documents import Document
from utils.embed_utils import embed_and_upsert_products


class ProductDataManager:
    """
    Manages product data from multiple JSON files using pandas DataFrames.
    Provides access to all product data for mapping and processing.
    """

    def __init__(self):
        self.dge_dataframes = {}  # file_name -> DataFrame
        self.magento_dataframes = {}  # store_key -> DataFrame
        self.index_data = []  # Index data from __index__.json
        self.file_paths = {}  # file_name -> full_path mapping

    def load_data_from_xcom(self, task_instance):
        """Load all data from XCom pulls and create DataFrames"""
        print("[INFO] Loading data from XCom...")

        # # Get file paths from XCom
        # file_paths_data = task_instance.xcom_pull(task_ids="get_file_paths")
        # if not file_paths_data:
        #     raise ValueError("No file paths found in XCom")

        # self.file_paths = file_paths_data
        # print(f"[INFO] Found {len(self.file_paths)} data files")

        # Load index data
        self._load_index_data(task_instance)

        # Load DGE data files
        self._load_dge_dataframes(task_instance)

        # Load Magento data
        self._load_magento_dataframes(task_instance)

        print("[INFO] All data loaded successfully")

    def _load_index_data(self, task_instance):
        try:
            file_paths = task_instance.xcom_pull(
                task_ids="fetch_dge_products", key="dge_files"
            )
            index_path = file_paths.get("__index__.json")

            if not index_path or not os.path.exists(index_path):
                print("[ERROR] __index__.json not found in DGE bundle")
                return

            with open(index_path, "r") as f:
                self.index_data = json.load(f)
                print(f"[INFO] Loaded {len(self.index_data)} index entries")

        except Exception as e:
            print(f"[ERROR] Failed to load index data: {e}")

    def _load_dge_dataframes(self, task_instance):
        try:
            file_paths = task_instance.xcom_pull(
                task_ids="fetch_dge_products", key="dge_files"
            )

            for file_name, file_path in file_paths.items():
                if (
                    file_name.startswith("data_")
                    and file_name.endswith(".json")
                    and os.path.exists(file_path)
                ):
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        df = pd.DataFrame(data)
                        self.dge_dataframes[file_name] = df
                        print(f"[INFO] Loaded {len(df)} products from {file_name}")

        except Exception as e:
            print(f"[ERROR] Failed to load DGE data files: {e}")

    def _load_magento_dataframes(self, task_instance):
        try:
            magento_path = task_instance.xcom_pull(
                task_ids="fetch_magento_products", key="magento_products_file"
            )
            if not magento_path or not os.path.exists(magento_path):
                print("[ERROR] Magento product file not found.")
                return

            with open(magento_path, "r") as f:
                products = json.load(f)

            store_groups = {}
            for product in products:
                store_key = product.get("fetched_store_key", "global")
                store_groups.setdefault(store_key, []).append(product)

            for store_key, store_products in store_groups.items():
                df = pd.DataFrame(store_products)
                self.magento_dataframes[store_key] = df
                print(
                    f"[INFO] Loaded {len(df)} Magento products for store: {store_key}"
                )

        except Exception as e:
            print(f"[ERROR] Failed to load Magento data: {e}")

    def get_dge_product_by_index(
        self, file_name: str, index: int
    ) -> Optional[Dict[str, Any]]:
        """Get a specific DGE product by file and index"""
        if file_name not in self.dge_dataframes:
            return None

        df = self.dge_dataframes[file_name]
        if index >= len(df):
            return None

        return df.iloc[index].to_dict()

    def get_dge_product_by_id(
        self, product_id: str
    ) -> Optional[Tuple[Dict[str, Any], str, int]]:
        """
        Get a DGE product by ID from index data.
        Returns (product_data, file_name, index) or None
        """
        # Find in index data
        for index_entry in self.index_data:
            if str(index_entry.get("i")) == str(product_id):
                file_name = index_entry.get("file")
                idx = index_entry.get("idx")

                if file_name and idx is not None:
                    product_data = self.get_dge_product_by_index(file_name, idx)
                    if product_data:
                        return product_data, file_name, idx

        return None

    def get_all_magento_products(self) -> List[Dict[str, Any]]:
        """Get all Magento products from all stores"""
        all_products = []
        for store_key, df in self.magento_dataframes.items():
            products = df.to_dict("records")
            all_products.extend(products)
        return all_products

    def get_index_entries_by_file(self, file_name: str) -> List[Dict[str, Any]]:
        """Get all index entries for a specific file"""
        return [entry for entry in self.index_data if entry.get("file") == file_name]

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded data"""
        return {
            "dge_files": len(self.dge_dataframes),
            "dge_total_products": sum(len(df) for df in self.dge_dataframes.values()),
            "magento_stores": len(self.magento_dataframes),
            "magento_total_products": sum(
                len(df) for df in self.magento_dataframes.values()
            ),
            "index_entries": len(self.index_data),
        }


def extract_dge_id_from_magento_product(product: Dict[str, Any]) -> Optional[str]:
    """Extract the DGE ID from a Magento product's custom attributes."""
    custom_attributes = product.get("custom_attributes", [])
    for attr in custom_attributes:
        if attr.get("attribute_code") == "dge_id" and attr.get("value"):
            return str(attr.get("value"))
    return None


def merge_product_metadata(
    magento_metadata: Dict[str, Any], dge_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge metadata from Magento and DGE products."""
    merged_metadata = {
        # Core fields from Magento
        "sku": magento_metadata.get("sku"),
        "id": magento_metadata.get("id"),
        "name": magento_metadata.get("name"),
        "type_id": magento_metadata.get("type_id"),
        "status": magento_metadata.get("status"),
        "visibility": magento_metadata.get("visibility"),
        "price": magento_metadata.get("price"),
        "website_id": magento_metadata.get("website_id"),
        # Add DGE identifiers
        "dge_id": magento_metadata.get("dge_id"),
        "dge_name": dge_metadata.get("name"),
        "dge_description": dge_metadata.get("description"),
        "dge_productcode": dge_metadata.get("productcode"),
        # Source tracking
        "magento_store_key": magento_metadata.get("fetched_store_key"),
        "dge_store_key": dge_metadata.get("fetched_store_key", "dge"),
        "dge_file": dge_metadata.get("file"),
        "dge_index": dge_metadata.get("index"),
        # Flag to indicate this is a merged product
        "is_merged": True,
        "source": "merged",
    }

    return merged_metadata


def create_magento_product_documents(
    product: dict, metadata_base: dict, source: str
) -> List[Document]:
    """Create documents for Magento product data"""
    documents = []

    sku = metadata_base.get("sku", "")
    website_id = metadata_base.get("website_id", 0)
    name = product.get("name", "")

    # 1. Name document
    doc_uuid = str(uuid.uuid4())
    documents.append(
        Document(
            page_content=f"Product name: {name}",
            metadata={
                **metadata_base,
                "type": "name",
                "source": source,
                "doc_id": doc_uuid,
            },
        )
    )

    # 2. Description from custom_attributes
    description = None
    for attr in product.get("custom_attributes", []):
        if attr.get("attribute_code") == "description":
            description = attr.get("value")
            break
    doc_uuid = str(uuid.uuid4())
    documents.append(
        Document(
            page_content=f"Product description: {description or 'No description available'}",
            metadata={
                **metadata_base,
                "type": "description",
                "source": source,
                "doc_id": doc_uuid,
            },
        )
    )

    # 3. Price document
    price = product.get("price")
    doc_uuid = str(uuid.uuid4())
    documents.append(
        Document(
            page_content=f"Price for SKU {sku} is {price if price is not None else 'N/A'} for website_id {website_id}",
            metadata={
                **metadata_base,
                "type": "pricing",
                "source": source,
                "doc_id": doc_uuid,
            },
        )
    )

    # 4. Brand document
    brand = None
    for attr in product.get("custom_attributes", []):
        if attr.get("attribute_code") == "brand":
            brand = attr.get("value")
            break
    doc_uuid = str(uuid.uuid4())
    documents.append(
        Document(
            page_content=f"Brand for SKU {sku} is {brand or 'Not specified'}",
            metadata={
                **metadata_base,
                "type": "brand",
                "source": source,
                "doc_id": doc_uuid,
            },
        )
    )

    # 5. Category document
    categories = product.get("category_ids", [])
    doc_uuid = str(uuid.uuid4())
    documents.append(
        Document(
            page_content=f"Product SKU {sku} belongs to categories: {categories if categories else 'None'}",
            metadata={
                **metadata_base,
                "type": "category",
                "source": source,
                "doc_id": doc_uuid,
            },
        )
    )

    # 6. Summary document
    summary = {"sku": sku, "name": name, "source": source}
    if price is not None:
        summary["price"] = price
    doc_uuid = str(uuid.uuid4())
    documents.append(
        Document(
            page_content=f"Product summary: {json.dumps(summary, indent=2)}",
            metadata={
                **metadata_base,
                "type": "summary",
                "source": source,
                "doc_id": doc_uuid,
            },
        )
    )

    return documents


def create_dge_product_documents(
    product: dict, metadata_base: dict, source: str
) -> List[Document]:
    """Create documents for DGE product data"""
    documents = []

    # 1. Basic info document
    basic_info = product.get("basic", {})
    if basic_info:
        doc_uuid = str(uuid.uuid4())
        documents.append(
            Document(
                page_content=f"DGE Basic Info: {json.dumps(basic_info, indent=2)}",
                metadata={
                    **metadata_base,
                    "type": "basic",
                    "doc_id": doc_uuid,
                    "source": source,
                },
            )
        )

    # 2. Unit document
    unit_info = product.get("unit", {})
    if unit_info:
        doc_uuid = str(uuid.uuid4())
        documents.append(
            Document(
                page_content=f"DGE Unit Info: {json.dumps(unit_info, indent=2)}",
                metadata={
                    **metadata_base,
                    "type": "unit",
                    "doc_id": doc_uuid,
                    "source": source,
                },
            )
        )

    # 3. Price document
    price_info = product.get("price", {})
    if price_info:
        doc_uuid = str(uuid.uuid4())
        documents.append(
            Document(
                page_content=f"DGE Price Info: {json.dumps(price_info, indent=2)}",
                metadata={
                    **metadata_base,
                    "type": "dge_price",
                    "doc_id": doc_uuid,
                    "source": source,
                },
            )
        )

    # 4. Logistics document
    logistics_info = product.get("logistics", {})
    if logistics_info:
        doc_uuid = str(uuid.uuid4())
        documents.append(
            Document(
                page_content=f"DGE Logistics Info: {json.dumps(logistics_info, indent=2)}",
                metadata={
                    **metadata_base,
                    "type": "logistics",
                    "doc_id": doc_uuid,
                    "source": source,
                },
            )
        )

    # 5. Full product document (searchable)
    doc_uuid = str(uuid.uuid4())
    documents.append(
        Document(
            page_content=f"DGE Product: {json.dumps(product, indent=2)}",
            metadata={
                **metadata_base,
                "type": "full_product",
                "doc_id": doc_uuid,
                "source": source,
            },
        )
    )

    return documents


def create_index_based_dge_document(
    index_entry: dict, product_data: dict, metadata_base: dict
) -> List[Document]:
    """Create documents based on index entry structure"""
    documents = []

    # Create a comprehensive document with index and product data
    doc_uuid = str(uuid.uuid4())

    # Combine index entry data with product data for search
    combined_content = {
        "id": index_entry.get("i"),
        "description": index_entry.get("d"),
        "ean": index_entry.get("ean"),
        "manufacturer_code": index_entry.get("mc"),
        "supplier_code": index_entry.get("supc"),
        "status": index_entry.get("st"),
        "supplier_id": index_entry.get("sup"),
        "product_data": product_data,
    }

    documents.append(
        Document(
            page_content=f"DGE Product Index: {json.dumps(combined_content, indent=2)}",
            metadata={
                **metadata_base,
                "type": "index_product",
                "doc_id": doc_uuid,
                "source": "dge_index",
                "dge_id": index_entry.get("i"),
                "ean": index_entry.get("ean"),
                "manufacturer_code": index_entry.get("mc"),
                "supplier_code": index_entry.get("supc"),
                "status": index_entry.get("st"),
            },
        )
    )

    return documents


def process_dge_products_from_index(data_manager: ProductDataManager) -> List[Document]:
    """Process all DGE products using index data"""
    all_docs = []
    processed_count = 0

    print(
        f"[INFO] Processing {len(data_manager.index_data)} DGE products from index..."
    )

    for index_entry in data_manager.index_data:  # Limit to first 100
        product_id = index_entry.get("i")
        file_name = index_entry.get("file")
        idx = index_entry.get("idx")

        if not all([product_id, file_name, idx is not None]):
            continue

        # Get product data from DataFrame
        product_data = data_manager.get_dge_product_by_index(file_name, idx)
        if not product_data:
            continue

        # Create metadata
        metadata_base = {
            "dge_id": product_id,
            "description": index_entry.get("d", ""),
            "ean": index_entry.get("ean", ""),
            "manufacturer_code": index_entry.get("mc", ""),
            "supplier_code": index_entry.get("supc", ""),
            "file": file_name,
            "index": idx,
            "source": "dge",
        }

        # Create documents
        docs = create_index_based_dge_document(index_entry, product_data, metadata_base)
        all_docs.extend(docs)
        processed_count += 1

        if processed_count % 100 == 0:
            print(f"[INFO] Processed {processed_count} DGE products...")

    print(f"[INFO] Successfully processed {processed_count} DGE products")
    return all_docs


def map_and_merge_products(**context):
    """
    Main function to map and merge products using the new DataFrame approach.
    """
    ti = context["task_instance"]

    # Initialize data manager
    data_manager = ProductDataManager()

    try:
        # Load all data from XCom
        data_manager.load_data_from_xcom(ti)

        # Print statistics
        stats = data_manager.get_stats()
        print(f"[INFO] Data loaded - {stats}")

        all_docs = []
        all_doc_log = {}

        # Step 1: Process DGE products from index
        print("[STEP 1] Processing DGE products from index...")
        dge_docs = process_dge_products_from_index(data_manager)
        all_docs.extend(dge_docs)

        # Log DGE documents
        for doc in dge_docs:
            dge_id = doc.metadata.get("dge_id")
            doc_type = doc.metadata.get("type")
            doc_id = doc.metadata.get("doc_id")

            if dge_id:
                key = f"dge_{dge_id}"
                if key not in all_doc_log:
                    all_doc_log[key] = {}
                all_doc_log[key].setdefault(doc_type, []).append(doc_id)

        # Step 2: Process Magento products and create merged documents
        print("[STEP 2] Processing Magento products and creating merged documents...")

        magento_products = data_manager.get_all_magento_products()
        matched_count = 0

        for magento_product in magento_products:
            sku = magento_product.get("sku", "")
            if not sku:
                continue

            # Extract DGE ID
            dge_id = extract_dge_id_from_magento_product(magento_product)
            if not dge_id:
                continue

            # Find matching DGE product using data manager
            dge_result = data_manager.get_dge_product_by_id(dge_id)
            if not dge_result:
                print(
                    f"[INFO] No matching DGE product found for ID: {dge_id} (SKU: {sku})"
                )
                continue

            dge_product, dge_file, dge_index = dge_result

            # Create metadata
            magento_metadata = {
                "sku": sku,
                "id": magento_product.get("id"),
                "name": magento_product.get("name"),
                "type_id": magento_product.get("type_id"),
                "status": magento_product.get("status"),
                "visibility": magento_product.get("visibility"),
                "price": magento_product.get("price"),
                "fetched_store_key": magento_product.get("fetched_store_key", "global"),
                "website_id": magento_product.get("website_id", 0),
                "dge_id": dge_id,
                "source": "magento",
            }

            # Find corresponding index entry
            index_entry = None
            for entry in data_manager.index_data:
                if str(entry.get("i")) == str(dge_id):
                    index_entry = entry
                    break

            dge_metadata = {
                "dge_id": dge_id,
                "name": index_entry.get("d", "") if index_entry else "",
                "description": index_entry.get("d", "") if index_entry else "",
                "productcode": dge_id,
                "file": dge_file,
                "index": dge_index,
                "source": "dge",
            }

            merged_metadata = merge_product_metadata(magento_metadata, dge_metadata)

            # Create documents
            magento_docs = create_magento_product_documents(
                magento_product, magento_metadata, "magento"
            )
            dge_docs = create_dge_product_documents(dge_product, dge_metadata, "dge")

            # Create merged document
            doc_uuid = str(uuid.uuid4())
            merged_doc = Document(
                page_content=f"Merged product: {magento_metadata.get('name')} (SKU: {sku}) mapped to DGE product {dge_metadata.get('description')} (ID: {dge_id})",
                metadata={**merged_metadata, "type": "merged", "doc_id": doc_uuid},
            )

            docs = magento_docs + dge_docs + [merged_doc]
            all_docs.extend(docs)

            # Log documents
            doc_log = {}
            for doc in docs:
                doc_type = doc.metadata.get("type")
                doc_id = doc.metadata.get("doc_id")
                doc_log.setdefault(doc_type, []).append(doc_id)

            all_doc_log[f"merged_{sku}"] = doc_log
            matched_count += 1

            if matched_count % 50 == 0:
                print(f"[INFO] Processed {matched_count} merged products...")

        print(f"[INFO] Successfully mapped {matched_count} Magento products to DGE")

        if not all_docs:
            print("[WARNING] No documents to embed.")
            return False

        print(f"[INFO] Embedding {len(all_docs)} documents...")
        result = embed_and_upsert_products(all_docs, all_doc_log, is_stock_info=False)

        if result:
            print(
                f"[SUCCESS] Successfully embedded all products. Total documents: {len(all_docs)}"
            )
            return True
        else:
            print(f"[ERROR] Embedding failed.")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to process products: {e}")
        import traceback

        traceback.print_exc()
        return False

import os
import json
import requests
import argparse
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

# Load environment variables
load_dotenv() 

class MagentoClient:
    """Client for interacting with Magento API to fetch products with dge_id."""
    
    def __init__(self, base_url=None, token=None):
        self.base_url = base_url or os.environ.get("MAGENTO_API_URL")
        self.token = token or os.environ.get("MAGENTO_API_TOKEN")
        
        if not self.base_url or not self.token:
            raise ValueError("Magento API URL and token must be provided")
    
    def get_headers(self):
        """Get headers for Magento API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def fetch_all_products(self, page_size=100) -> List[Dict[str, Any]]:
        """Fetch all products from Magento API."""
        all_products = []
        current_page = 1
        
        print(f"[INFO] Starting to fetch products from Magento API")
        print(f"[INFO] Base URL: {self.base_url}")
        
        while True:
            endpoint = f"{self.base_url.rstrip('/')}/rest/all/V1/products"
            params = {
                "searchCriteria[pageSize]": page_size,
                "searchCriteria[currentPage]": current_page,
            }
            
            try:
                print(f"[FETCH] Requesting page {current_page} with page size {page_size}")
                response = requests.get(endpoint, headers=self.get_headers(), params=params)
                response.raise_for_status()
                data = response.json()
                
                items = data.get("items", [])
                total_count = data.get("total_count", 0)
                
                if not items:
                    print(f"[INFO] No more products found on page {current_page}")
                    break
                
                print(f"[INFO] Retrieved {len(items)} products from page {current_page}")
                all_products.extend(items)
                
                print(f"[PROGRESS] Fetched {len(all_products)}/{total_count} products ({(len(all_products)/total_count*100):.2f}%)")
                
                current_page += 1
                
            except requests.RequestException as e:
                print(f"[ERROR] Failed to fetch products from page {current_page}: {str(e)}")
                break
        
        print(f"[COMPLETE] Fetched a total of {len(all_products)} products")
        return all_products
    
    def count_products_with_dge_id(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Count products with valid dge_id custom attribute."""
        products_with_dge_id = []
        products_with_empty_dge_id = []
        products_without_dge_id = []
        
        # List of values considered as empty/invalid
        invalid_values = ["na", "n/a", "#n/a", "", "null", "none", "#na", "#n/a"]
        
        for product in products:
            sku = product.get("sku", "unknown")
            custom_attributes = product.get("custom_attributes", [])
            
            dge_id_attr = None
            for attr in custom_attributes:
                if attr.get("attribute_code") == "dge_id":
                    dge_id_attr = attr
                    break
            
            if dge_id_attr:
                dge_id_value = dge_id_attr.get("value")
                if dge_id_value and str(dge_id_value).lower() not in invalid_values:
                    products_with_dge_id.append({
                        "sku": sku,
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "dge_id": dge_id_value
                    })
                else:
                    products_with_empty_dge_id.append({
                        "sku": sku,
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "dge_id": dge_id_value
                    })
            else:
                products_without_dge_id.append({
                    "sku": sku,
                    "id": product.get("id"),
                    "name": product.get("name")
                })
        
        return {
            "total_products": len(products),
            "products_with_dge_id_count": len(products_with_dge_id),
            "products_with_empty_dge_id_count": len(products_with_empty_dge_id),
            "products_without_dge_id_count": len(products_without_dge_id),
            "products_with_dge_id": products_with_dge_id,
            "products_with_empty_dge_id": products_with_empty_dge_id,
            "products_without_dge_id": products_without_dge_id
        }

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Count Magento products with dge_id custom attribute")
    parser.add_argument("--url", help="Magento API base URL")
    parser.add_argument("--token", help="Magento API token")
    parser.add_argument("--output", help="Output file path for detailed results", default="magento_dge_id_analysis.json")
    parser.add_argument("--page-size", type=int, help="Page size for API requests", default=100)
    parser.add_argument("--sample-size", type=int, help="Number of sample products to display", default=100)
    args = parser.parse_args()
    
    try:
        # Initialize client
        client = MagentoClient(base_url=args.url, token=args.token)
        
        # Fetch all products
        print("[START] Fetching all products from Magento API")
        all_products = client.fetch_all_products(page_size=args.page_size)
        
        # Count products with dge_id
        print("[ANALYZE] Analyzing products for dge_id attribute")
        results = client.count_products_with_dge_id(all_products)
        
        # Print summary
        print("\n===== SUMMARY =====")
        print(f"Total products: {results['total_products']}")
        print(f"Products with valid dge_id: {results['products_with_dge_id_count']} ({results['products_with_dge_id_count']/results['total_products']*100:.2f}%)")
        print(f"Products with empty dge_id: {results['products_with_empty_dge_id_count']} ({results['products_with_empty_dge_id_count']/results['total_products']*100:.2f}%)")
        print(f"Products without dge_id attribute: {results['products_without_dge_id_count']} ({results['products_without_dge_id_count']/results['total_products']*100:.2f}%)")
        
        # Save detailed results to file
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n[COMPLETE] Detailed results saved to {args.output}")
        
        # Print sample of products with dge_id
        sample_size = min(args.sample_size, len(results['products_with_dge_id']))
        if results['products_with_dge_id']:
            print(f"\n===== {sample_size} PRODUCTS WITH VALID DGE_ID =====")
            for i, product in enumerate(results['products_with_dge_id'][:sample_size]):
                print(f"{i+1}. SKU: {product['sku']}")
        
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()






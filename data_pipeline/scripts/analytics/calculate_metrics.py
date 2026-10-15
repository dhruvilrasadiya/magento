
import uuid
import json
from datetime import datetime
from langchain_core.documents import Document
from .analyze_metrics import (
    analyze_magento_orders,
    generate_product_insights,
    generate_customer_insights,
)
from utils.analytics_utils import embed_and_upsert_insights


def calculate_order_metrics(**context):
    """Calculate order-related metrics from order data passed via context."""
    print("[INFO] Calculating order metrics")

    # 1. Get orders from XCom
    task_instance = context["task_instance"]

    filename = task_instance.xcom_pull(task_ids="fetch_orders", key="orders_file")
    orders_count = task_instance.xcom_pull(task_ids="fetch_orders", key="orders_count")
    print(f"[PROCESS] Processing {orders_count} orders from {filename}")

    with open(filename, 'r') as f:
        orders_data = json.load(f)

    if not orders_data:
        print("[WARNING] No order data found in context")
        return False

    # 2. Run insight analysis
    insights = analyze_magento_orders(orders_data)

    if not insights:
        print("[WARNING] No Insights generated")
        return False

    print("[INFO] Insights generated successfully")

    # 3. Prepare for Qdrant insertion
    analytics_docs = []
    doc_logs = {}

    current_time = datetime.utcnow().isoformat()
    insight_type = "order_insights"

    for section_name, insight_text in insights.items():
        doc_uuid = str(uuid.uuid4())
        doc = Document(
            page_content=insight_text,
            metadata={
                "type": "analytics",
                "metric_type": section_name,
                "time_granularity": "all_time",
                "insight_type": insight_type,
                "doc_id": doc_uuid,
                "generated_at": current_time,
            },
        )
        analytics_docs.append(doc)
        doc_logs[section_name] = [doc_uuid]

    # 4. Embed and upsert to Qdrant + MongoDB
    try:
        embed_and_upsert_insights(
            docs=analytics_docs,
            all_doc_log=doc_logs,
            insight_type=insight_type,
            time_id=current_time,
            collection_name="analysis_data",
        )
        print(
            f"[INFO] Documents successfully embedded and upserted for time_id: {current_time}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to embed and upsert insights: {e}")
        return False

    return True


def calculate_product_metrics(**context):
    """Calculate product-related insights from product data passed via context."""
    print("[INFO] Calculating product insights")

    # 1. Get product data from XCom
    task_instance = context["task_instance"]

    # Get the filename from upstream task
    filename = task_instance.xcom_pull(task_ids="fetch_products", key="products_file")
    products_count = task_instance.xcom_pull(task_ids="fetch_products", key="products_count")
    print(f"[PROCESS] Processing {products_count} products from {filename}")
    with open(filename, 'r') as f:
        product_data = json.load(f)

    if not product_data:
        print("[WARNING] No product data found in context")
        return False
    print("++++++++++++++++++++++")
    print("product data :", product_data)
    print("++++++++++++++++++++++")

    # 2. Run product insight analysis
    insights = generate_product_insights(product_data["products"], product_data["total_count"])

    print("---" * 30)
    print(f"[INFO] Product insights: {insights}")
    print("---" * 30)

    if not insights:
        print("[WARNING] No Product Insights generated")
        return False

    print("[INFO] Product insights generated successfully")

    # 3. Prepare documents for Qdrant insertion
    analytics_docs = []
    doc_logs = {}

    current_time = datetime.utcnow().isoformat()
    insight_type = "product_insights"

    for section_name, insight_text in insights.items():
        doc_uuid = str(uuid.uuid4())
        doc = Document(
            page_content=insight_text,
            metadata={
                "type": "analytics",
                "metric_type": section_name,
                "time_granularity": "all_time",
                "insight_type": insight_type,
                "doc_id": doc_uuid,
                "generated_at": current_time,
            },
        )
        analytics_docs.append(doc)
        doc_logs[section_name] = [doc_uuid]

    # 4. Embed and upsert into Qdrant and MongoDB
    try:
        embed_and_upsert_insights(
            docs=analytics_docs,
            all_doc_log=doc_logs,
            insight_type=insight_type,
            time_id=current_time,
            collection_name="analysis_data",
        )
        print(
            f"[INFO] Product documents successfully embedded and upserted for time_id: {current_time}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to embed and upsert product insights: {e}")
        return False

    return True


def calculate_customer_metrics(**context):
    """Calculate customer-related insights from customer data passed via context."""
    print("[INFO] Calculating customer insights")

    # 1. Get customer data from XCom
    task_instance = context["task_instance"]
    customer_data = task_instance.xcom_pull(task_ids="fetch_customers", key="customers")

    if not customer_data:
        print("[WARNING] No customer data found in context")
        return False

    # 2. Run customer insight analysis
    insights = generate_customer_insights(customer_data["items"])

    print("---" * 30)
    print(f"[INFO] Customer insights: {insights}")
    print("---" * 30)

    if not insights:
        print("[WARNING] No Customer Insights generated")
        return False

    print("[INFO] Customer insights generated successfully")

    # 3. Prepare documents for Qdrant insertion
    analytics_docs = []
    doc_logs = {}

    current_time = datetime.utcnow().isoformat()
    insight_type = "customer_insights"

    for section_name, insight_text in insights.items():
        doc_uuid = str(uuid.uuid4())
        doc = Document(
            page_content=insight_text,
            metadata={
                "type": "analytics",
                "metric_type": section_name,
                "time_granularity": "all_time",
                "insight_type": insight_type,
                "doc_id": doc_uuid,
                "generated_at": current_time,
            },
        )
        analytics_docs.append(doc)
        doc_logs[section_name] = [doc_uuid]

    # 4. Embed and upsert into Qdrant and MongoDB
    try:
        embed_and_upsert_insights(
            docs=analytics_docs,
            all_doc_log=doc_logs,
            insight_type=insight_type,
            time_id=current_time,
            collection_name="analysis_data",
        )
        print(
            f"[INFO] Customer documents successfully embedded and upserted for time_id: {current_time}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to embed and upsert customer insights: {e}")
        return False

    return True

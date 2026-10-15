from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from scripts.order_data.fetch_orders import fetch_magento_orders
from scripts.product_data.fetch_products import fetch_magento_products
from scripts.customer_data.fetch_customers import fetch_magento_customers
from scripts.analytics.calculate_metrics import (
    calculate_order_metrics,
    calculate_product_metrics,
    calculate_customer_metrics,
)
from scripts.clean_up import cleanup_files

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="analytics_pipeline",
    default_args=default_args,
    start_date=datetime(2025, 5, 14, 0, 0),
    schedule_interval="@daily",
    catchup=False,
    tags=["analytics", "insights"],
)

# Fetch orders directly instead of waiting
fetch_orders_task = PythonOperator(
    task_id="fetch_orders",
    python_callable=fetch_magento_orders,
    provide_context=True,
    params={"is_initial": True},
    dag=dag,
)

# Fetch products directly
fetch_products_task = PythonOperator(
    task_id="fetch_products",
    python_callable=fetch_magento_products,
    provide_context=True,
    params={"is_initial": True},
    dag=dag,
)


# Fetch customers directly
fetch_customers_task = PythonOperator(
    task_id="fetch_customers",
    python_callable=fetch_magento_customers,
    provide_context=True,
    dag=dag,
)


# Calculate order metrics
calculate_orders = PythonOperator(
    task_id="calculate_order_metrics",
    python_callable=calculate_order_metrics,
    provide_context=True,
    dag=dag,
)

# Calculate product metrics
calculate_products = PythonOperator(
    task_id="calculate_product_metrics",
    python_callable=calculate_product_metrics,
    provide_context=True,
    dag=dag,
)

# Calculate customer metrics
calculate_customers = PythonOperator(
    task_id="calculate_customer_metrics",
    python_callable=calculate_customer_metrics,
    provide_context=True,
    dag=dag,
)



cleanup_task = PythonOperator(
    task_id="cleanup_temp_files",
    python_callable=cleanup_files,
    provide_context=True,
    dag=dag,
)

# Define task dependencies
fetch_orders_task >> calculate_orders >> cleanup_task
fetch_products_task >> calculate_products >> cleanup_task
fetch_customers_task >> calculate_customers

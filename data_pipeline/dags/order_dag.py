from datetime import timedelta

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from scripts.order_data.fetch_orders import fetch_magento_orders
from scripts.order_data.prepare_order_data import preprocess_order_data
from scripts.clean_up import cleanup_files

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "order_pipeline",
    default_args=default_args,
    description="Pipeline for processing Magento order data",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    tags=["magento", "orders"],
    params={
        "is_initial": False,
        "order_ids": [],
    },  # User can override this when triggering the DAG manually
)

# Task to fetch orders from Magento
fetch_orders = PythonOperator(
    task_id="fetch_orders",
    python_callable=fetch_magento_orders,
    dag=dag,
)


preprocess_order_data_task = PythonOperator(
    task_id="prepare_order_data",
    python_callable=preprocess_order_data,
    dag=dag,
)

cleanup_task = PythonOperator(
    task_id="cleanup_temp_files",
    python_callable=cleanup_files,
    provide_context=True,
    dag=dag,
)

fetch_orders >> preprocess_order_data_task >> cleanup_task

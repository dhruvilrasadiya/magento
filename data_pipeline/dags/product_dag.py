from airflow import DAG
from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from scripts.product_data.fetch_products import (
    fetch_magento_products,
    fetch_product_orders,
)
from scripts.product_data.fetch_stock_info import stock_info_data_fetch
from scripts.product_data.prepare_product_data import preprocess_product_data
from scripts.clean_up import cleanup_files

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "product_pipeline",
    default_args=DEFAULT_ARGS,
    description="Pipeline for processing product data per store",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    tags=["product"],
    params={
        "skus": [],
        "is_initial": False,
    },
) as dag:

    fetch_product = PythonOperator(
        task_id="fetch_products",
        python_callable=fetch_magento_products,
        provide_context=True,
    )

    fetch_product_orders_task = PythonOperator(
        task_id="fetch_product_orders",
        python_callable=fetch_product_orders,
        provide_context=True,
    )

    preprocess_product_task = PythonOperator(
        task_id="prepare_product_data",
        python_callable=preprocess_product_data,
        provide_context=True,
    )

    fetch_stock_info_task = PythonOperator(
        task_id="fetch_stock_info",
        python_callable=stock_info_data_fetch,
        provide_context=True,
    )

    cleanup_task = PythonOperator(
        task_id="cleanup_temp_files",
        python_callable=cleanup_files,
        provide_context=True,
    )

    (
        fetch_product
        >> fetch_product_orders_task
        >> preprocess_product_task
        >> cleanup_task
    )
    fetch_product >> fetch_stock_info_task

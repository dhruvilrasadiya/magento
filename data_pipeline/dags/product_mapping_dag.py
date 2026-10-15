from airflow import DAG
from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from scripts.product_data.product_mapper_new import map_and_merge_products
from scripts.product_data.fetch_dge_products_for_mapping import (
    fetch_dge_products_for_mapping,
    cleanup_product_bundle,
)
from scripts.product_data.fetch_magento_products_by_sku import (
    fetch_magento_products_by_sku,
)
from airflow.utils.trigger_rule import TriggerRule

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "DGE_product_mapping",
    default_args=DEFAULT_ARGS,
    description="Fetch DGE + Magento products by SKU (with dge_id) and map/merge them",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    tags=["product", "sku", "dge_id"],
    params={
        "is_initial": False,
    },
) as dag:

    fetch_dge_task = PythonOperator(
        task_id="fetch_dge_products",
        python_callable=fetch_dge_products_for_mapping,
        provide_context=True,
    )

    fetch_magento_by_sku_task = PythonOperator(
        task_id="fetch_magento_products",
        python_callable=fetch_magento_products_by_sku,
        provide_context=True,
    )

    map_merge_task = PythonOperator(
        task_id="map_and_merge_products",
        python_callable=map_and_merge_products,
        provide_context=True,
    )

    cleanup_task = PythonOperator(
        task_id="cleanup_product_bundle",
        python_callable=cleanup_product_bundle,
        provide_context=True,
        trigger_rule=TriggerRule.ALL_DONE,  # <== ensures it runs even if upstream fails
    )

    [fetch_dge_task, fetch_magento_by_sku_task] >> map_merge_task >> cleanup_task

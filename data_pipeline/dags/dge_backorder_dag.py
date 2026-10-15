from airflow import DAG
from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from scripts.order_data.fetch_dge_orders import fetch_dge_backorders_orders_task
from scripts.order_data.process_dge_orders import preprocess_dge_order_data

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "DGE_backorders_pipeline",
    default_args=DEFAULT_ARGS,
    description="Fetch DGE backorders",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    tags=["orders", "dge"],
    params={
        "is_initial": False,
    },
) as dag:

    fetch_dge_task = PythonOperator(
        task_id="fetch_dge_orders",
        python_callable=fetch_dge_backorders_orders_task,
        provide_context=True,
    )

    process_dge_task = PythonOperator(
        task_id="process_dge_orders",
        python_callable=preprocess_dge_order_data,
        provide_context=True,
    )

    fetch_dge_task >> process_dge_task

from airflow import DAG
from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from scripts.customer_data.deg_customer_fetch import fetch_dge_customers_task
from scripts.customer_data.dge_customer_process import preprocess_dge_customer_data


DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "DGE_customers_pipeline",
    default_args=DEFAULT_ARGS,
    description="Fetch DGE customers",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    tags=["customers", "dge"],
    params={
        "is_initial": False,
    },
) as dag:

    fetch_dge_task = PythonOperator(
        task_id="fetch_dge_customers",
        python_callable=fetch_dge_customers_task,
        provide_context=True,
    )

    process_dge_task = PythonOperator(
        task_id="process_dge_customers",
        python_callable=preprocess_dge_customer_data,
        provide_context=True,
    )

    fetch_dge_task >> process_dge_task

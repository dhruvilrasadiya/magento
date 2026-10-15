from airflow import DAG
from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from scripts.customer_data.fetch_customers import fetch_magento_customers
from scripts.customer_data.process_customer_data import process_customer_data

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "customer_pipeline",
    default_args=default_args,
    description="Pipeline for processing Magento customer data",
    schedule_interval="@daily",  # Run every 6 hours
    start_date=days_ago(1),
    catchup=False,
    tags=["magento", "customers"],
    params={"is_initial": False},
)

# Task to fetch customers from Magento
fetch_customers = PythonOperator(
    task_id="fetch_customers",
    python_callable=fetch_magento_customers,
    dag=dag,
)

# Task to process customer data and fetch related information
process_customers = PythonOperator(
    task_id="process_customer_data",
    python_callable=process_customer_data,
    dag=dag,
)

# Define task dependencies
fetch_customers >> process_customers

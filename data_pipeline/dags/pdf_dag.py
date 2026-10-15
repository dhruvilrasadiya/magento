from airflow import DAG
from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from scripts.pdf_data.process_pdfs import process_pdfs

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "pdf_pipeline",
    default_args=default_args,
    description="Pipeline for processing and embedding PDF documents",
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    tags=["pdf", "embedding"],
)

# Task to process and embed PDF documents
process_pdf_task = PythonOperator(
    task_id="process_pdfs",
    python_callable=process_pdfs,
    provide_context=True,
    dag=dag,
)

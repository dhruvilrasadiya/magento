# from airflow import DAG
# from datetime import timedelta
# from airflow.utils.dates import days_ago
# from airflow.operators.python import PythonOperator
# from scripts.product_data.fetch_dge_products import fetch_dge_products
# from scripts.product_data.prepare_dge_product_data import preprocess_dge_product_data

# DEFAULT_ARGS = {
#     "owner": "airflow",
#     "depends_on_past": False,
#     "email_on_failure": False,
#     "email_on_retry": False,
#     "retries": 1,
#     "retry_delay": timedelta(minutes=5),
# }

# with DAG(
#     "dge_product_pipeline",
#     default_args=DEFAULT_ARGS,
#     description="Pipeline for processing DGE product data",
#     schedule_interval="@daily",
#     start_date=days_ago(1),
#     catchup=False,
#     tags=["product", "dge"],
# ) as dag:

#     fetch_dge_products_task = PythonOperator(
#         task_id="fetch_dge_products",
#         python_callable=fetch_dge_products,
#         provide_context=True,
#     )

#     preprocess_dge_product_task = PythonOperator(
#         task_id="prepare_dge_product_data",
#         python_callable=preprocess_dge_product_data,
#         provide_context=True,
#     )

#     # Define task dependencies
#     fetch_dge_products_task >> preprocess_dge_product_task
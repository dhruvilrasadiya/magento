import os


def cleanup_files(**context):
    """Remove temporary files created during DAG run."""
    data_dir = "/tmp/airflow_data"
    run_id = context["dag_run"].run_id
    orders_file = f"{data_dir}/orders_{run_id.replace(':', '_')}.json"
    products_file = f"{data_dir}/products_{run_id.replace(':', '_')}.json"

    for f in [orders_file, products_file]:
        if os.path.exists(f):
            os.remove(f)
            print(f"[CLEANUP] Deleted file: {f}")
        else:
            print(f"[CLEANUP] File not found, skipping: {f}")

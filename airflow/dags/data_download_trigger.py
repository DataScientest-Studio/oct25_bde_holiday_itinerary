import time
from datetime import datetime, UTC, timedelta

from airflow.models import Variable
from airflow.providers.http.hooks.http import HttpHook
from airflow.providers.http.operators.http import HttpOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import TaskGroup
from airflow.sdk import dag, task


@task(multiple_outputs=True)
def trigger_download():
    hook = HttpHook(http_conn_id="NEO4J_API_CONN", method='GET')
    response = hook.run(
        endpoint='/data/trigger-download',
        headers={"Content-Type": "application/json"},
        extra_options={"check_response": False},
    )
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.json()}")
    return {
        "return_value": response.json(),
        "status_code": response.status_code,
    }


@task
def wait_for_status_complete(process):
    """
    Polls the /data/status endpoint until status == 'completed'
    """
    hook = HttpHook(http_conn_id="NEO4J_API_CONN", method='GET')
    endpoint = f"/data/{process}/status"

    max_attempts = 15
    poll_interval = 60

    for attempt in range(1, max_attempts + 1):
        response = hook.run(endpoint=endpoint)
        data = response.json()
        status = data.get('status')
        print(f"Attempt {attempt}: status = {status}")

        if status == 'completed':
            file_location = data.get('details')["filename"]
            return {
                'status': 'completed',
                'file_location': file_location,
            }
        time.sleep(poll_interval)

    raise Exception(f"Timed out waiting for download to complete")


@task.branch
def branch_download(status_code):
    print("status code in branch_download:", status_code)
    if status_code == 202:
            return "wait_for_download"
    if status_code == 409:
            return "do_nothing"
    if status_code == 404:
            return "do_nothing"
    return "do_nothing"

@task
def do_nothing():
    print("nothing to do")

@task
def trigger_unzip_data():
    hook = HttpHook(http_conn_id="NEO4J_API_CONN", method='GET')
    response = hook.run(
        endpoint='/data/trigger-unzip',
        headers={"Content-Type": "application/json"},
    )
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.json()}")
    return {
        "return_value": response.json(),
        "status_code": response.status_code,
    }

@task
def trigger_extract_new_data():
    hook = HttpHook(http_conn_id="NEO4J_API_CONN", method='GET')
    response = hook.run(
        endpoint='/data/trigger-extract-data',
        headers={"Content-Type": "application/json"},
    )
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.json()}")
    return {
        "return_value": response.json(),
        "status_code": response.status_code,
    }

@task
def trigger_import_new_data():
    hook = HttpHook(http_conn_id="NEO4J_API_CONN", method='GET')
    response = hook.run(
        endpoint='/data/trigger-import-data',
        headers={"Content-Type": "application/json"},
    )
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.json()}")
    return {
        "return_value": response.json(),
        "status_code": response.status_code,
    }

@task
def trigger_import_cleanup():
    hook = HttpHook(http_conn_id="NEO4J_API_CONN", method='GET')
    response = hook.run(
        endpoint='/data/trigger-import-cleanup',
        headers={"Content-Type": "application/json"},
    )
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.json()}")
    return {
        "return_value": response.json(),
        "status_code": response.status_code,
    }

@dag(
    dag_id="download-trigger",
    # schedule=timedelta(minutes=1),
    schedule=None,
    tags=['download', 'trigger', 'oct25_bde_holiday_itinerary'],
    catchup=False,
    default_args={
        'owner': 'airflow',
        'start_date': datetime.now(UTC) - timedelta(days=1)
    }
)
def download_dag():
    triggered_download = trigger_download()
    status_code = triggered_download["status_code"]
    branch_task = branch_download(status_code)

    do_nothing_ = do_nothing()
    wait_for_download = wait_for_status_complete.override(task_id="wait_for_download")("download")
    branch_task >> [do_nothing_, wait_for_download]

    unzip_data = trigger_unzip_data()
    wait_for_unzip = wait_for_status_complete.override(task_id="wait_for_unzip")("unzip")

    extract_new_data = trigger_extract_new_data()
    wait_for_extract = wait_for_status_complete.override(task_id="wait_for_extract")("extract")

    import_new_data = trigger_import_new_data()
    wait_for_import = wait_for_status_complete.override(task_id="wait_for_import")("import")

    cleanup_import = trigger_import_cleanup()
    wait_for_cleanup = wait_for_status_complete.override(task_id="wait_for_cleanup")("cleanup")

    wait_for_download >> unzip_data >> wait_for_unzip
    wait_for_unzip >> extract_new_data >> wait_for_extract
    wait_for_extract >> import_new_data >> wait_for_import
    wait_for_import >> cleanup_import >> wait_for_cleanup



dag = download_dag()


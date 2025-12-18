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
def wait_for_download_complete():
    """
    Polls the /data/status endpoint until status == 'completed'
    """
    hook = HttpHook(http_conn_id="NEO4J_API_CONN", method='GET')
    endpoint = f"/data/status"

    max_attempts = 15
    poll_interval = 60

    for attempt in range(1, max_attempts + 1):
        response = hook.run(endpoint=endpoint)
        data = response.json()
        status = data.get('status')
        print(f"Attempt {attempt}: Download status = {status}")

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
            return "wait_for_download_complete"
    if status_code == 409:
            return "do_nothing"
    if status_code == 404:
            return "do_nothing"
    return "do_nothing"

@task
def do_nothing():
    print("nothing to do")

@task
def trigger_import_new_data_to_neo4j():
    hook = HttpHook(http_conn_id="NEO4J_API_CONN", method='GET')
    response = hook.run(
        endpoint='/data/trigger-import-new-data',
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
    wait_for_download = wait_for_download_complete()
    branch_task >> [do_nothing_, wait_for_download]

    trigger_import_new_data_to_neo4j_ = trigger_import_new_data_to_neo4j()

    wait_for_download >> trigger_import_new_data_to_neo4j_


dag = download_dag()


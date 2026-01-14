import os
from pathlib import Path
from typing import Any, Dict, Literal, Union

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from starlette.status import HTTP_202_ACCEPTED

from src.neo4j_api.cleanup_import import perform_cleanup_import
from src.neo4j_api.data_upload_etl import perform_extract_data, unzip_data
from src.neo4j_api.datatourisme_handler import AuthenticatedClient, NoDataAvailable, check_download, perform_download
from src.neo4j_api.import_data import perform_import_data
from src.neo4j_api.status_handler import ProcessLock, ProcessRunning, get_status_file, get_status_file_content

SAVE_DIR = os.getenv("DATATOURISME_SAVE_DIR")
if not os.path.exists(SAVE_DIR):
    os.mkdir(SAVE_DIR)
SAVE_DIR = Path(SAVE_DIR)

IMPORT_DIR = os.getenv("DATATOURISME_IMPORT_DIR")
if not os.path.exists(IMPORT_DIR):
    os.mkdir(IMPORT_DIR)
IMPORT_DIR = Path(IMPORT_DIR)

router = APIRouter()


def raise_if_in_progress(save_dir, process):
    ProcessLock(save_dir, process=process).raise_for_in_process()


def raise_if_file_not_exists(file_path: Union[Path, str]):
    if not Path(file_path).exists():
        raise FileNotFoundError(f"file {file_path} not found")


def raise_if_file_exists(file_path: Union[Path, str]):
    if Path(file_path).exists():
        raise FileExistsError(f"file {file_path} already exists")


@router.get("/{process}/status")
async def get_status(process: Literal["download", "unzip", "extract", "import", "cleanup"]):
    """Airflow polls this endpoint to check if a process is done."""
    if ProcessLock(SAVE_DIR, process=process).lock_file.exists():
        return {"status": "in_progress"}

    status_file = get_status_file(SAVE_DIR, process=process)
    if not status_file.exists():
        return {"status": "never_run"}

    content = get_status_file_content(SAVE_DIR, process=process)
    return {"status": "completed", "details": content}


@router.get("/trigger-download", status_code=HTTP_202_ACCEPTED)  # type: ignore[misc]
async def trigger_download(bg_tasks: BackgroundTasks):
    """
    Airflow calls this endpoint.
    Returns immediately with 202 Accepted.
    Download runs in background.
    """
    try:
        raise_if_in_progress(SAVE_DIR, "download")
        auth_client = AuthenticatedClient()
        await auth_client.login()
        await check_download(auth_client, SAVE_DIR)
        bg_tasks.add_task(perform_download, SAVE_DIR, auth_client)
    except ProcessRunning:
        raise HTTPException(status_code=409, detail="Download already in progress")
    except NoDataAvailable:
        raise HTTPException(status_code=404, detail="No new data available")

    return {"message": "Download triggered successfully", "check_status_at": "/status", "download_dir": str(SAVE_DIR)}


@router.get("/trigger-unzip", status_code=HTTP_202_ACCEPTED)
async def unzip_downloaded_data(bg_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Airflow calls this endpoint.
    Returns immediately with 202 Accepted.
    Unzip runs in background.
    """
    try:
        raise_if_in_progress(SAVE_DIR, "download")
        raise_if_in_progress(SAVE_DIR, "unzip")

        download_status = get_status_file_content(SAVE_DIR, "download")
        file_path = SAVE_DIR / download_status["filename"]
        raise_if_file_not_exists(file_path)

        extract_to = SAVE_DIR / file_path.stem
        raise_if_file_exists(extract_to)

        bg_tasks.add_task(unzip_data, file_path, SAVE_DIR, extract_to)
    except ProcessRunning as exc:
        status_code = 409
        detail = "Unzip already in progress"
        if exc.process == "download":
            status_code = 404
            detail = "No data available for unzip"
        raise HTTPException(status_code=status_code, detail=detail)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except FileExistsError:
        raise HTTPException(status_code=400, detail="already done")

    return {
        "message": "Unzip downloaded data triggered successfully",
        "extract_to": str(extract_to),
    }


@router.get("/trigger-extract-data")
async def extract_data(bg_tasks: BackgroundTasks) -> Dict[str, Any]:
    try:
        raise_if_in_progress(SAVE_DIR, "extract")
        raise_if_file_not_exists(get_status_file(SAVE_DIR, "unzip"))

        unzip_status = get_status_file_content(SAVE_DIR, "unzip")
        extracted_data_path = Path(unzip_status["filename"])
        raise_if_file_not_exists(extracted_data_path)

        bg_tasks.add_task(perform_extract_data, extracted_data_path, SAVE_DIR, IMPORT_DIR)
    except ProcessRunning:
        raise HTTPException(status_code=409, detail="Extract already in progress")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {
        "message": "Extract data triggered successfully",
        "check_status_at": "/status",
    }


@router.get("/trigger-import-data")
async def import_data(request: Request, bg_tasks: BackgroundTasks) -> Dict[str, Any]:
    try:
        raise_if_in_progress(SAVE_DIR, "import")
        raise_if_file_not_exists(get_status_file(SAVE_DIR, "extract"))

        extract_status = get_status_file_content(SAVE_DIR, "extract")
        extracted_data_path = Path(extract_status["filename"])
        raise_if_file_not_exists(extracted_data_path)

        bg_tasks.add_task(perform_import_data, SAVE_DIR, request.app.state.driver, extracted_data_path)
    except ProcessRunning:
        raise HTTPException(status_code=409, detail="Import already in progress")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {
        "message": "Import data triggered successfully",
        "check_status_at": "/status",
    }


@router.get("/trigger-import-cleanup")
async def process_cleanup(request: Request, bg_tasks: BackgroundTasks) -> Dict[str, Any]:
    try:
        raise_if_in_progress(SAVE_DIR, "cleanup")
        raise_if_file_not_exists(get_status_file(SAVE_DIR, "import"))

        import_status = get_status_file_content(SAVE_DIR, "import")
        if "import_version" not in import_status:
            raise HTTPException(status_code=400, detail="Import didn't finish successfully")

        import_version = import_status["import_version"]

        download_status = get_status_file_content(SAVE_DIR, "download")
        zip_file_path = SAVE_DIR / download_status["filename"]

        unzipped_status = get_status_file_content(SAVE_DIR, "unzip")
        unzipped_data_path = Path(unzipped_status["filename"])

        extracted_status = get_status_file_content(SAVE_DIR, "extract")
        extracted_data_path = Path(extracted_status["filename"])

        bg_tasks.add_task(
            perform_cleanup_import,
            SAVE_DIR,
            zip_file_path,
            unzipped_data_path,
            extracted_data_path,
            request.app.state.driver,
            import_version,
        )
    except ProcessRunning:
        raise HTTPException(status_code=409, detail="Cleanup already in progress")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {
        "message": "Cleanup import triggered successfully",
        "check_status_at": "/status",
    }

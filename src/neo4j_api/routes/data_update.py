import asyncio
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict
from bs4 import BeautifulSoup
import json

import httpx
from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_202_ACCEPTED

router = APIRouter()

# FEED = "https://diffuseur.datatourisme.fr/flux/24943/download/complete"
# LOGIN_URL = "https://diffuseur.datatourisme.fr/fr/login"
# EMAIL = "adam.stibal@gmail.com"
# PASSWORD = "FrzuaKjW3v!trx3"
#
# SAVE_DIR = Path("./feed_data")
# STATUS_FILE = SAVE_DIR / "last_download.txt"
# IN_PROGRESS_FILE = SAVE_DIR / "download_in_progress.lock"

FEED = os.getenv("DATATOURISME_FEED")
LOGIN_URL = os.getenv("DATATOURISME_LOGIN_URL")
EMAIL = os.getenv("DATATOURISME_EMAIL")
PASSWORD = os.getenv("DATATOURISME_PASSWORD")
SAVE_DIR = os.getenv("DATATOURISME_SAVE_DIR")
if not os.path.exists(SAVE_DIR):
    os.mkdir(SAVE_DIR)
SAVE_DIR = Path(SAVE_DIR)
STATUS_FILE = SAVE_DIR / "last_download.txt"
IN_PROGRESS_FILE = SAVE_DIR / "download_in_progress.lock"

def is_download_in_progress() -> bool:
    return os.path.exists(IN_PROGRESS_FILE)

def set_in_progress():
    open(IN_PROGRESS_FILE, 'w').close()

def clear_in_progress():
    if os.path.exists(IN_PROGRESS_FILE):
        os.remove(IN_PROGRESS_FILE)

class AuthenticatedClient:
    """Manages login and provides an authenticated async client."""
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=None, follow_redirects=True)

    async def login(self):
        """Fetch login page, extract CSRF, POST credentials."""
        # GET login page to get CSRF token
        resp = await self.client.get(LOGIN_URL)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not load login page")

        soup = BeautifulSoup(resp.text, "html.parser")
        csrf_input = soup.find("input", {"name": "_csrf_token"})
        if not csrf_input or not csrf_input.get("value"):
            raise HTTPException(status_code=500, detail="CSRF token not found on login page")

        csrf_token = csrf_input["value"]

        # POST login
        login_data = {
            "_username": EMAIL,      # Common Symfony field name; adjust if it's "email"
            "_password": PASSWORD,
            "_csrf_token": csrf_token,
            # If the form uses "email" instead of "_username", change above
        }

        login_resp = await self.client.post(LOGIN_URL, data=login_data)
        if login_resp.status_code != 200 or "logout" not in login_resp.text.lower():
            # Rough check: after login, page should have logout link
            raise HTTPException(status_code=401, detail="Login failed - check credentials or field names")

    async def close(self):
        await self.client.aclose()

async def check_download() -> Dict[str, Any]:
    """check if new flux data available for download"""
    try:
        with open(STATUS_FILE, "r") as f:
            last_download = json.load(f)
    except FileNotFoundError:
        return {
            "download_available": True,
            "feed_generation": None,
        }

    auth_client = AuthenticatedClient()

    await auth_client.login()

    modal_resp = await auth_client.client.get(FEED)

    soup = BeautifulSoup(modal_resp.text, "html.parser")
    form = soup.find("form", {"action": "/flux/24943/download/complete"})
    if not form:
        raise HTTPException(status_code=500, detail="Download form not found in modal")
    details = {
        key.strip(): value.strip()
        for li in form.find("ul").find_all("li")
        for key, value in [li.text.split(":", 1)]
    }

    if last_download["last_feed_generation"] == details["Date"]:
        return {
            "download_available": False,
        }
    return {
        "download_available": True,
        "feed_generation": details["Date"],
    }

async def perform_download() -> Dict[str, Any]:
    """download the new flux file"""
    if is_download_in_progress():
        return {"status": "in_progress"}

    auth_client = AuthenticatedClient()
    set_in_progress()
    try:
        await auth_client.login()
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"datatourisme_data_{timestamp}.zip"
        filepath = SAVE_DIR / filename

        get_resp = await auth_client.client.get(FEED)

        if get_resp.status_code == 302:
            # If redirect, follow manually once
            redirect_url = get_resp.headers["Location"]
            modal_resp = await auth_client.client.get(redirect_url)
        else:
            modal_resp = get_resp

        if modal_resp.status_code != 200:
            raise HTTPException(status_code=modal_resp.status_code, detail="Failed to load confirmation modal")

        # Parse modal HTML to extract the actual download trigger URL
        soup = BeautifulSoup(modal_resp.text, "html.parser")

        form = soup.find("form", {"action": "/flux/24943/download/complete"})
        if not form:
            raise HTTPException(status_code=500, detail="Download form not found in modal")
        details = {
            key.strip(): value.strip()
            for li in form.find("ul").find_all("li")
            for key, value in [li.text.split(":", 1)]
        }

        try:
            with open(STATUS_FILE, "r") as f:
                last_download = json.load(f)

            if last_download["last_feed_generation"] == details["Date"]:
                return {
                    "status": "skipped",
                    "reason": "no new data available",
                }
        except FileNotFoundError:
            pass

        post_resp = await auth_client.client.post(FEED+"/get")
        if post_resp.status_code != 200:
            raise HTTPException(status_code=post_resp.status_code, detail="POST to trigger download failed")

            # The POST response should now be the actual GZ file (binary stream)
        content_disposition = post_resp.headers.get("Content-Disposition", "")
        if "attachment" not in content_disposition and post_resp.headers.get("Content-Type", "").startswith(
                "text/html"):
            # Fallback: save response for debugging
            with open(os.path.join(SAVE_DIR, "debug_last_response.html"), "wb") as f:
                f.write(post_resp.content)
            raise HTTPException(status_code=500,
                                detail="Received HTML instead of file after POST - check debug_last_response.html")

        # Streaming save the real file
        with open(filepath, "wb") as f:
            async for chunk in post_resp.aiter_bytes(chunk_size=8192):
                f.write(chunk)
        x=1
        status = {
            "last_download_utc": datetime.now(UTC).isoformat(),
            "last_feed_generation": details["Date"],
            "filename": filename,
            "size_bytes": os.path.getsize(filepath)
        }
        with open(STATUS_FILE, "w") as f:
            json.dump(status, fp=f)
        return status
    finally:
        clear_in_progress()
        await auth_client.close()

@router.get("/trigger-download", status_code=HTTP_202_ACCEPTED)  # type: ignore[misc]
async def trigger_download():
    """
        Airflow calls this endpoint.
        Returns immediately with 202 Accepted.
        Download runs in background.
        """
    if is_download_in_progress():
        raise HTTPException(
            status_code=409,
            detail="Download already in progress"
        )

    data_available_resp = await check_download()
    if data_available_resp["download_available"] == False:
        raise HTTPException(
            status_code=404,
            detail="No new data available"
        )

    asyncio.create_task(perform_download())
    return {
        "message": "Download triggered successfully",
        "check_status_at": "/status",
        "download_dir": SAVE_DIR
    }

@router.get("/status")
async def get_status():
    """Airflow polls this endpoint to check if download is done."""
    if is_download_in_progress():
        return {"status": "in_progress"}

    if not os.path.exists(STATUS_FILE):
        return {"status": "never_run"}

    with open(STATUS_FILE, "r") as f:
        content = json.load(f)
        return {"status": "completed", "details": content}


@router.get("/trigger-import-new-data", status_code=HTTP_202_ACCEPTED)
async def trigger_import_new_data() -> Dict[str, str]:
    if is_download_in_progress() or not os.path.exists(STATUS_FILE):
        raise HTTPException(status_code=404, detail="data for import not available")
    with open(STATUS_FILE, "r") as f:
        content = json.load(f)
    file_path = SAVE_DIR/ content["filename"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"file {file_path} for import not found")
    return {
        "message": "Import new data to Neo4j triggered successfully",
    }


@router.get("/")
async def root():
    return {"service": "DATAtourisme download trigger for Airflow"}
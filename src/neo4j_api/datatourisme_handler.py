"""handlers for datatourisme API"""

import json
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any

from bs4 import BeautifulSoup
import httpx
from fastapi import HTTPException

from src.neo4j_api.status_handler import ProcessLock, get_status_file

FEED = os.getenv("DATATOURISME_FEED")
LOGIN_URL = os.getenv("DATATOURISME_LOGIN_URL")
EMAIL = os.getenv("DATATOURISME_EMAIL")
PASSWORD = os.getenv("DATATOURISME_PASSWORD")


class NoDataAvailable(Exception):
    def __str__(self):
        return f"No new flux data available for download"


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
            "_username": EMAIL,
            "_password": PASSWORD,
            "_csrf_token": csrf_token,
        }

        login_resp = await self.client.post(LOGIN_URL, data=login_data)
        if login_resp.status_code != 200 or "logout" not in login_resp.text.lower():
            # Rough check: after login, page should have logout link
            raise HTTPException(status_code=401, detail="Login failed - check credentials or field names")

    async def close(self):
        await self.client.aclose()

async def check_download(auth_client, save_dir) -> Dict[str, Any]:
    """check if new flux data available for download"""
    try:
        with open(get_status_file(save_dir, "download"), "r") as f:
            last_download = json.load(f)
    except FileNotFoundError:
        return True

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
        raise NoDataAvailable()
    return True


async def perform_download(save_dir: Path, auth_client: AuthenticatedClient) -> Dict[str, Any]:
    """download the new flux file"""
    with ProcessLock(save_dir, "download"):
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"datatourisme_data_{timestamp}.zip"
        filepath = save_dir / filename

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
            with open(get_status_file(save_dir, "download"), "r") as f:
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
            with open(os.path.join(save_dir, "debug_last_response.html"), "wb") as f:
                f.write(post_resp.content)
            raise HTTPException(status_code=500,
                                detail="Received HTML instead of file after POST - check debug_last_response.html")

        # Streaming save the real file
        with open(filepath, "wb") as f:
            async for chunk in post_resp.aiter_bytes(chunk_size=8192):
                f.write(chunk)
        status = {
            "last_download_utc": datetime.now(UTC).isoformat(),
            "last_feed_generation": details["Date"],
            "filename": filename,
            "size_bytes": os.path.getsize(filepath)
        }
        with open(get_status_file(save_dir, "download"), "w") as f:
            json.dump(status, fp=f)
        await auth_client.close()
        return status

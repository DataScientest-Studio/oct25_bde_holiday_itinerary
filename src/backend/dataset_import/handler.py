"""handlers for datatourisme API"""

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict

import aiohttp
from bs4 import BeautifulSoup
from fastapi import HTTPException
from tqdm import tqdm

from .status_handler import ProcessLock, get_status_file

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

FEED = os.getenv("DATATOURISME_FEED")
LOGIN_URL = os.getenv("DATATOURISME_LOGIN_URL")
EMAIL = os.getenv("DATATOURISME_EMAIL")
PASSWORD = os.getenv("DATATOURISME_PASSWORD")
VERIFY_SSL = os.getenv("DATATOURISME_VERIFY_SSL", "true").lower() == "true"


class NoDataAvailable(Exception):
    def __str__(self):
        return "No new flux data available for download"


class AuthenticatedClient:
    """Manages login and provides an authenticated async client."""

    def __init__(self):
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=20, ssl=False)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=None),
        )

    async def login(self):
        """Fetch login page, extract CSRF, POST credentials."""
        # GET login page to get CSRF token
        async with self.session.get(LOGIN_URL, allow_redirects=True) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=502, detail="Could not load login page")

            text = await resp.text()
            soup = BeautifulSoup(text, "html.parser")
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

            async with self.session.post(LOGIN_URL, data=login_data, allow_redirects=True) as login_resp:
                login_text = await login_resp.text()
                if login_resp.status != 200 or "logout" not in login_text.lower():
                    # Rough check: after login, page should have logout link
                    raise HTTPException(status_code=401, detail="Login failed - check credentials or field names")

    async def close(self):
        await self.session.close()


async def check_download(auth_client: AuthenticatedClient, save_dir) -> Dict[str, Any]:
    """check if new flux data available for download"""
    try:
        with open(get_status_file(save_dir, "download"), "r") as f:
            last_download = json.load(f)
    except FileNotFoundError:
        return True

    async with auth_client.session.get(FEED, allow_redirects=True) as modal_resp:
        text = await modal_resp.text()
        soup = BeautifulSoup(text, "html.parser")
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


async def perform_download(save_dir: Path, auth_client: AuthenticatedClient) -> Dict[str, Any]:  # noqa: C901
    """download the new flux file"""
    with ProcessLock(save_dir, "download"):
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"datatourisme_data_{timestamp}.zip"
        filepath = save_dir / filename

        async with auth_client.session.get(FEED, allow_redirects=True) as get_resp:
            if get_resp.status != 200:
                raise HTTPException(status_code=get_resp.status, detail="Failed to load confirmation modal")

            modal_text = await get_resp.text()
            # Parse modal HTML to extract the actual download trigger URL
            soup = BeautifulSoup(modal_text, "html.parser")

            form = soup.find("form", {"action": "/flux/24943/download/complete"})
            if not form:
                raise HTTPException(status_code=500, detail="Download form not found in modal")

            # Use the actual action from the form and the final URL to construct the POST URL
            action = form.get("action")
            # Ensure we use the base URL from the final response URL in case of redirects
            base_url = f"{get_resp.url.scheme}://{get_resp.url.host}"
            if get_resp.url.port:
                base_url += f":{get_resp.url.port}"

            post_url = f"{base_url}{action}/get"
            details = {
                key.strip(): value.strip()
                for li in form.find("ul").find_all("li")
                for key, value in [li.text.split(":", 1)]
            }

            try:
                with open(get_status_file(save_dir, "download"), "r") as f:
                    last_download = json.load(f)

                if last_download["last_feed_generation"] == details["Date"]:
                    await auth_client.close()
                    return {
                        "status": "skipped",
                        "reason": "no new data available",
                    }
            except FileNotFoundError:
                pass

            logger.info("Starting download of new DataTourisme flux...")
            async with auth_client.session.post(post_url, allow_redirects=True) as post_resp:
                if post_resp.status != 200:
                    raise HTTPException(status_code=post_resp.status, detail="POST to trigger download failed")

                content_disposition = post_resp.headers.get("Content-Disposition", "")
                if "attachment" not in content_disposition and post_resp.headers.get("Content-Type", "").startswith(
                    "text/html"
                ):
                    # Fallback: save response for debugging
                    with open(os.path.join(save_dir, "debug_last_response.html"), "wb") as f:
                        f.write(await post_resp.read())
                    # Ensure we close session if we fail here
                    await auth_client.close()
                    raise HTTPException(
                        status_code=500,
                        detail="Received HTML instead of file after POST - check debug_last_response.html",
                    )

                # Streaming save the real file
                total_size = int(post_resp.headers.get("Content-Length", 0)) or None
                desc = f"Downloading {filename}"
                try:
                    with tqdm(
                        desc=desc,
                        total=total_size,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        miniters=1,
                        dynamic_ncols=True,
                        disable=False,
                        ascii=True,
                    ) as pbar:
                        with open(filepath, "wb") as f:
                            async for chunk in post_resp.content.iter_chunked(8192 * 4):
                                f.write(chunk)
                                pbar.update(len(chunk))
                finally:
                    await auth_client.close()

        status = {
            "last_download_utc": datetime.now(UTC).isoformat(),
            "last_feed_generation": details["Date"],
            "filename": filename,
            "size_bytes": os.path.getsize(filepath),
        }
        with open(get_status_file(save_dir, "download"), "w") as f:
            json.dump(status, fp=f)
        return status

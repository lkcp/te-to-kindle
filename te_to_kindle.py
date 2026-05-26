"""Send the latest The Economist issue from evanbio/The_Economist to Kindle by email."""
from __future__ import annotations

import mimetypes
import os
import smtplib
import sys
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

import requests

REPO = "evanbio/The_Economist"
BRANCH = "main"
FORMAT = os.environ.get("TE_FORMAT", "mobi").lower()  # mobi / epub / azw3 / pdf
STATE_FILE = Path(os.environ.get("TE_STATE_FILE", "last_sent.txt"))

KINDLE_EMAIL = os.environ["KINDLE_EMAIL"]
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

GH_HEADERS = {"Accept": "application/vnd.github+json"}
if token := os.environ.get("GITHUB_TOKEN"):
    GH_HEADERS["Authorization"] = f"Bearer {token}"


def list_issue_folders() -> list[str]:
    """Return TE-YYYY-MM-DD folder names sorted ascending."""
    url = f"https://api.github.com/repos/{REPO}/contents?ref={BRANCH}"
    r = requests.get(url, headers=GH_HEADERS, timeout=30)
    r.raise_for_status()
    folders = [
        item["name"]
        for item in r.json()
        if item["type"] == "dir" and item["name"].startswith("TE-")
    ]
    return sorted(folders)


def expected_folder_for_today() -> str:
    """Issue is dated to the Saturday of the current week (Beijing time)."""
    now = datetime.now(timezone(timedelta(hours=8)))
    # weekday(): Mon=0 ... Sat=5, Sun=6
    days_back = (now.weekday() - 5) % 7
    sat = (now - timedelta(days=days_back)).date()
    return f"TE-{sat.isoformat()}"


def download(folder: str) -> Path:
    filename = f"{folder}.{FORMAT}"
    raw = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{folder}/{filename}"
    r = requests.get(raw, timeout=300)
    r.raise_for_status()
    out = Path("/tmp") / filename
    out.write_bytes(r.content)
    return out


def send_to_kindle(file: Path) -> None:
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = KINDLE_EMAIL
    msg["Subject"] = "convert"  # tells Amazon to auto-convert if needed
    msg.set_content(f"Auto-pushed: {file.name}")

    ctype, _ = mimetypes.guess_type(file.name)
    if ctype is None:
        ctype = "application/octet-stream"
    maintype, subtype = ctype.split("/", 1)
    msg.add_attachment(file.read_bytes(), maintype=maintype, subtype=subtype, filename=file.name)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.ehlo()
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)


def already_sent(folder: str) -> bool:
    return STATE_FILE.exists() and STATE_FILE.read_text().strip() == folder


def mark_sent(folder: str) -> None:
    STATE_FILE.write_text(folder)


def main() -> int:
    target = expected_folder_for_today()
    print(f"[info] looking for {target} (format={FORMAT})")

    if already_sent(target):
        print("[skip] already sent this week")
        return 0

    # Retry up to 6 times (10 min apart) in case upstream is a bit late.
    for attempt in range(1, 7):
        folders = list_issue_folders()
        latest = folders[-1] if folders else None
        print(f"[info] attempt {attempt}: latest upstream folder = {latest}")
        if target in folders:
            break
        if attempt == 6:
            print(f"[error] {target} not found upstream after 6 attempts; latest is {latest}")
            return 1
        time.sleep(600)

    print(f"[info] downloading {target}.{FORMAT}")
    f = download(target)
    print(f"[info] {f.name}: {f.stat().st_size / 1024 / 1024:.1f} MB")

    print(f"[info] sending to {KINDLE_EMAIL}")
    send_to_kindle(f)

    mark_sent(target)
    print("[done] sent")
    return 0


if __name__ == "__main__":
    sys.exit(main())

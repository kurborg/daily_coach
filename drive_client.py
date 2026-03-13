import os
import json
import base64
import zipfile
from io import BytesIO

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _get_credentials():
    b64 = os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64")
    if b64:
        json_str = base64.b64decode(b64).decode("utf-8")
        info = json.loads(json_str)
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

    path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")
    if path:
        return service_account.Credentials.from_service_account_file(path, scopes=SCOPES)

    raise ValueError(
        "No Google credentials found. Set GOOGLE_SERVICE_ACCOUNT_BASE64 or "
        "GOOGLE_SERVICE_ACCOUNT_JSON_PATH environment variable."
    )


def _get_service():
    creds = _get_credentials()
    return build("drive", "v3", credentials=creds)


def _find_folder_id(service, folder_name: str) -> str:
    query = (
        f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    result = service.files().list(q=query, fields="files(id, name)").execute()
    files = result.get("files", [])
    if not files:
        raise FileNotFoundError(f"Folder '{folder_name}' not found in Google Drive.")
    return files[0]["id"]


def _list_export_files(service, folder_id: str) -> list:
    """Return all .zip and .json files in the folder, newest first."""
    query = (
        f"'{folder_id}' in parents and trashed = false and ("
        "mimeType = 'application/zip' or "
        "mimeType = 'application/x-zip-compressed' or "
        "mimeType = 'application/json'"
        ")"
    )
    result = service.files().list(
        q=query,
        orderBy="createdTime desc",
        fields="files(id, name, createdTime, mimeType)",
    ).execute()
    return result.get("files", [])


def _download_bytes(service, file_id: str) -> bytes:
    request = service.files().get_media(fileId=file_id)
    buf = BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return buf.read()


def _extract_json_from_zip(zip_bytes: bytes) -> dict:
    """
    Extract the health export JSON from a ZIP.
    Health Auto Export ZIPs typically contain one JSON file (sometimes nested
    in a subfolder). We take the largest JSON file found — that's the export.
    """
    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        json_names = [
            name for name in zf.namelist()
            if name.endswith(".json") and not name.startswith("__MACOSX")
        ]

        if not json_names:
            raise ValueError("No JSON file found inside the ZIP export.")

        # If multiple JSONs, pick the largest (most complete)
        if len(json_names) > 1:
            json_names.sort(key=lambda n: zf.getinfo(n).file_size, reverse=True)
            print(f"[Drive] ZIP contains {len(json_names)} JSON files — using largest: {json_names[0]}")
        else:
            print(f"[Drive] Extracting: {json_names[0]}")

        with zf.open(json_names[0]) as f:
            return json.loads(f.read().decode("utf-8"))


def get_latest_health_export() -> dict:
    folder_name = os.environ.get("GOOGLE_DRIVE_FOLDER_NAME", "health-exports")
    service = _get_service()
    folder_id = _find_folder_id(service, folder_name)
    files = _list_export_files(service, folder_id)

    if not files:
        raise FileNotFoundError(
            f"No export files (.zip or .json) found in Google Drive folder '{folder_name}'."
        )

    latest = files[0]
    print(f"[Drive] Found export: {latest['name']} ({latest['mimeType']}) — {latest['createdTime']}")

    raw_bytes = _download_bytes(service, latest["id"])

    if latest["name"].endswith(".zip") or "zip" in latest["mimeType"]:
        return _extract_json_from_zip(raw_bytes)
    else:
        return json.loads(raw_bytes.decode("utf-8"))


def get_health_exports_last_n_days(n: int) -> list:
    folder_name = os.environ.get("GOOGLE_DRIVE_FOLDER_NAME", "health-exports")
    service = _get_service()
    folder_id = _find_folder_id(service, folder_name)
    files = _list_export_files(service, folder_id)

    results = []
    for f in files[:n]:
        try:
            raw_bytes = _download_bytes(service, f["id"])
            if f["name"].endswith(".zip") or "zip" in f["mimeType"]:
                results.append(_extract_json_from_zip(raw_bytes))
            else:
                results.append(json.loads(raw_bytes.decode("utf-8")))
        except Exception as e:
            print(f"Warning: could not process {f['name']}: {e}")
    return results

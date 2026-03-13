import os
import json
import base64
import tempfile
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


def _list_json_files(service, folder_id: str) -> list:
    query = (
        f"'{folder_id}' in parents and mimeType = 'application/json' and trashed = false"
    )
    result = service.files().list(
        q=query,
        orderBy="createdTime desc",
        fields="files(id, name, createdTime)",
    ).execute()
    return result.get("files", [])


def _download_file(service, file_id: str) -> dict:
    request = service.files().get_media(fileId=file_id)
    buf = BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return json.loads(buf.read().decode("utf-8"))


def get_latest_health_export() -> dict:
    folder_name = os.environ.get("GOOGLE_DRIVE_FOLDER_NAME", "health-exports")
    service = _get_service()
    folder_id = _find_folder_id(service, folder_name)
    files = _list_json_files(service, folder_id)
    if not files:
        raise FileNotFoundError(
            f"No JSON files found in Google Drive folder '{folder_name}'."
        )
    return _download_file(service, files[0]["id"])


def get_health_exports_last_n_days(n: int) -> list:
    folder_name = os.environ.get("GOOGLE_DRIVE_FOLDER_NAME", "health-exports")
    service = _get_service()
    folder_id = _find_folder_id(service, folder_name)
    files = _list_json_files(service, folder_id)
    results = []
    for f in files[:n]:
        try:
            results.append(_download_file(service, f["id"]))
        except Exception as e:
            print(f"Warning: could not download {f['name']}: {e}")
    return results

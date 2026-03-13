import os
import json
import base64
import zipfile
from io import BytesIO

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
DAYS_TO_FETCH = 7


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


def _find_folder_id(service, folder_name: str, parent_id: str = None) -> str:
    """Find a folder by name, optionally scoped to a parent folder."""
    parent_clause = f"and '{parent_id}' in parents " if parent_id else ""
    query = (
        f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' "
        f"{parent_clause}and trashed = false"
    )
    result = service.files().list(q=query, fields="files(id, name)").execute()
    files = result.get("files", [])
    if not files:
        raise FileNotFoundError(f"Folder '{folder_name}' not found in Google Drive.")
    return files[0]["id"]


def _resolve_export_folder(service) -> str:
    """
    Resolve the folder containing daily export files.

    Health Auto Export creates: "Health Auto Export" / "Health-exports"
    GOOGLE_DRIVE_FOLDER_NAME can be overridden to point directly to the export folder.
    Falls back to searching for the nested structure automatically.
    """
    folder_name = os.environ.get("GOOGLE_DRIVE_FOLDER_NAME", "")

    if folder_name:
        # Try direct lookup first
        try:
            folder_id = _find_folder_id(service, folder_name)
            print(f"[Drive] Using folder: {folder_name}")
            return folder_id
        except FileNotFoundError:
            pass

    # Navigate the Health Auto Export nested structure
    print("[Drive] Navigating Health Auto Export → Health-exports")
    parent_id = _find_folder_id(service, "Health Auto Export")
    return _find_folder_id(service, "Health-exports", parent_id=parent_id)


def _list_export_files(service, folder_id: str) -> list:
    """Return all .zip and .json files in the folder, newest first."""
    query = f"'{folder_id}' in parents and trashed = false"
    result = service.files().list(
        q=query,
        orderBy="createdTime desc",
        fields="files(id, name, createdTime, mimeType)",
    ).execute()
    files = result.get("files", [])
    # Filter client-side by extension — Drive often assigns text/plain to .json uploads
    return [f for f in files if f["name"].endswith(".json") or f["name"].endswith(".zip")]


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

        if len(json_names) > 1:
            json_names.sort(key=lambda n: zf.getinfo(n).file_size, reverse=True)
            print(f"[Drive] ZIP contains {len(json_names)} JSON files — using largest: {json_names[0]}")
        else:
            print(f"[Drive] Extracting: {json_names[0]}")

        with zf.open(json_names[0]) as f:
            return json.loads(f.read().decode("utf-8"))


def _load_export(service, f: dict) -> dict:
    raw_bytes = _download_bytes(service, f["id"])
    if f["name"].endswith(".zip") or "zip" in f["mimeType"]:
        return _extract_json_from_zip(raw_bytes)
    return json.loads(raw_bytes.decode("utf-8"))


def _merge_daily_exports(exports: list) -> dict:
    """
    Merge multiple daily JSON exports into a single combined structure.

    Each daily file has: {"data": {"metrics": [...], "workouts": [...]}}
    We merge by combining each metric's data arrays and concatenating workouts.
    health_parser.py already handles multiple entries per metric via latest()
    and latest_day_sum(), so the merged structure gives rolling history.
    """
    merged_metrics: dict[str, dict] = {}  # metric name → {name, units, data: [...]}
    merged_workouts: list = []

    for export in exports:
        data = export.get("data", export)
        for metric in data.get("metrics", []):
            name = metric["name"]
            if name not in merged_metrics:
                merged_metrics[name] = {"name": name, "units": metric.get("units", ""), "data": []}
            merged_metrics[name]["data"].extend(metric.get("data", []))
        merged_workouts.extend(data.get("workouts", []))

    return {"data": {"metrics": list(merged_metrics.values()), "workouts": merged_workouts}}


def get_latest_health_export() -> dict:
    """
    Fetch and merge the last DAYS_TO_FETCH daily export files.
    Returns a single combined JSON structure for health_parser.py.
    """
    service = _get_service()
    folder_id = _resolve_export_folder(service)
    files = _list_export_files(service, folder_id)

    if not files:
        raise FileNotFoundError("No export files (.zip or .json) found in the health exports folder.")

    exports = []
    for f in files[:DAYS_TO_FETCH]:
        try:
            print(f"[Drive] Fetching: {f['name']} ({f['createdTime']})")
            exports.append(_load_export(service, f))
        except Exception as e:
            print(f"[Drive] Warning: could not process {f['name']}: {e}")

    if not exports:
        raise FileNotFoundError("No valid export files could be loaded.")

    print(f"[Drive] Merging {len(exports)} daily export(s)")
    return _merge_daily_exports(exports)


def get_health_exports_last_n_days(n: int) -> list:
    service = _get_service()
    folder_id = _resolve_export_folder(service)
    files = _list_export_files(service, folder_id)

    results = []
    for f in files[:n]:
        try:
            results.append(_load_export(service, f))
        except Exception as e:
            print(f"Warning: could not process {f['name']}: {e}")
    return results

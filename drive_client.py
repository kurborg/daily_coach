import os
import json
import base64
import zipfile
import time
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


def _resolve_export_folder(service, folder_id: str = "", folder_name: str = "") -> str:
    """
    Resolve the folder containing daily export files.

    If folder_id is given, return it immediately.
    Otherwise try folder_name as a direct lookup, then fall back to searching
    under the "Health Auto Export" parent folder (handles any subfolder name).
    """
    if folder_id:
        print(f"[Drive] Using folder_id: {folder_id}")
        return folder_id

    target = folder_name or "Health-exports"

    # Try direct (root-level) lookup first
    try:
        fid = _find_folder_id(service, target)
        print(f"[Drive] Using folder: {target}")
        return fid
    except FileNotFoundError:
        pass

    # Fall back to navigating under "Health Auto Export"
    print(f"[Drive] Navigating Health Auto Export → {target}")
    parent_id = _find_folder_id(service, "Health Auto Export")
    return _find_folder_id(service, target, parent_id=parent_id)


def _list_export_files(service, folder_id: str) -> list:
    """Return all .zip and .json files in the folder, newest first."""
    query = f"'{folder_id}' in parents and trashed = false"
    result = service.files().list(
        q=query,
        orderBy="createdTime desc",
        pageSize=1000,
        fields="files(id, name, createdTime, mimeType)",
    ).execute()
    files = result.get("files", [])
    print(f"[Drive] Found {len(files)} total file(s) in folder before filtering")
    if files:
        sample = files[:5]
        for f in sample:
            print(f"[Drive]   {f['name']} | mimeType={f['mimeType']}")
    # Filter client-side by extension — Drive often assigns text/plain to .json uploads
    filtered = [f for f in files if f["name"].endswith(".json") or f["name"].endswith(".zip")]
    print(f"[Drive] {len(filtered)} file(s) matched .json/.zip filter")
    return filtered


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


def get_latest_health_export(folder_id: str = "", folder_name: str = "", retries: int = 3, retry_delay: int = 60) -> dict:
    """
    Fetch and merge the last DAYS_TO_FETCH daily export files.
    Returns a single combined JSON structure for health_parser.py.

    Retries if the folder is temporarily empty (e.g. during a file rotation
    by the Health Auto Export app).
    """
    service = _get_service()
    resolved_folder_id = _resolve_export_folder(service, folder_id=folder_id, folder_name=folder_name)

    files = []
    for attempt in range(1, retries + 1):
        files = _list_export_files(service, resolved_folder_id)
        if files:
            break
        if attempt < retries:
            print(f"[Drive] No export files found (attempt {attempt}/{retries}). Retrying in {retry_delay}s...")
            time.sleep(retry_delay)

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


def get_latest_workout_export(folder_id: str = "", folder_name: str = "") -> list:
    """
    Fetch and merge workouts from the last DAYS_TO_FETCH workout export files.
    Returns a flat list of workout objects ready to inject into a health export.
    """
    service = _get_service()
    resolved_folder_id = _resolve_export_folder(service, folder_id=folder_id, folder_name=folder_name)
    files = _list_export_files(service, resolved_folder_id)

    if not files:
        print("[Drive] No workout export files found.")
        return []

    workouts = []
    for f in files[:DAYS_TO_FETCH]:
        try:
            print(f"[Drive] Fetching workout file: {f['name']}")
            export = _load_export(service, f)
            data = export.get("data", export)
            workouts.extend(data.get("workouts", []))
        except Exception as e:
            print(f"[Drive] Warning: could not process {f['name']}: {e}")

    print(f"[Drive] Found {len(workouts)} workout(s) from workout exports")
    return workouts


def get_health_exports_last_n_days(n: int, folder_id: str = "", folder_name: str = "") -> list:
    service = _get_service()
    resolved_folder_id = _resolve_export_folder(service, folder_id=folder_id, folder_name=folder_name)
    files = _list_export_files(service, resolved_folder_id)

    results = []
    for f in files[:n]:
        try:
            results.append(_load_export(service, f))
        except Exception as e:
            print(f"Warning: could not process {f['name']}: {e}")
    return results

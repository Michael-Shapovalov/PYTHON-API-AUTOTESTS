import os

import requests
from dotenv import load_dotenv


def main() -> int:
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    base = (os.getenv("TMS_URL") or "").rstrip("/")
    token = os.getenv("TMS_PRIVATE_TOKEN") or ""
    if not base or not token:
        print("Set TMS_URL and TMS_PRIVATE_TOKEN in .env")
        return 2

    url = f"{base}/api/v2/projects/search"
    headers = {
        "Authorization": f"PrivateToken {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {"take": 50, "skip": 0, "orderBy": [], "searchString": ""}
    r = requests.post(url, headers=headers, json=body, timeout=30)
    print("status:", r.status_code)
    r.raise_for_status()
    data = r.json()
    # Try common shapes: {items:[...]}, {projects:[...]}, list[...]
    items = None
    if isinstance(data, dict):
        for k in ("items", "projects", "data"):
            if isinstance(data.get(k), list):
                items = data[k]
                break
    if items is None and isinstance(data, list):
        items = data
    if not items:
        print("No projects returned. Response keys:", list(data.keys()) if isinstance(data, dict) else type(data))
        return 3

    print("First projects:")
    for p in items[:10]:
        if isinstance(p, dict):
            print("-", p.get("name"), "id:", p.get("id"))
        else:
            print("-", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


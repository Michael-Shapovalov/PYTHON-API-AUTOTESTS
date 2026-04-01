import configparser
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import requests

_ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tests.utils.testit_smoke_docs import get_smoke_tc_description  # noqa: E402


@dataclass(frozen=True)
class AutotestMeta:
    external_id: str
    display_name: str
    title: str
    description: str
    namespace: str
    class_name: str
    labels: list[str]
    steps: list[dict[str, Any]]


def _read_testit_config(ini_path: Path) -> dict[str, str]:
    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")
    if "testit" not in cp:
        raise RuntimeError(f"Missing [testit] section in {ini_path}")
    sec = cp["testit"]
    return {
        "url": (sec.get("url") or "").rstrip("/"),
        "token": sec.get("privateToken") or "",
        "project_id": sec.get("projectId") or "",
    }


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"PrivateToken {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _get_project_attributes(base_url: str, token: str, project_id: str) -> list[dict[str, Any]]:
    url = f"{base_url}/api/v2/projects/{project_id}/attributes"
    r = requests.get(url, headers=_headers(token), timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected attributes response shape: {type(data)}")
    return data


def _build_required_attributes_payload(attributes: list[dict[str, Any]]) -> dict[str, Any]:
    """
    TestIT can require custom attributes on autotest creation.
    Adapter 3.5.2 doesn't send them -> 400. We send them explicitly.

    Strategy:
    - for required attribute with options -> pick the FIRST option id
    - for required attribute without options -> set "auto"
    """
    payload: dict[str, Any] = {}
    missing: list[str] = []
    for a in attributes:
        if not a.get("isEnabled"):
            continue
        if not a.get("isRequired"):
            continue
        attr_id = a.get("id")
        if not attr_id:
            continue
        options = a.get("options") or []
        if isinstance(options, list) and options:
            opt0 = options[0]
            opt_id = opt0.get("id") if isinstance(opt0, dict) else None
            if opt_id:
                payload[attr_id] = opt_id
                continue
        # fallback – may still be invalid for some attribute types; we surface that as error
        payload[attr_id] = "auto"
        missing.append(str(a.get("name") or attr_id))
    # We don't fail here; API will tell us if "auto" is invalid
    return payload


def _get_autotest_by_external_id(base_url: str, token: str, project_id: str, external_id: str) -> Optional[dict[str, Any]]:
    url = f"{base_url}/api/v2/autoTests"
    params = {
        "projectId": project_id,
        "externalId": external_id,
        "take": 1,
        "skip": 0,
    }
    r = requests.get(url, headers=_headers(token), params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    # common shapes: {items:[...]} or list[...]
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        items = data["items"]
    elif isinstance(data, list):
        items = data
    else:
        return None
    return items[0] if items else None


def _create_autotest(base_url: str, token: str, project_id: str, meta: AutotestMeta, required_attrs: dict[str, Any]) -> dict[str, Any]:
    url = f"{base_url}/api/v2/autoTests"
    body = {
        "externalId": meta.external_id,
        "projectId": project_id,
        "name": meta.display_name,
        "namespace": meta.namespace,
        "className": meta.class_name,
        "title": meta.title,
        "description": meta.description,
        "steps": meta.steps,
        "labels": [{"name": x} for x in meta.labels],
        "shouldCreateWorkItem": True,  # create manual test case linked to this autotest
        "attributes": required_attrs,
    }
    r = requests.post(url, headers=_headers(token), json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Create autotest failed ({r.status_code}): {r.text}")
    return r.json() if r.text else {"status": r.status_code}


def _update_autotest(base_url: str, token: str, project_id: str, autotest_id: str, meta: AutotestMeta, required_attrs: dict[str, Any]) -> None:
    url = f"{base_url}/api/v2/autoTests"
    body = {
        "id": autotest_id,
        "externalId": meta.external_id,
        "projectId": project_id,
        "name": meta.display_name,
        "namespace": meta.namespace,
        "className": meta.class_name,
        "title": meta.title,
        "description": meta.description,
        "steps": meta.steps,
        "labels": [{"name": x} for x in meta.labels],
        "attributes": required_attrs,
    }
    r = requests.put(url, headers=_headers(token), json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Update autotest failed ({r.status_code}): {r.text}")


_RE_EXTERNAL = re.compile(r'@testit\.externalId\(\s*"([^"]+)"\s*\)')
_RE_DISPLAY = re.compile(r'@testit\.displayName\(\s*"([^"]+)"\s*\)')
_RE_TITLE = re.compile(r'@testit\.title\(\s*"([^"]+)"\s*\)')
_RE_NAMESPACE = re.compile(r'@testit\.nameSpace\(\s*"([^"]+)"\s*\)')
_RE_CLASSNAME = re.compile(r'@testit\.className\(\s*"([^"]+)"\s*\)')
_RE_LABELS = re.compile(r"@testit\.labels\(([^)]+)\)")
_RE_DESC_CALL = re.compile(r'@testit\.description\(\s*get_smoke_tc_description\(\s*"([^"]+)"\s*,\s*(\d+)\s*\)\s*\)')


def _parse_labels(raw: str) -> list[str]:
    # raw looks like: '"api", "smoke", "inventory"'
    return [s.strip().strip('"').strip("'") for s in raw.split(",") if s.strip()]


def _build_steps_from_description(desc: str) -> list[dict[str, Any]]:
    """
    Fill autotest.steps so TestIT library won't show "empty steps".
    Minimal robust approach: try to extract numbered steps; fallback to one step with whole description.
    """
    if not desc:
        return [{"title": "Шаги", "description": "Описание не задано"}]

    lines = [ln.rstrip() for ln in desc.splitlines()]
    step_lines: list[str] = []
    for ln in lines:
        s = ln.strip()
        if re.match(r"^\d+\.", s):
            step_lines.append(s)

    if step_lines:
        return [{"title": s.split(".", 1)[0].strip(), "description": s} for s in step_lines[:20]]

    # Fallback: a single step with full text
    return [{"title": "Описание", "description": desc[:4000]}]


def _extract_autotests_from_file(path: Path) -> list[AutotestMeta]:
    text = path.read_text(encoding="utf-8")
    # Parse by decorator block: find each @testit.externalId(...) and take the block until `def test_...`.
    metas: list[AutotestMeta] = []
    for m in _RE_EXTERNAL.finditer(text):
        start = m.start()
        # Find start of decorator block (nearest preceding line starting with '@')
        block_start = text.rfind("\n@", 0, start)
        if block_start == -1:
            block_start = max(0, start - 4000)
        # Find end of decorator block at next function definition
        def_pos = text.find("\ndef ", start)
        if def_pos == -1:
            def_pos = min(len(text), start + 8000)
        block = text[block_start:def_pos]
        external_id = m.group(1)

        display = _RE_DISPLAY.search(block)
        title = _RE_TITLE.search(block)
        ns = _RE_NAMESPACE.search(block)
        cn = _RE_CLASSNAME.search(block)
        labels_m = _RE_LABELS.search(block)
        desc_call = _RE_DESC_CALL.search(block)

        display_name = display.group(1) if display else external_id
        title_s = title.group(1) if title else display_name
        namespace = ns.group(1) if ns else "API/Smoke"
        class_name = cn.group(1) if cn else "Smoke"
        labels = _parse_labels(labels_m.group(1)) if labels_m else ["api", "smoke"]

        if desc_call:
            entity = desc_call.group(1)
            idx = int(desc_call.group(2))
            description = get_smoke_tc_description(entity, idx)
        else:
            description = ""

        steps = _build_steps_from_description(description)

        metas.append(
            AutotestMeta(
                external_id=external_id,
                display_name=display_name,
                title=title_s,
                description=description,
                namespace=namespace,
                class_name=class_name,
                labels=labels,
                steps=steps,
            )
        )
    return metas


def main() -> int:
    root = _ROOT
    ini = _ROOT / "connection_config.ini"
    cfg = _read_testit_config(ini)

    base_url = cfg["url"]
    token = cfg["token"]
    project_id = cfg["project_id"]
    if not base_url or not token or not project_id:
        print("Missing url/privateToken/projectId in connection_config.ini")
        return 2

    attrs = _get_project_attributes(base_url, token, project_id)
    required_attrs = _build_required_attributes_payload(attrs)
    print("Required attributes payload keys:", list(required_attrs.keys()))

    smoke_files = sorted((root / "tests" / "api").glob("**/smoke/test_*_smoke_flow.py"))
    all_metas: list[AutotestMeta] = []
    for f in smoke_files:
        all_metas.extend(_extract_autotests_from_file(f))

    print(f"Found autotests in code: {len(all_metas)}")

    created = 0
    updated = 0
    for meta in all_metas:
        existing = _get_autotest_by_external_id(base_url, token, project_id, meta.external_id)
        if existing and existing.get("id"):
            _update_autotest(base_url, token, project_id, existing["id"], meta, required_attrs)
            updated += 1
        else:
            _create_autotest(base_url, token, project_id, meta, required_attrs)
            created += 1

    print(f"Done. created={created}, updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


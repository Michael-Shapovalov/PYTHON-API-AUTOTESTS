import copy
import uuid
from typing import Optional

import pytest
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

from tests.api.warehousebin.client import WarehouseBinApiClient
from tests.utils import rt_metrics

SERVICE_NAME = "WarehouseBin"
DEFAULT_RT_CATEGORY = "rt_medium"


def _find_by(items, lookup_key: str, lookup_value) -> Optional[dict]:
    for item in items:
        if item.get(lookup_key) == lookup_value:
            return item
    return None


def build_unique_warehousebin_payload(warehouse_ref: dict, warehousebintype_ref: dict) -> dict:
    suffix = uuid.uuid4().hex[:12]
    code = f"WB{suffix}"[:30]
    name = f"Складская ячейка тест {suffix}"[:250]
    return {
        "integrationId": f"wb-smoke-{suffix}"[:100],
        "code": code,
        "name": name,
        "presentation": f"{code} {name}"[:350],
        "warehouse": warehouse_ref,
        "warehouseBinType": warehousebintype_ref,
        "identification": f"BIN-{suffix}"[:250],
        "pickingOrder": 0,
        "status": 0,
    }


def build_updated_payload_smoke(payload, id_suffix="-upd", max_id_len=250):
    payload_updated = copy.deepcopy(payload)
    ident_orig = payload_updated.get("identification") or ""
    ident_updated = (ident_orig + id_suffix)[:max_id_len]
    payload_updated["identification"] = ident_updated
    return payload_updated, ident_updated


def build_updated_payloads_smoke(payloads, id_suffix="-upd", max_id_len=250):
    payloads_updated = []
    identifications_updated = []
    for p in payloads:
        dup = copy.deepcopy(p)
        ident_orig = dup.get("identification") or ""
        ident_new = (ident_orig + id_suffix)[:max_id_len]
        dup["identification"] = ident_new
        payloads_updated.append(dup)
        identifications_updated.append(ident_new)
    return payloads_updated, identifications_updated


def _put(put_url: str, payload: dict, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME, "PUT", "/WarehouseBin/CreateOrUpdate", category,
        lambda: WarehouseBinApiClient.create_or_update(put_url, payload=payload, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _put_many(base_url: str, payloads, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME, "PUT", "/WarehouseBin/CreateOrUpdateMany", category,
        lambda: WarehouseBinApiClient.create_or_update_many(base_url, payloads=payloads, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _get_response(get_url: str, admin_auth, page_num=0, page_size=0, no_count=False, timeout=30):
    category = "rt_heavy"

    def _get():
        try:
            return WarehouseBinApiClient.get_list(get_url, auth=admin_auth, page_num=page_num, page_size=page_size, no_count=no_count, timeout=timeout)
        except (ConnectTimeout, RequestsConnectionError) as e:
            pytest.fail(f"GET /WarehouseBin: нет связи с сервером: {e}")

    return rt_metrics.timed_request(SERVICE_NAME, "GET", "/WarehouseBin", category, _get)


def _get_list(get_url: str, admin_auth, page_size=5000):
    response = _get_response(get_url, admin_auth, page_num=0, page_size=page_size, no_count=False, timeout=30)
    assert response.status_code == 200, f"GET /WarehouseBin: ожидался 200, получен {response.status_code}. {response.text}"
    data = response.json()
    return data.get("items") or []


def _patch_delete(base_url: str, body, auth=None, raw_body=None, timeout=30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME, "PATCH", "/WarehouseBin/Delete", category,
        lambda: WarehouseBinApiClient.delete(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _patch_delete_many(base_url: str, body, auth=None, raw_body=None, timeout=30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME, "PATCH", "/WarehouseBin/DeleteMany", category,
        lambda: WarehouseBinApiClient.delete_many(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _post_filter(post_url: str, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME, "POST", "/WarehouseBin", category,
        lambda: WarehouseBinApiClient.post_filter(post_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


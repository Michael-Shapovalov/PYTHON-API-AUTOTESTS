import copy
import uuid

import pytest
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

from tests.api.inventorystatus.client import InventoryStatusApiClient
from tests.utils import rt_metrics

SERVICE_NAME = "InventoryStatus"
DEFAULT_RT_CATEGORY = "rt_medium"


def _log_check(what: str, expected, actual):
    print(f"  Проверка: {what}: ожидаемый {expected} - фактический {actual}")


def build_unique_inventorystatus_payload():
    """
    Минимальный валидный payload InventoryStatus для smoke:
    - integrationId/code/name — уникальные;
    - все обязательные boolean-поля заданы явно.
    """
    suffix = uuid.uuid4().hex[:12]
    return {
        "integrationId": f"inv-status-smoke-{suffix}"[:100],
        "code": f"IS{suffix}"[:30],
        "name": f"Статус запаса тест {suffix}"[:250],
        "isAllowPicking": True,
        "isAvailableStock": True,
        "isForWarehouse": True,
        "isForWarehouseBin": False,
        "isForLot": False,
        "isForSerialNumber": False,
    }


def build_updated_payload_smoke(payload, name_suffix=" (обновлено)", max_name_len=250):
    payload_updated = copy.deepcopy(payload)
    name_orig = payload_updated.get("name") or ""
    name_updated = (name_orig + name_suffix)[:max_name_len]
    payload_updated["name"] = name_updated
    return payload_updated, name_updated


def build_updated_payloads_smoke(payloads, name_suffix=" (обновлено)", max_name_len=250):
    payloads_updated = []
    names_updated = []
    for p in payloads:
        dup = copy.deepcopy(p)
        name_orig = dup.get("name") or ""
        name_new = (name_orig + name_suffix)[:max_name_len]
        dup["name"] = name_new
        payloads_updated.append(dup)
        names_updated.append(name_new)
    return payloads_updated, names_updated


def _put_inventorystatus(put_url, payload=None, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/InventoryStatus/CreateOrUpdate",
        category,
        lambda: InventoryStatusApiClient.create_or_update(
            put_url, payload=payload, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _put_create_or_update_many(base_url, payloads, auth, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/InventoryStatus/CreateOrUpdateMany",
        category,
        lambda: InventoryStatusApiClient.create_or_update_many(
            base_url, payloads=payloads, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _get_response(get_url, admin_auth, page_num=0, page_size=0, no_count=False, timeout=30):
    category = "rt_heavy"

    def _get():
        try:
            return InventoryStatusApiClient.get_list(
                get_url,
                auth=admin_auth,
                page_num=page_num,
                page_size=page_size,
                no_count=no_count,
                timeout=timeout,
            )
        except (ConnectTimeout, RequestsConnectionError) as e:
            pytest.fail(f"GET /InventoryStatus: нет связи с сервером: {e}")

    return rt_metrics.timed_request(
        SERVICE_NAME, "GET", "/InventoryStatus", category, _get
    )


def _get_list(get_url, admin_auth, page_size=5000):
    response = _get_response(get_url, admin_auth, page_num=0, page_size=page_size, no_count=False, timeout=30)
    assert response.status_code == 200, f"GET /InventoryStatus: ожидался 200, получен {response.status_code}. {response.text}"
    data = response.json()
    return data.get("items") or []


def _find_by(items, lookup_key, lookup_value):
    for it in items:
        if it.get(lookup_key) == lookup_value:
            return it
    return None


def _post_filter(post_url, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "POST",
        "/InventoryStatus",
        category,
        lambda: InventoryStatusApiClient.post_filter(
            post_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _patch_delete(base_url, body, auth=None, raw_body=None, timeout=30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/InventoryStatus/Delete",
        category,
        lambda: InventoryStatusApiClient.delete(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _patch_delete_many(base_url, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/InventoryStatus/DeleteMany",
        category,
        lambda: InventoryStatusApiClient.delete_many(
            base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


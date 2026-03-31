import copy
import uuid

import pytest
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

from tests.api.inventorytransactiontype.client import InventoryTransactionTypeApiClient
from tests.utils import rt_metrics

SERVICE_NAME = "InventoryTransactionType"
DEFAULT_RT_CATEGORY = "rt_medium"


def _log_check(what: str, expected, actual):
    print(f"  Проверка: {what}: ожидаемый {expected} - фактический {actual}")


def build_unique_inventorytransactiontype_payload():
    """
    Минимальный валидный payload InventoryTransactionType для smoke:
    - integrationId/code/name — уникальные;
    - actionType=0 (ReceiptIntoInventory), sourceType=0 (Inventory);
    - isDefault=false; isFor* = false.
    """
    suffix = uuid.uuid4().hex[:12]
    return {
        "integrationId": f"inv-txn-type-smoke-{suffix}"[:100],
        "code": f"ITT{suffix}"[:30],
        "name": f"Тип складской операции тест {suffix}"[:250],
        "isDefault": False,
        "actionType": 0,
        "sourceType": 0,
        "description": f"Smoke описание {suffix}"[:500],
        "isForPicking": False,
        "isForComponentIssue": False,
        "isForProductCompletion": False,
        "isForProductReturn": False,
        "isForWIPProductScrap": False,
    }


def build_updated_payload_smoke(payload, name_suffix=" (обновлено)", max_name_len=250):
    """Копия payload с обновлённым name для smoke update. Возвращает (payload_updated, name_updated_str)."""
    payload_updated = copy.deepcopy(payload)
    name_orig = payload_updated.get("name") or ""
    name_updated = (name_orig + name_suffix)[:max_name_len]
    payload_updated["name"] = name_updated
    return payload_updated, name_updated


def build_updated_payloads_smoke(payloads, name_suffix=" (обновлено)", max_name_len=250):
    """Список копий payloads с обновлённым name для smoke update many. Возвращает (payloads_updated, names_updated)."""
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


def _put_inventorytransactiontype(put_url, payload=None, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/InventoryTransactionType/CreateOrUpdate",
        category,
        lambda: InventoryTransactionTypeApiClient.create_or_update(
            put_url, payload=payload, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _put_create_or_update_many(base_url, payloads, auth, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/InventoryTransactionType/CreateOrUpdateMany",
        category,
        lambda: InventoryTransactionTypeApiClient.create_or_update_many(
            base_url, payloads=payloads, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _get_response(get_url, admin_auth, page_num=0, page_size=0, no_count=False, timeout=30):
    category = "rt_heavy"

    def _get():
        try:
            return InventoryTransactionTypeApiClient.get_list(
                get_url,
                auth=admin_auth,
                page_num=page_num,
                page_size=page_size,
                no_count=no_count,
                timeout=timeout,
            )
        except (ConnectTimeout, RequestsConnectionError) as e:
            pytest.fail(f"GET /InventoryTransactionType: нет связи с сервером: {e}")

    return rt_metrics.timed_request(
        SERVICE_NAME, "GET", "/InventoryTransactionType", category, _get
    )


def _get_list(get_url, admin_auth, page_size=5000):
    response = _get_response(
        get_url,
        admin_auth,
        page_num=0,
        page_size=page_size,
        no_count=False,
        timeout=30,
    )
    assert response.status_code == 200, (
        f"GET /InventoryTransactionType: ожидался 200, получен {response.status_code}. {response.text}"
    )
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
        "/InventoryTransactionType",
        category,
        lambda: InventoryTransactionTypeApiClient.post_filter(
            post_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _patch_delete(base_url, body, auth=None, raw_body=None, timeout=30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/InventoryTransactionType/Delete",
        category,
        lambda: InventoryTransactionTypeApiClient.delete(
            base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _patch_delete_many(base_url, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/InventoryTransactionType/DeleteMany",
        category,
        lambda: InventoryTransactionTypeApiClient.delete_many(
            base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


import copy
import uuid

import pytest
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

from tests.api.inventorystatustransactiontype.client import (
    InventoryStatusTransactionTypeApiClient,
)
from tests.utils import rt_metrics

SERVICE_NAME = "InventoryStatusTransactionType"
DEFAULT_RT_CATEGORY = "rt_medium"


def _log_check(what: str, expected, actual):
    print(f"  Проверка: {what}: ожидаемый {expected} - фактический {actual}")


def build_unique_inventorystatustransactiontype_payload(inventory_status_ref, inventory_transaction_type_ref):
    """
    Минимальный payload InventoryStatusTransactionType для smoke:
    - integrationId — уникальный;
    - ссылки на InventoryStatus и InventoryTransactionType по id;
    - isNotAllowed — boolean.
    """
    suffix = uuid.uuid4().hex[:12]
    return {
        "integrationId": f"inv-status-txn-smoke-{suffix}"[:100],
        "inventoryStatus": inventory_status_ref,
        "inventoryTransactionType": inventory_transaction_type_ref,
        "isNotAllowed": False,
    }


def build_updated_payload_smoke(payload):
    """Копия payload с переключённым isNotAllowed для smoke update. Возвращает (payload_updated, is_not_allowed_new)."""
    payload_updated = copy.deepcopy(payload)
    new_val = not bool(payload_updated.get("isNotAllowed", False))
    payload_updated["isNotAllowed"] = new_val
    return payload_updated, new_val


def build_updated_payloads_smoke(payloads):
    """Список копий payloads со сменой isNotAllowed. Возвращает (payloads_updated, values_new)."""
    payloads_updated = []
    values_new = []
    for p in payloads:
        dup = copy.deepcopy(p)
        new_val = not bool(dup.get("isNotAllowed", False))
        dup["isNotAllowed"] = new_val
        payloads_updated.append(dup)
        values_new.append(new_val)
    return payloads_updated, values_new


def _put_one(put_url, payload=None, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/InventoryStatusTransactionType/CreateOrUpdate",
        category,
        lambda: InventoryStatusTransactionTypeApiClient.create_or_update(
            put_url, payload=payload, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _put_many(base_url, payloads, auth, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/InventoryStatusTransactionType/CreateOrUpdateMany",
        category,
        lambda: InventoryStatusTransactionTypeApiClient.create_or_update_many(
            base_url, payloads=payloads, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _get_response(get_url, admin_auth, page_num=0, page_size=0, no_count=False, timeout=30):
    category = "rt_heavy"

    def _get():
        try:
            return InventoryStatusTransactionTypeApiClient.get_list(
                get_url,
                auth=admin_auth,
                page_num=page_num,
                page_size=page_size,
                no_count=no_count,
                timeout=timeout,
            )
        except (ConnectTimeout, RequestsConnectionError) as e:
            pytest.fail(f"GET /InventoryStatusTransactionType: нет связи с сервером: {e}")

    return rt_metrics.timed_request(
        SERVICE_NAME, "GET", "/InventoryStatusTransactionType", category, _get
    )


def _get_list(get_url, admin_auth, page_size=5000):
    response = _get_response(get_url, admin_auth, page_num=0, page_size=page_size, no_count=False, timeout=30)
    assert response.status_code == 200, (
        f"GET /InventoryStatusTransactionType: ожидался 200, получен {response.status_code}. {response.text}"
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
        "/InventoryStatusTransactionType",
        category,
        lambda: InventoryStatusTransactionTypeApiClient.post_filter(
            post_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _patch_delete(base_url, body, auth=None, raw_body=None, timeout=30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/InventoryStatusTransactionType/Delete",
        category,
        lambda: InventoryStatusTransactionTypeApiClient.delete(
            base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _patch_delete_many(base_url, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/InventoryStatusTransactionType/DeleteMany",
        category,
        lambda: InventoryStatusTransactionTypeApiClient.delete_many(
            base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


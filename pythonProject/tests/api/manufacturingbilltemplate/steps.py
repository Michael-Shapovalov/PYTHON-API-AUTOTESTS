import copy
import uuid
from typing import Optional

import pytest
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

from tests.api.manufacturingbilltemplate.client import ManufacturingBillTemplateApiClient
from tests.utils import rt_metrics

SERVICE_NAME = "ManufacturingBillTemplate"
DEFAULT_RT_CATEGORY = "rt_medium"


def _find_mbt_by(items, lookup_key: str, lookup_value) -> Optional[dict]:
    for item in items:
        if item.get(lookup_key) == lookup_value:
            return item
    return None


def build_unique_manufacturingbilltemplate_payload() -> dict:
    """
    Минимально валидный payload ManufacturingBillTemplate для smoke:
    - уникальные integrationId/code/name;
    - presentation = <Code> <Name>;
    - isDefault=false, status=Draft, PositionNumberingStep>0.
    """
    suffix = uuid.uuid4().hex[:12]
    code = f"MBT{suffix}"[:30]
    name = f"Шаблон спецификации тест {suffix}"[:250]
    presentation = f"{code} {name}"[:350]
    return {
        "integrationId": f"mbt-smoke-{suffix}"[:100],
        "code": code,
        "name": name,
        "presentation": presentation,
        "isDefault": False,
        "positionNumberingStep": 10,
        "status": 0,  # Draft
    }


def build_updated_payload_smoke(payload: dict, name_suffix: str = " (обновлено)", max_name_len: int = 250):
    """Копия payload с обновлённым name и recalculated presentation."""
    payload_updated = copy.deepcopy(payload)
    name_orig = payload_updated.get("name") or ""
    name_updated = (name_orig + name_suffix)[:max_name_len]
    payload_updated["name"] = name_updated
    payload_updated["presentation"] = f"{payload_updated.get('code', '')} {name_updated}"[:350]
    return payload_updated, name_updated


def build_updated_payloads_smoke(payloads, name_suffix: str = " (обновлено)", max_name_len: int = 250):
    """Список копий payloads с обновлёнными name и recalculated presentation."""
    payloads_updated = []
    names_updated = []
    for p in payloads:
        dup = copy.deepcopy(p)
        name_orig = dup.get("name") or ""
        name_new = (name_orig + name_suffix)[:max_name_len]
        dup["name"] = name_new
        dup["presentation"] = f"{dup.get('code', '')} {name_new}"[:350]
        payloads_updated.append(dup)
        names_updated.append(name_new)
    return payloads_updated, names_updated


def _put_mbt(put_url: str, payload: dict, auth=None, raw_body=None, timeout: int = 30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/ManufacturingBillTemplate/CreateOrUpdate",
        category,
        lambda: ManufacturingBillTemplateApiClient.create_or_update(
            put_url, payload=payload, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _put_create_or_update_many(base_url: str, payloads, auth=None, raw_body=None, timeout: int = 30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/ManufacturingBillTemplate/CreateOrUpdateMany",
        category,
        lambda: ManufacturingBillTemplateApiClient.create_or_update_many(
            base_url, payloads=payloads, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _get_mbt_response(get_url: str, admin_auth, page_num: int = 0, page_size: int = 0, no_count: bool = False, timeout: int = 30):
    category = "rt_heavy"  # GET — heavy

    def _get():
        try:
            return ManufacturingBillTemplateApiClient.get_manufacturingbilltemplate(
                get_url,
                auth=admin_auth,
                page_num=page_num,
                page_size=page_size,
                no_count=no_count,
                timeout=timeout,
            )
        except (ConnectTimeout, RequestsConnectionError) as e:
            pytest.fail(f"GET /ManufacturingBillTemplate: нет связи с сервером: {e}")

    return rt_metrics.timed_request(SERVICE_NAME, "GET", "/ManufacturingBillTemplate", category, _get)


def _get_mbt_list(get_url: str, admin_auth, page_size: int = 5000):
    response = _get_mbt_response(get_url, admin_auth, page_num=0, page_size=page_size, no_count=False, timeout=30)
    assert response.status_code == 200, f"GET /ManufacturingBillTemplate: ожидался 200, получен {response.status_code}. {response.text}"
    data = response.json()
    return data.get("items") or []


def _patch_delete(base_url: str, body, auth=None, raw_body=None, timeout: int = 30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/ManufacturingBillTemplate/Delete",
        category,
        lambda: ManufacturingBillTemplateApiClient.delete(
            base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _patch_delete_many(base_url: str, body, auth=None, raw_body=None, timeout: int = 30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/ManufacturingBillTemplate/DeleteMany",
        category,
        lambda: ManufacturingBillTemplateApiClient.delete_many(
            base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


def _post_mbt(post_url: str, body, auth=None, raw_body=None, timeout: int = 30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "POST",
        "/ManufacturingBillTemplate",
        category,
        lambda: ManufacturingBillTemplateApiClient.post_manufacturingbilltemplate(
            post_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout
        ),
    )


import copy
import uuid
from typing import Optional

import pytest
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

from tests.api.processoperation.client import ProcessOperationApiClient
from tests.utils import rt_metrics

SERVICE_NAME = "ProcessOperation"
DEFAULT_RT_CATEGORY = "rt_heavy"


def _find_processoperation_by(items, lookup_key: str, lookup_value) -> Optional[dict]:
    for item in items:
        if item.get(lookup_key) == lookup_value:
            return item
    return None


def build_unique_processoperation_payload(process_segment_ref: dict, shop_floor_ref: dict, shop_floor_area_ref: dict) -> dict:
    """
    Минимально валидный payload ProcessOperation для smoke:
    - уникальный integrationId;
    - уникальные Number и NumberInProcess внутри одного ProcessSegment (есть уникальные индексы в БД);
    - обязательные ссылки: ProcessSegment, ShopFloor, ShopFloorArea (фиксированные id, без доп. запросов).

    Вложенные позиции (material/equipment/labour/tooling) намеренно НЕ передаём (решение для smoke).
    """
    suffix = uuid.uuid4().hex[:12]

    number = int(suffix[:6], 16) % 9000 + 1000
    number_in_process = suffix[-3:].upper()
    name = f"Smoke ProcessOperation {suffix}"[:250]

    return {
        "integrationId": f"po-smoke-{suffix}"[:100],
        "processSegment": process_segment_ref,
        "shopFloor": shop_floor_ref,
        "shopFloorArea": shop_floor_area_ref,
        # Обязательная ссылка (по валидации API). Используем фиксированный id без доп. запросов.
        "manufacturingOperationType": {"id": 2},
        # Совместимость: на части окружений бэкенд ожидает PascalCase поля.
        "ManufacturingOperationType": {"id": 2},
        "number": number,
        "numberInProcess": number_in_process,
        "name": name,
        "isSubcontracted": False,
        "confirmationStages": 3,  # Worker + Master
        "ConfirmationStages": 3,
        "kindOfActualAccounting": 0,  # Piecework
        "rateTypeForSetup": 1,  # PerLot
        "rateForSetupTime": 0,
        "rateTypeForProcessing": 0,  # PerUnit
        "rateForProcessingTime": 0,
        "rateTypeForTeardown": 1,  # PerLot
        "rateForTeardownTime": 0,
        "calculateRateForProcessingTime": True,
        "grade": 0,
        "labourQty": 1,
        "numberOfItemsSimultaneouslyProcessed": 1,
        "productivityFactor": 1,
        "rateForAuxiliaryTime": 0,
        "rateForMachineTime": 0,
        "rateForWaitingTime": 0,
        "rateForIdleTime": 0,
        "rateForTransportTime": 0,
    }


def build_updated_payload_smoke(payload: dict, name_suffix: str = " (обновлено)", max_name_len: int = 250):
    payload_updated = copy.deepcopy(payload)
    name_orig = payload_updated.get("name") or ""
    name_updated = (name_orig + name_suffix)[:max_name_len]
    payload_updated["name"] = name_updated
    return payload_updated, name_updated


def build_updated_payloads_smoke(payloads, name_suffix: str = " (обновлено)", max_name_len: int = 250):
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


def _put_processoperation(put_url: str, payload: dict, auth=None, raw_body=None, timeout: int = 30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/ProcessOperation/CreateOrUpdate",
        category,
        lambda: ProcessOperationApiClient.create_or_update(put_url, payload=payload, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _put_create_or_update_many(base_url: str, payloads, auth=None, raw_body=None, timeout: int = 30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/ProcessOperation/CreateOrUpdateMany",
        category,
        lambda: ProcessOperationApiClient.create_or_update_many(base_url, payloads=payloads, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _get_processoperation_response(get_url: str, admin_auth, page_num: int = 0, page_size: int = 0, no_count: bool = False, timeout: int = 30):
    category = "rt_heavy"

    def _get():
        try:
            return ProcessOperationApiClient.get_processoperation(
                get_url,
                auth=admin_auth,
                page_num=page_num,
                page_size=page_size,
                no_count=no_count,
                timeout=timeout,
            )
        except (ConnectTimeout, RequestsConnectionError) as e:
            pytest.fail(f"GET /ProcessOperation: нет связи с сервером: {e}")

    return rt_metrics.timed_request(SERVICE_NAME, "GET", "/ProcessOperation", category, _get)


def _get_processoperation_list(get_url: str, admin_auth, page_size: int = 5000):
    response = _get_processoperation_response(get_url, admin_auth, page_num=0, page_size=page_size, no_count=False, timeout=30)
    assert response.status_code == 200, f"GET /ProcessOperation: ожидался 200, получен {response.status_code}. {response.text}"
    data = response.json()
    return data.get("items") or []


def _patch_delete(base_url: str, body, auth=None, raw_body=None, timeout: int = 30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/ProcessOperation/Delete",
        category,
        lambda: ProcessOperationApiClient.delete(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _patch_delete_many(base_url: str, body, auth=None, raw_body=None, timeout: int = 30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/ProcessOperation/DeleteMany",
        category,
        lambda: ProcessOperationApiClient.delete_many(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _post_processoperation(post_url: str, body, auth=None, raw_body=None, timeout: int = 30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "POST",
        "/ProcessOperation",
        category,
        lambda: ProcessOperationApiClient.post_processoperation(post_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


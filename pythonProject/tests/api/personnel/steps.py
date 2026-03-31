import copy
import uuid

import pytest
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

from tests.api.personnel.client import PersonnelApiClient
from tests.utils import rt_metrics

SERVICE_NAME = "Personnel"
DEFAULT_RT_CATEGORY = "rt_heavy"


def _log_check(what: str, expected, actual):
    print(f"  Проверка: {what}: ожидаемый {expected} - фактический {actual}")


def build_unique_personnel_payload(production_unit_ref, profession_ref):
    """
    Минимальный валидный payload Personnel для smoke:
    - уникальный integrationId/code/name/ФИО;
    - одна базовая локация (PersonnelLocation);
    - одна базовая квалификация (PersonnelQualification).
    """
    suffix = uuid.uuid4().hex[:12]
    first_name = f"Иван{suffix[:4]}"
    last_name = f"Иванов{suffix[:4]}"
    full_name = f"{last_name} {first_name} Тест"
    return {
        "integrationId": f"pers-smoke-{suffix}"[:100],
        "code": f"PERS{suffix}"[:30],
        "name": full_name[:250],
        "firstName": first_name[:50],
        "lastName": last_name[:50],
        "patronymic": "Тестович",
        "status": 0,
        "isMaster": False,
        "personnelLocations": [
            {
                "id": 0,
                "integrationId": f"pers-loc-{suffix}"[:100],
                "personnel": {"id": 0},
                "productionUnit": production_unit_ref,
                "validFrom": "2025-01-01T00:00:00",
                "validTo": "2030-12-31T23:59:59",
                "isBasic": True,
                "isPermanent": True,
                "presentation": "Основное место работы",
            }
        ],
        "personnelQualifications": [
            {
                "id": 0,
                "integrationId": f"pers-qual-{suffix}"[:100],
                "personnel": {"id": 0},
                "profession": profession_ref,
                "grade": 1,
                "isBasic": True,
                "status": 0,
                "presentation": "Тестовая квалификация 1 разряд",
            }
        ],
    }


def build_updated_payload_smoke(payload, name_suffix=" (обновлено)", max_name_len=250):
    """Копия payload Personnel с обновлённым name/FullName для smoke update. Возвращает (payload_updated, name_updated_str)."""
    payload_updated = copy.deepcopy(payload)
    name_orig = payload_updated.get("name") or payload_updated.get("fullName") or ""
    name_updated = (name_orig + name_suffix)[:max_name_len]
    payload_updated["name"] = name_updated
    payload_updated["fullName"] = name_updated
    return payload_updated, name_updated


def build_updated_payloads_smoke(payloads, name_suffix=" (обновлено)", max_name_len=250):
    """Список копий payloads Personnel с обновлённым name/fullName. Возвращает (payloads_updated, names_updated)."""
    payloads_updated = []
    names_updated = []
    for p in payloads:
        dup = copy.deepcopy(p)
        name_orig = dup.get("name") or dup.get("fullName") or ""
        name_new = (name_orig + name_suffix)[:max_name_len]
        dup["name"] = name_new
        dup["fullName"] = name_new
        payloads_updated.append(dup)
        names_updated.append(name_new)
    return payloads_updated, names_updated


def _put_personnel(put_url, payload=None, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/Personnel/CreateOrUpdate",
        category,
        lambda: PersonnelApiClient.create_or_update(put_url, payload=payload, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _get_personnel_response(get_url, admin_auth, page_num=0, page_size=0, no_count=False, timeout=30):
    category = "rt_heavy"

    def _get():
        try:
            return PersonnelApiClient.get_personnel(
                get_url,
                auth=admin_auth,
                page_num=page_num,
                page_size=page_size,
                no_count=no_count,
                timeout=timeout,
            )
        except (ConnectTimeout, RequestsConnectionError) as e:
            pytest.fail(f"GET /Personnel: нет связи с сервером: {e}")

    return rt_metrics.timed_request(SERVICE_NAME, "GET", "/Personnel", category, _get)


def _get_personnel_list(get_url, admin_auth, page_size=5000):
    response = _get_personnel_response(get_url, admin_auth, page_num=0, page_size=page_size, no_count=False, timeout=30)
    assert response.status_code == 200, f"GET /Personnel: ожидался 200, получен {response.status_code}. {response.text}"
    data = response.json()
    return data.get("items") or []


def _find_personnel_by(items, lookup_key, lookup_value):
    for p in items:
        if p.get(lookup_key) == lookup_value:
            return p
    return None


def _patch_delete(base_url, body, auth=None, raw_body=None, timeout=30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/Personnel/Delete",
        category,
        lambda: PersonnelApiClient.delete(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _patch_delete_many(base_url, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/Personnel/DeleteMany",
        category,
        lambda: PersonnelApiClient.delete_many(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _put_create_or_update_many(base_url, payloads, auth, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/Personnel/CreateOrUpdateMany",
        category,
        lambda: PersonnelApiClient.create_or_update_many(base_url, payloads=payloads, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _post_personnel(post_url, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "POST",
        "/Personnel",
        category,
        lambda: PersonnelApiClient.post_personnel(post_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


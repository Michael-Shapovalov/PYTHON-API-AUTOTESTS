import copy
import uuid
from typing import Optional

import pytest
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

from tests.api.company.client import CompanyApiClient
from tests.utils import rt_metrics

SERVICE_NAME = "Company"
DEFAULT_RT_CATEGORY = "rt_medium"


def _find_company_by(items, lookup_key: str, lookup_value) -> Optional[dict]:
    for item in items:
        if item.get(lookup_key) == lookup_value:
            return item
    return None


def build_unique_company_payload(contractor_ref: dict) -> dict:
    suffix = uuid.uuid4().hex[:12]
    code = f"COMP{suffix}"[:30]
    name = f"Организация тест {suffix}"[:250]
    return {
        "integrationId": f"company-smoke-{suffix}"[:100],
        "code": code,
        "name": name,
        "presentation": f"{code} {name}"[:350],
        "contractor": contractor_ref,
        "status": 0,
    }


def build_updated_payload_smoke(payload, name_suffix=" (обновлено)", max_name_len=250):
    payload_updated = copy.deepcopy(payload)
    name_orig = payload_updated.get("name") or ""
    name_updated = (name_orig + name_suffix)[:max_name_len]
    payload_updated["name"] = name_updated
    payload_updated["presentation"] = f"{payload_updated.get('code', '')} {name_updated}"[:350]
    return payload_updated, name_updated


def build_updated_payloads_smoke(payloads, name_suffix=" (обновлено)", max_name_len=250):
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


def _put_company(put_url: str, payload=None, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/Company/CreateOrUpdate",
        category,
        lambda: CompanyApiClient.create_or_update(put_url, payload=payload, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _put_create_or_update_many(base_url: str, payloads, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PUT",
        "/Company/CreateOrUpdateMany",
        category,
        lambda: CompanyApiClient.create_or_update_many(base_url, payloads=payloads, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _get_company_response(get_url: str, admin_auth, page_num=0, page_size=0, no_count=False, timeout=30):
    category = "rt_heavy"

    def _get():
        try:
            return CompanyApiClient.get_list(
                get_url,
                auth=admin_auth,
                page_num=page_num,
                page_size=page_size,
                no_count=no_count,
                timeout=timeout,
            )
        except (ConnectTimeout, RequestsConnectionError) as e:
            pytest.fail(f"GET /Company: нет связи с сервером: {e}")

    return rt_metrics.timed_request(SERVICE_NAME, "GET", "/Company", category, _get)


def _get_company_list(get_url: str, admin_auth, page_size=5000):
    response = _get_company_response(get_url, admin_auth, page_num=0, page_size=page_size, no_count=False, timeout=30)
    assert response.status_code == 200, f"GET /Company: ожидался 200, получен {response.status_code}. {response.text}"
    data = response.json()
    return data.get("items") or []


def _patch_delete(base_url: str, body, auth=None, raw_body=None, timeout=30):
    category = "rt_heavy"
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/Company/Delete",
        category,
        lambda: CompanyApiClient.delete(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _patch_delete_many(base_url: str, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "PATCH",
        "/Company/DeleteMany",
        category,
        lambda: CompanyApiClient.delete_many(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _post_company(post_url: str, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME,
        "POST",
        "/Company",
        category,
        lambda: CompanyApiClient.post_filter(post_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


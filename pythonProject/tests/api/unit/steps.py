import copy
import json
import os
import random
import uuid
from typing import Optional

import jsonschema
import pytest
from jsonref import replace_refs
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

from tests.api.unit.client import UnitApiClient
from tests.utils import rt_metrics

SERVICE_NAME = "Unit"
DEFAULT_RT_CATEGORY = "rt_light"

CREATE_OR_UPDATE_SCHEMA_NAME = "RestResponseDtoOfRestUnit"
GET_SCHEMA_NAME = "PaginatedListOfRestUnit"


def _log_check(what: str, expected, actual):
    print(f"  Проверка: {what}: ожидаемый {expected} - фактический {actual}")


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _openapi_nullable_to_jsonschema(schema: dict) -> dict:
    if not isinstance(schema, dict):
        return schema
    out = {}
    for key, value in schema.items():
        if key == "nullable" and value is True:
            continue
        if key == "type" and schema.get("nullable") is True:
            out[key] = [value, "null"] if isinstance(value, str) else list(value) + ["null"]
            continue
        if isinstance(value, dict):
            out[key] = _openapi_nullable_to_jsonschema(value)
        elif isinstance(value, list):
            out[key] = [_openapi_nullable_to_jsonschema(item) if isinstance(item, dict) else item for item in value]
        else:
            out[key] = value
    return out


def _merge_allof(schema: dict) -> dict:
    if not isinstance(schema, dict):
        return schema
    if "oneOf" in schema and len(schema["oneOf"]) == 1:
        return _merge_allof(copy.deepcopy(schema["oneOf"][0]))
    if "allOf" not in schema:
        out = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                out[key] = _merge_allof(value)
            elif key == "items" and isinstance(value, dict):
                out[key] = _merge_allof(value)
            else:
                out[key] = value
        return out
    merged = {"type": "object", "properties": {}, "additionalProperties": False}
    for part in schema["allOf"]:
        part = _merge_allof(copy.deepcopy(part))
        if isinstance(part, dict) and "properties" in part:
            for prop_key, prop_val in part["properties"].items():
                merged["properties"][prop_key] = _merge_allof(prop_val) if isinstance(prop_val, dict) else prop_val
    return merged


def _load_swagger_schema(schema_name: str) -> dict:
    swagger_path = os.path.join(_project_root(), "swagger.json")
    if not os.path.isfile(swagger_path):
        raise FileNotFoundError(f"swagger.json не найден: {swagger_path}")
    with open(swagger_path, encoding="utf-8") as f:
        swagger = json.load(f)
    swagger_resolved = replace_refs(swagger, proxies=False)
    schema = copy.deepcopy(swagger_resolved["components"]["schemas"][schema_name])
    schema = _openapi_nullable_to_jsonschema(schema)
    return _merge_allof(schema)


def get_unit_create_or_update_response_schema() -> dict:
    return _load_swagger_schema(CREATE_OR_UPDATE_SCHEMA_NAME)


def get_unit_get_response_schema() -> dict:
    return _load_swagger_schema(GET_SCHEMA_NAME)


def _unique_suffix() -> str:
    return uuid.uuid4().hex[:12]


def build_unique_unit_payload() -> dict:
    suffix = _unique_suffix()
    return {
        "integrationId": f"unit-test-{suffix}"[:100],
        "code": f"U{suffix}"[:30],
        "name": f"Ед. изм. тест {suffix}"[:250],
        "acronym": f"u{suffix[:8]}"[:10],
        "measurementCode": str(random.randint(100, 999)),
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


def _random_integration_id_validation_value() -> str:
    return f"val-{_unique_suffix()}"


def _put_unit(put_url: str, payload=None, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME, "PUT", "/Unit/CreateOrUpdate", category,
        lambda: UnitApiClient.create_or_update(put_url, payload=payload, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _get_unit_response(get_url, admin_auth, page_num=0, page_size=0, no_count=False, timeout=30):
    category = "rt_heavy"  # GET — тяжёлый по времени, лимит 5 с
    def _get():
        try:
            return UnitApiClient.get_units(
                get_url,
                auth=admin_auth,
                page_num=page_num,
                page_size=page_size,
                no_count=no_count,
                timeout=timeout,
            )
        except (ConnectTimeout, RequestsConnectionError) as e:
            pytest.fail(f"GET /Unit: нет связи с сервером: {e}")
    return rt_metrics.timed_request(SERVICE_NAME, "GET", "/Unit", category, _get)


def _get_units_list(get_url, admin_auth, page_size=1000):
    response = _get_unit_response(get_url, admin_auth, page_num=0, page_size=page_size, no_count=False, timeout=30)
    assert response.status_code == 200, f"GET /Unit: ожидался 200, получен {response.status_code}. {response.text}"
    data = response.json()
    return data.get("items") or []


def _find_unit_by(items, lookup_key: str, lookup_value) -> Optional[dict]:
    for unit in items:
        if unit.get(lookup_key) == lookup_value:
            return unit
    return None


def _post_unit(post_url, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME, "POST", "/Unit", category,
        lambda: UnitApiClient.post_units(post_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _put_create_or_update_many(base_url, payloads, auth, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME, "PUT", "/Unit/CreateOrUpdateMany", category,
        lambda: UnitApiClient.create_or_update_many(base_url, payloads=payloads, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _patch_delete(base_url, body, auth=None, raw_body=None, timeout=30):
    category = "rt_heavy"  # PATCH /Unit/Delete — тяжёлый по времени, лимит 7 с
    return rt_metrics.timed_request(
        SERVICE_NAME, "PATCH", "/Unit/Delete", category,
        lambda: UnitApiClient.delete(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _patch_delete_many(base_url, body, auth=None, raw_body=None, timeout=30):
    category = rt_metrics.get_rt_category(DEFAULT_RT_CATEGORY)
    return rt_metrics.timed_request(
        SERVICE_NAME, "PATCH", "/Unit/DeleteMany", category,
        lambda: UnitApiClient.delete_many(base_url, body=body, auth=auth, raw_body=raw_body, timeout=timeout),
    )


def _assert_error_response(response, expected_status_range=(400, 499)):
    _log_check("статус ответа (ожидается ошибка)", "4xx или ошибка в results", response.status_code)
    if expected_status_range[0] <= response.status_code <= expected_status_range[1]:
        return
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get("added") == 1:
                pytest.fail(f"Ожидалась ошибка, но получен успех: added=1. Тело: {response.text}")
            results = data.get("results") or []
            if results and isinstance(results[0], dict):
                err = results[0].get("errorMessage") or results[0].get("error") or results[0].get("message") or str(results[0])
                if err:
                    return
        except Exception:
            pass
        pytest.fail(f"Ожидалась ошибка (4xx или ошибка в results), но получен 200. Тело: {response.text}")
    pytest.fail(f"Ожидался статус 4xx или 200 с ошибкой в results. Получен: {response.status_code}. Тело: {response.text}")


def _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url, *, full_check=True):
    try:
        response = _put_unit(put_url, payload=payload, auth=admin_auth)
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"Нет связи с сервером: {e}. URL: {put_url}.")
    if response.status_code != 200:
        err_body = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        _log_check("код ответа PUT /Unit/CreateOrUpdate", 200, response.status_code)
        pytest.fail(f"Ожидаемый код 200 - фактический {response.status_code}. Response: {err_body}")
    _log_check("код ответа PUT /Unit/CreateOrUpdate", 200, response.status_code)

    data = response.json()
    has_results = "results" in data
    _log_check("наличие поля 'results' в ответе", True, has_results)
    assert has_results, f"Ожидалось 'results' в ответе. Ключи: {list(data.keys())}"
    added_val = data.get("added")
    updated_val = data.get("updated")
    _log_check("added в ответе", 1, added_val)
    _log_check("updated в ответе", "0 или 1", updated_val)
    assert (added_val == 1 or updated_val == 1), f"Ожидалось added=1 или updated=1. Ответ: {data}"

    if full_check:
        schema = get_unit_create_or_update_response_schema()
        try:
            jsonschema.validate(instance=data, schema=schema)
            _log_check("соответствие ответа схеме RestResponseDtoOfRestUnit", True, True)
        except jsonschema.ValidationError as e:
            _log_check("схема ответа", True, str(e))
            pytest.fail(f"Ответ не соответствует схеме: {e}. Ответ: {data}")

    get_response = _get_unit_response(get_url, admin_auth, page_num=0, page_size=0, no_count=False, timeout=30)
    assert get_response.status_code == 200, get_response.text
    list_data = get_response.json()
    items = list_data.get("items") or []
    lookup_key = "integrationId" if "integrationId" in payload else "code"
    lookup_value = payload.get("integrationId") or payload.get("code")
    found = _find_unit_by(items, lookup_key, lookup_value)
    _log_check("созданная единица найдена в GET /Unit", True, found is not None)
    assert found is not None, (
        f"Созданная единица не найдена в списке GET /Unit по {lookup_key}={lookup_value!r}. "
        f"Всего в items: {len(items)}"
    )
    return response, found

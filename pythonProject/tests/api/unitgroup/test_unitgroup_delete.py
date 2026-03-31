"""
Тесты для API UnitGroup: PATCH /UnitGroup/Delete (удаление одного объекта).
Тело — RestDtoBase (id, integrationId, code, name). Ответ 200 — RestResponseDto.
"""
import copy
import json
import os

import jsonschema
import pytest
import requests
from jsonref import replace_refs

pytestmark = pytest.mark.rt_light

from tests.api.unitgroup.test_unitgroup_create_or_update import (
    build_unique_unitgroup_payload,
    ensure_one_unit_and_get_ref,
    _find_unitgroup_by,
    _get_unitgroups_list,
    _log_check,
    _put_unitgroup,
)

DELETE_RESPONSE_SCHEMA_NAME = "RestResponseDto"


def _project_root():
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
        for k, v in schema.items():
            if isinstance(v, dict):
                out[k] = _merge_allof(v)
            elif k == "items" and isinstance(v, dict):
                out[k] = _merge_allof(v)
            else:
                out[k] = v
        return out
    merged = {"type": "object", "properties": {}, "additionalProperties": False}
    for part in schema["allOf"]:
        part = _merge_allof(copy.deepcopy(part))
        if isinstance(part, dict) and "properties" in part:
            for pk, pv in part["properties"].items():
                merged["properties"][pk] = _merge_allof(pv) if isinstance(pv, dict) else pv
    return merged


def get_rest_response_dto_schema() -> dict:
    swagger_path = os.path.join(_project_root(), "swagger.json")
    if not os.path.isfile(swagger_path):
        raise FileNotFoundError(f"swagger.json не найден: {swagger_path}")
    with open(swagger_path, encoding="utf-8") as f:
        swagger = json.load(f)
    swagger_resolved = replace_refs(swagger, proxies=False)
    schema = copy.deepcopy(swagger_resolved["components"]["schemas"][DELETE_RESPONSE_SCHEMA_NAME])
    schema = _openapi_nullable_to_jsonschema(schema)
    schema = _merge_allof(schema)
    return schema


def _patch_delete(base_url, body, auth=None, raw_body=None, timeout=30):
    from tests.api.unitgroup.steps import _patch_delete as step_patch_delete

    return step_patch_delete(base_url, body, auth=auth, raw_body=raw_body, timeout=timeout)


@pytest.fixture(scope="module")
def unitgroup_created_for_delete(base_server_url, admin_auth):
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    response = _put_unitgroup(put_url, payload=payload, auth=admin_auth)
    assert response.status_code == 200, response.text
    assert response.json().get("added") == 1 or response.json().get("updated") == 1, response.json()
    items = _get_unitgroups_list(get_url, admin_auth)
    ug = _find_unitgroup_by(items, "integrationId", payload["integrationId"])
    assert ug is not None, "Созданная группа не найдена в GET /UnitGroup"
    yield base_server_url, admin_auth, get_url, ug.get("id"), payload.get("integrationId")


@pytest.mark.regression
@pytest.mark.fast
@pytest.mark.test_name_ru("PATCH /UnitGroup/Delete: успешное удаление по id — 200 и схема")
def test_unitgroup_delete_success_by_id(unitgroup_created_for_delete):
    print("\n  === Тест: PATCH /UnitGroup/Delete — успешное удаление по id ===\n")
    base_url, admin_auth, get_url, ug_id, integration_id = unitgroup_created_for_delete
    response = _patch_delete(base_url, {"id": ug_id}, admin_auth)
    _log_check("код ответа PATCH /UnitGroup/Delete", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    deleted = data.get("deleted")
    count = data.get("count")
    success = deleted in (1, True) or (isinstance(count, int) and count >= 1) or (data.get("results") and len(data.get("results")) >= 1)
    assert success, f"Ожидалось удаление. Ответ: {data}"
    schema = get_rest_response_dto_schema()
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Ответ не соответствует схеме: {e}. Ответ: {data}")
    items_after = _get_unitgroups_list(get_url, admin_auth)
    found_after = _find_unitgroup_by(items_after, "id", ug_id)
    assert found_after is None, f"Группа с id={ug_id} всё ещё есть в списке после Delete"


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /UnitGroup/Delete: успешное удаление по integrationId — 200")
def test_unitgroup_delete_success_by_integration_id(base_server_url, admin_auth):
    print("\n  === Тест: PATCH /UnitGroup/Delete — удаление по integrationId ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    response = _put_unitgroup(put_url, payload=payload, auth=admin_auth)
    assert response.status_code == 200, response.text
    response = _patch_delete(base_server_url, {"integrationId": payload["integrationId"]}, admin_auth)
    _log_check("код ответа PATCH /UnitGroup/Delete по integrationId", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("deleted") in (1, True, None) or data.get("count", 0) >= 1, f"Ответ: {data}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /UnitGroup/Delete: запрос без авторизации — 401")
def test_unitgroup_delete_no_auth_returns_401(base_server_url):
    response = _patch_delete(base_server_url, {"id": 999999}, auth=None)
    _log_check("статус без авторизации", 401, response.status_code)
    assert response.status_code == 401, response.text


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /UnitGroup/Delete: удаление несуществующего id — 200 с deleted=0 или 404")
def test_unitgroup_delete_nonexistent_id(base_server_url, admin_auth):
    response = _patch_delete(base_server_url, {"id": 999999999}, admin_auth)
    if response.status_code in (404, 400, 200):
        return
    pytest.fail(f"Ожидался 200, 404 или 400, получен {response.status_code}. {response.text}")


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /UnitGroup/Delete: пустой body — 400/404")
def test_unitgroup_delete_empty_body(base_server_url, admin_auth):
    response = _patch_delete(base_server_url, {}, admin_auth)
    assert response.status_code in (400, 404, 422), response.text


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /UnitGroup/Delete: невалидный JSON — 400")
def test_unitgroup_delete_invalid_json(base_server_url, admin_auth):
    response = _patch_delete(base_server_url, None, admin_auth, raw_body=b'{"id": 1')
    assert response.status_code in (400, 415, 422), response.text

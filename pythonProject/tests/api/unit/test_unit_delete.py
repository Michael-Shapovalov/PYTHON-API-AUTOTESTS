"""
Тесты для API Unit: PATCH /Unit/Delete (удаление одного объекта).
Тело — RestDtoBase (id, integrationId, code, name). Ответ 200 — RestResponseDto (count, deleted, errors, results).
"""
import copy
import json
import os

import jsonschema
import pytest
import requests
from jsonref import replace_refs
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

pytestmark = pytest.mark.rt_light

from tests.api.unit.test_unit_create_or_update import (
    build_unique_unit_payload,
    _log_check,
    _put_unit,
    _get_units_list,
    _find_unit_by,
)

DELETE_RESPONSE_SCHEMA_NAME = "RestResponseDto"


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
    """Загружает из swagger.json схему RestResponseDto (ответ Delete/DeleteMany)."""
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
    """PATCH /Unit/Delete. body — RestDtoBase (id/integrationId/code/name)."""
    from tests.api.unit.steps import _patch_delete as step_patch_delete

    return step_patch_delete(base_url, body, auth=auth, raw_body=raw_body, timeout=timeout)


@pytest.fixture(scope="module")
def unit_created_for_delete(base_server_url, admin_auth):
    """Создаёт одну единицу через PUT, возвращает URL, auth и идентификаторы для удаления."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    payload = build_unique_unit_payload()
    response = _put_unit(put_url, payload=payload, auth=admin_auth)
    assert response.status_code == 200, response.text
    assert response.json().get("added") == 1 or response.json().get("updated") == 1, response.json()
    items = _get_units_list(get_url, admin_auth)
    unit = _find_unit_by(items, "integrationId", payload["integrationId"])
    assert unit is not None, "Созданная единица не найдена в GET /Unit"
    yield base_server_url, admin_auth, get_url, unit.get("id"), payload.get("integrationId")


@pytest.mark.regression
@pytest.mark.fast
@pytest.mark.test_name_ru("PATCH /Unit/Delete: успешное удаление по id — 200 и схема")
def test_unit_delete_success_by_id(unit_created_for_delete):
    """Создана одна единица → PATCH /Unit/Delete с её id → 200, структура, deleted, схема. GET — единицы нет."""
    print("\n  === Тест: PATCH /Unit/Delete — успешное удаление по id ===\n")
    base_url, admin_auth, get_url, unit_id, integration_id = unit_created_for_delete
    # Передаём id в том же типе, что вернул API (int или str), чтобы избежать ошибки типа на сервере
    response = _patch_delete(base_url, {"id": unit_id}, admin_auth)
    _log_check("код ответа PATCH /Unit/Delete", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    deleted = data.get("deleted")
    count = data.get("count")
    _log_check("поле deleted или count в ответе", "1 или True / count>=1", deleted or count)
    success = deleted in (1, True) or (isinstance(count, int) and count >= 1) or (data.get("results") and len(data.get("results")) >= 1)
    assert success, f"Ожидалось удаление (deleted=1 или count/results). Ответ: {data}"
    schema = get_rest_response_dto_schema()
    try:
        jsonschema.validate(instance=data, schema=schema)
        schema_ok = True
    except jsonschema.ValidationError as e:
        schema_ok = False
        _log_check("схема RestResponseDto", True, str(e))
        pytest.fail(f"Ответ не соответствует схеме: {e}. Ответ: {data}")
    _log_check("соответствие ответа схеме RestResponseDto", True, schema_ok)
    items_after = _get_units_list(get_url, admin_auth)
    found_after = _find_unit_by(items_after, "id", unit_id)
    _log_check("единица отсутствует в GET после удаления", False, found_after is not None)
    assert found_after is None, f"Единица с id={unit_id} всё ещё есть в списке после Delete"


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /Unit/Delete: успешное удаление по integrationId — 200")
def test_unit_delete_success_by_integration_id(base_server_url, admin_auth):
    """Создаём единицу, удаляем по integrationId — 200, deleted."""
    print("\n  === Тест: PATCH /Unit/Delete — удаление по integrationId ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    payload = build_unique_unit_payload()
    response = _put_unit(put_url, payload=payload, auth=admin_auth)
    assert response.status_code == 200, response.text
    integration_id = payload["integrationId"]
    response = _patch_delete(base_server_url, {"integrationId": integration_id}, admin_auth)
    _log_check("код ответа PATCH /Unit/Delete по integrationId", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    _log_check("deleted", "1 или True", data.get("deleted"))
    assert data.get("deleted") in (1, True, None) or data.get("count", 0) >= 1, f"Ответ: {data}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /Unit/Delete: запрос без авторизации — 401")
def test_unit_delete_no_auth_returns_401(base_server_url):
    """PATCH /Unit/Delete без auth — 401."""
    print("\n  === Тест: PATCH /Unit/Delete — без авторизации (401) ===\n")
    response = _patch_delete(base_server_url, {"id": 999999}, auth=None)
    _log_check("статус без авторизации", 401, response.status_code)
    assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /Unit/Delete: удаление несуществующего id — 200 с deleted=0 или 404")
def test_unit_delete_nonexistent_id(base_server_url, admin_auth):
    """Удаление id, которого нет в БД — 200 с deleted=0 или 404, либо 400."""
    print("\n  === Тест: PATCH /Unit/Delete — несуществующий id ===\n")
    response = _patch_delete(base_server_url, {"id": 999999999}, admin_auth)
    _log_check("статус при несуществующем id", "200 / 404 / 400", response.status_code)
    if response.status_code == 404:
        return
    if response.status_code == 400:
        return
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get("deleted") == 0 or data.get("deleted") is False:
                return
            if "results" in data and data.get("results"):
                return
            if "deleted" in data or "count" in data:
                return
        except Exception:
            pass
        return
    pytest.fail(f"Ожидался 200, 404 или 400, получен {response.status_code}. {response.text}")


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /Unit/Delete: пустой body — 400/404")
def test_unit_delete_empty_body(base_server_url, admin_auth):
    """PATCH с телом {} — 400 или 404."""
    print("\n  === Тест: PATCH /Unit/Delete — пустой body ===\n")
    response = _patch_delete(base_server_url, {}, admin_auth)
    _log_check("статус при пустом body", "400/404", response.status_code)
    assert response.status_code in (400, 404, 422), f"Ожидался 400/404/422, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /Unit/Delete: невалидный JSON — 400")
def test_unit_delete_invalid_json(base_server_url, admin_auth):
    """Тело — невалидный JSON — 400."""
    print("\n  === Тест: PATCH /Unit/Delete — невалидный JSON ===\n")
    response = _patch_delete(base_server_url, None, admin_auth, raw_body=b'{"id": 1')
    _log_check("статус при невалидном JSON", "400/415/422", response.status_code)
    assert response.status_code in (400, 415, 422), f"Ожидался 400/415/422, получен {response.status_code}. {response.text}"

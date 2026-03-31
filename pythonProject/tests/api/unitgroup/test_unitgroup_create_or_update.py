"""
Тесты для API UnitGroup: PUT /UnitGroup/CreateOrUpdate.
Создание/обновление группы единиц измерения (UnitGroup). Для baseUnit используется существующая Unit.
"""
import copy
import json
import os
import uuid

import jsonschema
import pytest
import requests
from jsonref import replace_refs
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

pytestmark = pytest.mark.rt_light

from tests.api.unit.test_unit_create_or_update import (
    build_unique_unit_payload,
    _find_unit_by,
    _get_units_list,
    _put_unit,
)

SWAGGER_RESPONSE_SCHEMA_NAME = "RestResponseDtoOfRestUnitGroup"


def _log_check(what: str, expected, actual):
    """Логирует проверку в формате: ожидаемый результат - фактический."""
    print(f"  Проверка: {what}: ожидаемый {expected} - фактический {actual}")


def _project_root() -> str:
    """Корень проекта (каталог с swagger.json)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _openapi_nullable_to_jsonschema(schema: dict) -> dict:
    """Преобразует OpenAPI nullable в вид, понятный jsonschema."""
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
    """Сливает allOf в одну схему рекурсивно. Упрощает oneOf из одного элемента."""
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


def get_unitgroup_create_or_update_response_schema() -> dict:
    """Загружает из swagger.json схему ответа RestResponseDtoOfRestUnitGroup."""
    swagger_path = os.path.join(_project_root(), "swagger.json")
    if not os.path.isfile(swagger_path):
        raise FileNotFoundError(f"swagger.json не найден: {swagger_path}")
    with open(swagger_path, encoding="utf-8") as f:
        swagger = json.load(f)
    swagger_resolved = replace_refs(swagger, proxies=False)
    schema = copy.deepcopy(swagger_resolved["components"]["schemas"][SWAGGER_RESPONSE_SCHEMA_NAME])
    schema = _openapi_nullable_to_jsonschema(schema)
    schema = _merge_allof(schema)
    return schema


def _unique_suffix() -> str:
    """Короткий уникальный суффикс для полей."""
    return uuid.uuid4().hex[:12]


def ensure_one_unit_and_get_ref(base_server_url, admin_auth):
    """
    Создаёт одну Unit через PUT /Unit/CreateOrUpdate и возвращает ссылку для baseUnit.
    Возвращает dict: {"id": <unit_id>} для подстановки в payload UnitGroup.
    """
    base = base_server_url.rstrip("/")
    put_unit_url = f"{base}/Unit/CreateOrUpdate"
    get_unit_url = f"{base}/Unit"
    payload = build_unique_unit_payload()
    response = _put_unit(put_unit_url, payload=payload, auth=admin_auth)
    assert response.status_code == 200, response.text
    assert response.json().get("added") == 1 or response.json().get("updated") == 1, response.json()
    items = _get_units_list(get_unit_url, admin_auth)
    unit = _find_unit_by(items, "integrationId", payload["integrationId"])
    assert unit is not None, "Созданная единица не найдена в GET /Unit"
    unit_id = unit.get("id")
    assert unit_id is not None, unit
    return {"id": unit_id}


def build_unique_unitgroup_payload(base_unit_ref: dict):
    """
    Готовит уникальные данные для создания UnitGroup.
    base_unit_ref — ссылка на Unit, например {"id": 123} или {"integrationId": "..."}.
    По документации: Code, Name, IntegrationId уникальны; baseUnit обязателен.
    """
    suffix = _unique_suffix()
    unique_code = f"UG{suffix}"[:30]
    payload = {
        "integrationId": f"unitgroup-test-{suffix}"[:100],
        "code": unique_code,
        "name": f"Группа ЕИ тест {suffix}"[:250],
        "baseUnit": base_unit_ref,
    }
    return payload


def build_minimal_unitgroup_payload(base_unit_ref: dict):
    """Минимальный payload: code, name, baseUnit (уникальные code+name)."""
    suffix = _unique_suffix()
    return {
        "code": f"UG{suffix}"[:30],
        "name": f"Группа ЕИ мин {suffix}"[:250],
        "baseUnit": base_unit_ref,
    }


def _put_unitgroup(put_url: str, payload=None, auth=None, raw_body=None, timeout=30):
    """Выполняет PUT /UnitGroup/CreateOrUpdate. Возвращает response."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if raw_body is not None:
        return requests.put(put_url, data=raw_body, auth=auth, headers=headers, timeout=timeout)
    return requests.put(put_url, json=payload, auth=auth, headers=headers, timeout=timeout)


def _get_unitgroups_list(get_url, admin_auth, page_size=1000):
    """GET /UnitGroup, возвращает список items."""
    try:
        r = requests.get(
            get_url,
            params={"pageNum": 0, "pageSize": page_size},
            auth=admin_auth,
            headers={"Accept": "application/json"},
            timeout=30,
        )
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"GET /UnitGroup: нет связи с сервером: {e}")
    assert r.status_code == 200, f"GET /UnitGroup: ожидался 200, получен {r.status_code}. {r.text}"
    data = r.json()
    return data.get("items") or []


def _find_unitgroup_by(items, lookup_key: str, lookup_value):
    """Ищет в списке items группу с lookup_key == lookup_value."""
    for ug in items:
        if ug.get(lookup_key) == lookup_value:
            return ug
    return None


def _assert_error_response(response, expected_status_range=(400, 499)):
    """Проверяет, что ответ — ошибка (4xx или ошибка в results)."""
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
    """PUT UnitGroup, проверки ответа, GET, поиск группы в items."""
    try:
        response = requests.put(
            put_url,
            json=payload,
            auth=admin_auth,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"Нет связи с сервером: {e}. URL: {put_url}.")
    if response.status_code != 200:
        err_body = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        _log_check("код ответа PUT /UnitGroup/CreateOrUpdate", 200, response.status_code)
        pytest.fail(f"Ожидаемый код 200 - фактический {response.status_code}. Response: {err_body}")
    _log_check("код ответа PUT /UnitGroup/CreateOrUpdate", 200, response.status_code)
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
        schema = get_unitgroup_create_or_update_response_schema()
        try:
            jsonschema.validate(instance=data, schema=schema)
            _log_check("соответствие ответа схеме RestResponseDtoOfRestUnitGroup", True, True)
        except jsonschema.ValidationError as e:
            _log_check("схема ответа", True, str(e))
            pytest.fail(f"Ответ не соответствует схеме: {e}. Ответ: {data}")
    get_response = requests.get(get_url, params={"pageNum": 0, "pageSize": 0}, auth=admin_auth, headers={"Accept": "application/json"}, timeout=30)
    assert get_response.status_code == 200, get_response.text
    list_data = get_response.json()
    items = list_data.get("items") or []
    lookup_key = "integrationId" if "integrationId" in payload else "code"
    lookup_value = payload.get("integrationId") or payload.get("code")
    found = _find_unitgroup_by(items, lookup_key, lookup_value)
    _log_check(f"созданная группа в списке GET /UnitGroup (по {lookup_key})", True, found is not None)
    assert found is not None, f"Группа ({lookup_key}={lookup_value!r}) не найдена в items. Всего: {len(items)}"


# --- Тесты ---

from tests.api.unitgroup import steps as unitgroup_steps

_log_check = unitgroup_steps._log_check
_project_root = unitgroup_steps._project_root
_openapi_nullable_to_jsonschema = unitgroup_steps._openapi_nullable_to_jsonschema
_merge_allof = unitgroup_steps._merge_allof
get_unitgroup_create_or_update_response_schema = unitgroup_steps.get_unitgroup_create_or_update_response_schema
_unique_suffix = unitgroup_steps._unique_suffix
ensure_one_unit_and_get_ref = unitgroup_steps.ensure_one_unit_and_get_ref
build_unique_unitgroup_payload = unitgroup_steps.build_unique_unitgroup_payload
build_minimal_unitgroup_payload = unitgroup_steps.build_minimal_unitgroup_payload
_put_unitgroup = unitgroup_steps._put_unitgroup
_get_unitgroups_list = unitgroup_steps._get_unitgroups_list
_find_unitgroup_by = unitgroup_steps._find_unitgroup_by
_assert_error_response = unitgroup_steps._assert_error_response
_run_put_get_and_assert_checks = unitgroup_steps._run_put_get_and_assert_checks


@pytest.mark.regression
@pytest.mark.fast
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Создание группы с полным набором полей (PUT + GET + сравнение)")
def test_unitgroup_create_or_update_full(base_server_url, admin_auth):
    """Создание UnitGroup с code, name, integrationId, baseUnit. 200, added=1 или updated=1, группа в GET."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — создание с полным набором полей ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url)


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Создание с минимальным набором (code, name, baseUnit)")
def test_unitgroup_create_or_update_minimal(base_server_url, admin_auth):
    """Минимальный payload: code, name, baseUnit. 200, создание, группа в GET."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — минимальный набор полей ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_minimal_unitgroup_payload(base_unit_ref)
    _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url, full_check=False)


@pytest.mark.negative
@pytest.mark.validation
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Обязательность: отсутствие name — ошибка")
def test_unitgroup_missing_name_rejected(base_server_url, admin_auth):
    """PUT без name (есть code, baseUnit) — 400 или ошибка в results."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — отсутствие name ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_minimal_unitgroup_payload(base_unit_ref)
    payload.pop("name", None)
    response = _put_unitgroup(put_url, payload=payload, auth=admin_auth)
    _assert_error_response(response)


@pytest.mark.negative
@pytest.mark.validation
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Обязательность: отсутствие code — ошибка")
def test_unitgroup_missing_code_rejected(base_server_url, admin_auth):
    """PUT без code (есть name, baseUnit) — 400 или ошибка в results."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — отсутствие code ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_minimal_unitgroup_payload(base_unit_ref)
    payload.pop("code", None)
    response = _put_unitgroup(put_url, payload=payload, auth=admin_auth)
    _assert_error_response(response)


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Уникальность: повтор по integrationId — обновление (updated=1)")
def test_unitgroup_duplicate_by_integration_id_updates(base_server_url, admin_auth):
    """Создать группу по integrationId, затем тот же integrationId с другими полями → updated=1."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — повтор по integrationId → обновление ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload1 = build_unique_unitgroup_payload(base_unit_ref)
    r1 = _put_unitgroup(put_url, payload1, auth=admin_auth)
    assert r1.status_code == 200 and r1.json().get("added") == 1, r1.text
    payload2 = {**payload1, "name": f"Обновлённая группа {_unique_suffix()}"[:250]}
    r2 = _put_unitgroup(put_url, payload2, auth=admin_auth)
    assert r2.status_code == 200 and r2.json().get("updated") == 1, r2.text
    items = _get_unitgroups_list(get_url, admin_auth)
    found = _find_unitgroup_by(items, "integrationId", payload1["integrationId"])
    assert found is not None and found.get("name") == payload2["name"], found


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Уникальность: повтор по code+name — обновление (updated=1)")
def test_unitgroup_duplicate_by_code_name_updates(base_server_url, admin_auth):
    """Создать по code+name, затем тот же code+name с другими полями → updated=1."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — повтор по code+name → обновление ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    suffix = _unique_suffix()
    code, name = f"UG{suffix}"[:30], f"Группа code+name {suffix}"[:250]
    payload1 = {"code": code, "name": name, "baseUnit": base_unit_ref}
    r1 = _put_unitgroup(put_url, payload1, auth=admin_auth)
    assert r1.status_code == 200 and r1.json().get("added") == 1, r1.text
    payload2 = {"code": code, "name": name, "baseUnit": base_unit_ref, "integrationId": f"ug-cn-{suffix}"[:100]}
    r2 = _put_unitgroup(put_url, payload2, auth=admin_auth)
    assert r2.status_code == 200 and r2.json().get("updated") == 1, r2.text
    items = _get_unitgroups_list(get_url, admin_auth)
    found = _find_unitgroup_by(items, "code", code)
    assert found is not None, items


@pytest.mark.regression
@pytest.mark.validation
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Границы: code длина 30, name длина 250 — успех")
def test_unitgroup_boundary_max_length_success(base_server_url, admin_auth):
    """Поля ровно maxLength: code 30, name 250 → 200, создание."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — границы длин полей ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    suffix = _unique_suffix()
    payload = {
        "integrationId": f"ug-bnd-{suffix}"[:100],
        "code": "A" * 28 + suffix[:2],
        "name": "Б" * 248 + suffix[:2],
        "baseUnit": base_unit_ref,
    }
    assert len(payload["code"]) <= 30 and len(payload["name"]) <= 250
    _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url, full_check=False)


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Правило: создание по IntegrationId (без id)")
def test_unitgroup_create_by_integration_id(base_server_url, admin_auth):
    """Создание без id, с уникальным integrationId → added=1."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — создание по IntegrationId ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url, full_check=False)


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Правило: создание по Code+Name (без id и integrationId)")
def test_unitgroup_create_by_code_name(base_server_url, admin_auth):
    """Создание без id и integrationId, с уникальной парой code+name → added=1."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — создание по Code+Name ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_minimal_unitgroup_payload(base_unit_ref)
    _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url, full_check=False)


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Правило: обновление по Id")
def test_unitgroup_update_by_id(base_server_url, admin_auth):
    """Создать группу, получить id из GET, PUT с id и новыми полями → updated=1."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — обновление по Id ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload1 = build_unique_unitgroup_payload(base_unit_ref)
    r1 = _put_unitgroup(put_url, payload1, auth=admin_auth)
    assert r1.status_code == 200 and r1.json().get("added") == 1, r1.text
    items = _get_unitgroups_list(get_url, admin_auth)
    found = _find_unitgroup_by(items, "integrationId", payload1["integrationId"])
    assert found is not None, items
    ug_id = found.get("id")
    assert ug_id is not None, found
    new_name = f"Обновлено по Id {_unique_suffix()}"[:250]
    payload2 = {"id": ug_id, "integrationId": payload1["integrationId"], "code": payload1["code"], "name": new_name, "baseUnit": base_unit_ref}
    r2 = _put_unitgroup(put_url, payload2, auth=admin_auth)
    assert r2.status_code == 200 and r2.json().get("updated") == 1, r2.text
    items2 = _get_unitgroups_list(get_url, admin_auth)
    found2 = _find_unitgroup_by(items2, "id", ug_id)
    assert found2 is not None and found2.get("name") == new_name, found2


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Идемпотентность: один и тот же запрос дважды — added=1, затем updated=1")
def test_unitgroup_same_request_twice_create_then_update(base_server_url, admin_auth):
    """Один и тот же payload дважды: первый added=1, второй updated=1."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — идемпотентность ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    r1 = _put_unitgroup(put_url, payload, auth=admin_auth)
    assert r1.status_code == 200 and r1.json().get("added") == 1, r1.text
    r2 = _put_unitgroup(put_url, payload, auth=admin_auth)
    assert r2.status_code == 200 and r2.json().get("updated") == 1, r2.text
    items = _get_unitgroups_list(get_url, admin_auth)
    found = _find_unitgroup_by(items, "integrationId", payload["integrationId"])
    assert found is not None and found.get("name") == payload["name"], found


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Запрос без тела (пустой body) — 400")
def test_unitgroup_empty_body_rejected(base_server_url, admin_auth):
    """PUT с телом {} — 400 или ошибка в results."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — пустой body ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    response = _put_unitgroup(put_url, payload={}, auth=admin_auth)
    _assert_error_response(response)


@pytest.mark.negative
@pytest.mark.fast
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Запрос без авторизации — 401")
def test_unitgroup_no_auth_rejected(base_server_url, admin_auth):
    """PUT без Basic Auth → 401. Unit создаётся с auth, затем PUT UnitGroup без auth."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — без авторизации ===\n")
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    response = _put_unitgroup(put_url, payload=payload, auth=None)
    _log_check("статус без авторизации", 401, response.status_code)
    assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdate: Невалидный JSON в теле — 400")
def test_unitgroup_invalid_json_rejected(base_server_url, admin_auth):
    """PUT с телом не-JSON — 400 или 415."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdate — невалидный JSON ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    response = _put_unitgroup(put_url, raw_body=b'{"code": "x", "name": ', auth=admin_auth)
    assert response.status_code in (400, 415, 422), f"Ожидался 400/415/422, получен {response.status_code}. {response.text}"

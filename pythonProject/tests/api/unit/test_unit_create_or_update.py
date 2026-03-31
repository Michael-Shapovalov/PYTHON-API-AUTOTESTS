"""
Тесты для API Unit: PUT /Unit/CreateOrUpdate.
Создание единицы измерения (Unit) с уникальными данными.
"""
import copy
import json
import os
import random
import uuid
from typing import Optional

import jsonschema
import pytest
import requests
from jsonref import replace_refs
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

pytestmark = pytest.mark.rt_light

# Схема ответа PUT /Unit/CreateOrUpdate (200) из swagger: RestResponseDtoOfRestUnit
SWAGGER_RESPONSE_SCHEMA_NAME = "RestResponseDtoOfRestUnit"


def _log_check(what: str, expected, actual):
    """Логирует проверку в формате: ожидаемый результат - фактический (для вывода в терминале)."""
    print(f"  Проверка: {what}: ожидаемый {expected} - фактический {actual}")


def _project_root() -> str:
    """Корень проекта (каталог с swagger.json)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _openapi_nullable_to_jsonschema(schema: dict) -> dict:
    """Преобразует OpenAPI nullable в вид, понятный jsonschema (type: [..., "null"])."""
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
    """Сливает allOf в одну схему (объединение properties) рекурсивно. Упрощает oneOf из одного элемента."""
    if not isinstance(schema, dict):
        return schema
    # oneOf: [single] -> single (чтобы entity с вложенным allOf валидировался)
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


def get_unit_create_or_update_response_schema() -> dict:
    """Загружает из swagger.json схему ответа RestResponseDtoOfRestUnit (с разрешением $ref)."""
    swagger_path = os.path.join(_project_root(), "swagger.json")
    if not os.path.isfile(swagger_path):
        raise FileNotFoundError(f"swagger.json не найден: {swagger_path}")
    with open(swagger_path, encoding="utf-8") as f:
        swagger = json.load(f)
    # Разрешаем все $ref в документе, затем берём нужную схему
    swagger_resolved = replace_refs(swagger, proxies=False)
    schema = copy.deepcopy(swagger_resolved["components"]["schemas"][SWAGGER_RESPONSE_SCHEMA_NAME])
    schema = _openapi_nullable_to_jsonschema(schema)
    schema = _merge_allof(schema)
    return schema


def _unique_suffix() -> str:
    """Короткий уникальный суффикс для полей (без дефисов, для code)."""
    return uuid.uuid4().hex[:12]


def build_unique_unit_payload() -> dict:
    """
    Готовит уникальные данные для создания Unit (единицы измерения).
    Соответствует схеме БД dbo.Unit и уникальным индексам (Acronym, Code, IntegrationId).
    Опциональные поля с значением None не включаются в JSON (как часто делает Swagger).
    """
    suffix = _unique_suffix()
    unique_part = f"UT{suffix}"
    payload = {
        "integrationId": f"unit-test-{suffix}"[:100],
        "code": unique_part[:30],
        "name": f"Единица измерения тест {suffix}"[:250],
        "acronym": unique_part[:30],
        "description": (f"Тестовая единица измерения, создана автотестом. {suffix}")[:4000],
        "internationalAcronym": unique_part[:3],
        "isDivisible": True,
        "precision": 2,
    }
    # Не добавляем okei, если не задан — сервер может не принимать явный null
    return payload


# Наборы символов для валидации integrationId (без пробелов — pattern \S+ в swagger)
_RU_LETTERS = "абвгдежзийклмнопрстуфхцчшщъыьэюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
_EN_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_SPECIAL = "!@#$%^&*()_+-=[]{}|;:',.<>?"
_DIGITS = "0123456789"


def _random_integration_id_validation_value() -> str:
    """
    Случайная строка для валидации integrationId: по 2 символа каждого типа
    (русские, английские, спецсимволы, цифры, подчёркивания). Каждый запуск — уникальное значение.
    """
    return (
        "".join(random.choices(_RU_LETTERS, k=2))
        + "".join(random.choices(_EN_LETTERS, k=2))
        + "".join(random.choices(_SPECIAL, k=2))
        + "".join(random.choices(_DIGITS, k=2))
        + "__"
    )


def build_unit_payload_with_integration_id_validation() -> dict:
    """
    Payload для теста валидации поля integrationId.
    integrationId = случайная строка из 2 русских, 2 английских, 2 спецсимволов, 2 цифр, 2 подчёркиваний (уникальна каждый раз).
    Остальные поля — уникальные (чтобы code/acronym не конфликтовали).
    """
    suffix = _unique_suffix()
    unique_part = f"UT{suffix}"
    return {
        "integrationId": _random_integration_id_validation_value(),
        "code": unique_part[:30],
        "name": f"Единица измерения тест (валидация integrationId) {suffix}"[:250],
        "acronym": unique_part[:30],
        "description": (f"Тест валидации поля integrationId. {suffix}")[:4000],
        "internationalAcronym": unique_part[:3],
        "isDivisible": True,
        "precision": 2,
    }


def build_minimal_unit_payload() -> dict:
    """
    Минимальный payload для создания Unit: только обязательные поля name и acronym (по БД).
    Уникальные значения, чтобы не конфликтовать с существующими записями.
    """
    suffix = _unique_suffix()
    unique_part = f"UT{suffix}"
    return {
        "name": f"ЕИ мин {suffix}"[:250],
        "acronym": unique_part[:30],
    }


def build_payload_without_field(exclude_field: str) -> dict:
    """Минимальный payload без указанного поля (для проверки обязательности)."""
    payload = build_minimal_unit_payload()
    payload.pop(exclude_field, None)
    return payload


def build_payload_with_null_field(field_name: str) -> dict:
    """Минимальный payload с явным null для указанного поля."""
    payload = build_minimal_unit_payload()
    payload[field_name] = None
    return payload


def build_payload_with_wrong_type(field_name: str, wrong_value) -> dict:
    """Уникальный валидный payload с подменённым значением типа для одного поля."""
    payload = build_unique_unit_payload()
    payload[field_name] = wrong_value
    return payload


def _put_unit(put_url: str, payload=None, auth=None, raw_body=None, timeout=30):
    """
    Выполняет PUT /Unit/CreateOrUpdate. Возвращает response.
    Если raw_body задан — отправляется как data=raw_body с Content-Type application/json.
    """
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if raw_body is not None:
        return requests.put(put_url, data=raw_body, auth=auth, headers=headers, timeout=timeout)
    return requests.put(put_url, json=payload, auth=auth, headers=headers, timeout=timeout)


def _assert_error_response(response, expected_status_range=(400, 499)):
    """Проверяет, что ответ — ошибка (статус 4xx или ошибка в results, не added=1)."""
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
                err = results[0].get("error") or results[0].get("message") or str(results[0])
                if err:
                    return
        except Exception:
            pass
        pytest.fail(f"Ожидалась ошибка (4xx или ошибка в results), но получен 200. Тело: {response.text}")
    pytest.fail(f"Ожидался статус 4xx или 200 с ошибкой в results. Получен: {response.status_code}. Тело: {response.text}")


def _get_units_list(get_url, admin_auth, page_size=1000):
    """GET /Unit, возвращает список items."""
    try:
        r = requests.get(
            get_url,
            params={"pageNum": 0, "pageSize": page_size},
            auth=admin_auth,
            headers={"Accept": "application/json"},
            timeout=30,
        )
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"GET /Unit: нет связи с сервером: {e}")
    assert r.status_code == 200, f"GET /Unit: ожидался 200, получен {r.status_code}. {r.text}"
    data = r.json()
    return (data.get("items") or [])


def _find_unit_by(items, lookup_key: str, lookup_value) -> Optional[dict]:
    """Ищет в списке items единицу с lookup_key == lookup_value."""
    for unit in items:
        if unit.get(lookup_key) == lookup_value:
            return unit
    return None


def _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url, *, full_check=True):
    """
    Стандартная логика тестов: PUT, проверки ответа (200, results, added/updated), GET, поиск единицы.
    При full_check=True дополнительно: валидация ответа по схеме и сравнение полей из payload с GET.
    Поиск: по integrationId, если он в payload, иначе по acronym.
    """
    try:
        response = requests.put(
            put_url,
            json=payload,
            auth=admin_auth,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(
            f"Нет связи с сервером: {e}. URL: {put_url}. "
            "Проверьте BASE_SERVER_URL в .env и доступность сервера с этой машины."
        )

    if response.status_code != 200:
        try:
            err_body = response.json()
        except Exception:
            err_body = response.text
        _log_check("код ответа сервера PUT /Unit/CreateOrUpdate", 200, response.status_code)
        pytest.fail(
            f"Ожидаемый код ответа 200 - фактический {response.status_code}.\n"
            f"URL: {put_url}\nRequest body: {payload}\nResponse body: {err_body}"
        )
    _log_check("код ответа сервера PUT /Unit/CreateOrUpdate", 200, response.status_code)
    data = response.json()

    has_results = "results" in data
    _log_check("наличие поля 'results' в ответе CreateOrUpdate", True, has_results)
    assert has_results, (
        f"Ожидаемый результат проверки (наличие 'results') True - фактический False. Ключи ответа: {list(data.keys())}"
    )

    added_val = data.get("added")
    updated_val = data.get("updated")
    _log_check("значение поля 'added' в ответе CreateOrUpdate", 1, added_val)
    _log_check("значение поля 'updated' в ответе CreateOrUpdate", "0 или 1", updated_val)
    # CreateOrUpdate либо создаёт (added=1), либо обновляет существующую запись (updated=1)
    assert (added_val == 1 or updated_val == 1), (
        f"Ожидаемый результат проверки (added=1 или updated=1) - фактический added={added_val!r}, updated={updated_val!r}. Ответ: {data}"
    )

    if full_check:
        response_schema = get_unit_create_or_update_response_schema()
        schema_valid = True
        schema_error = None
        try:
            jsonschema.validate(instance=data, schema=response_schema)
        except jsonschema.ValidationError as e:
            schema_valid = False
            schema_error = f"{e!s}; путь: {list(e.absolute_path) if e.absolute_path else []}"
        _log_check("соответствие ответа PUT схеме RestResponseDtoOfRestUnit", True, schema_valid if schema_valid else schema_error)
        if not schema_valid:
            pytest.fail(
                f"Ожидаемый результат проверки (схема ответа) True - фактический (ошибка): {schema_error}. Ответ: {data}"
            )

    try:
        get_response = requests.get(
            get_url,
            params={"pageNum": 0, "pageSize": 0},
            auth=admin_auth,
            headers={"Accept": "application/json"},
            timeout=30,
        )
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"GET /Unit: нет связи с сервером: {e}")

    _log_check("код ответа сервера GET /Unit", 200, get_response.status_code)
    assert get_response.status_code == 200, (
        f"Ожидаемый код ответа GET /Unit 200 - фактический {get_response.status_code}. Тело: {get_response.text}"
    )
    list_data = get_response.json()
    has_items = "items" in list_data
    _log_check("наличие поля 'items' в ответе GET /Unit", True, has_items)
    assert has_items, (
        f"Ожидаемый результат проверки (наличие 'items') True - фактический False. Ключи: {list(list_data.keys())}"
    )
    items = list_data["items"] or []

    # Поиск созданной единицы: по integrationId если передан, иначе по acronym (уникальный индекс)
    if "integrationId" in payload:
        lookup_key, lookup_value = "integrationId", payload["integrationId"]
    else:
        lookup_key, lookup_value = "acronym", payload["acronym"]
    found_unit = None
    for unit in items:
        if unit.get(lookup_key) == lookup_value:
            found_unit = unit
            break

    _log_check(f"наличие созданной единицы в списке GET /Unit (по {lookup_key})", True, found_unit is not None)
    assert found_unit is not None, (
        f"Ожидаемый результат проверки (единица в списке) True - фактический False. "
        f"{lookup_key}={lookup_value!r}, всего в списке: {len(items)}."
    )

    if full_check:
        # Сравниваем только те поля, которые были в запросе (для минимального payload — только name, acronym)
        fields_sent = ["integrationId", "code", "name", "acronym", "description", "internationalAcronym", "isDivisible", "precision"]
        for field in fields_sent:
            if field not in payload:
                continue
            expected = payload.get(field)
            actual = found_unit.get(field)
            _log_check(f"поле '{field}' у единицы в списке GET /Unit", expected, actual)
            assert actual == expected, (
                f"Ожидаемый результат проверки (поле {field!r}) {expected!r} - фактический {actual!r}. Единица: {found_unit}"
            )

from tests.api.unit import steps as unit_steps

_log_check = unit_steps._log_check
_project_root = unit_steps._project_root
_openapi_nullable_to_jsonschema = unit_steps._openapi_nullable_to_jsonschema
_merge_allof = unit_steps._merge_allof
get_unit_create_or_update_response_schema = unit_steps.get_unit_create_or_update_response_schema
_unique_suffix = unit_steps._unique_suffix
build_unique_unit_payload = unit_steps.build_unique_unit_payload
_random_integration_id_validation_value = unit_steps._random_integration_id_validation_value
_put_unit = unit_steps._put_unit
_assert_error_response = unit_steps._assert_error_response
_get_units_list = unit_steps._get_units_list
_find_unit_by = unit_steps._find_unit_by
_run_put_get_and_assert_checks = unit_steps._run_put_get_and_assert_checks


@pytest.mark.regression
@pytest.mark.fast
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Создание единицы измерения с полным набором полей (PUT + GET + сравнение)")
def test_unit_create_or_update_creates_entity(base_server_url, admin_auth):
    """
    PUT /Unit/CreateOrUpdate: подготовка уникальных данных и создание сущности (единицы измерения).
    Ожидается успешный ответ 200 и результат с созданным объектом.
    """
    print("\n  === Тест: Создание единицы измерения с полным набором полей (PUT + GET + сравнение) ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    payload = build_unique_unit_payload()
    _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url)


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Создание единицы с минимальным набором полей (только name и acronym)")
def test_unit_create_or_update_minimal_required_fields(base_server_url, admin_auth):
    """
    PUT /Unit/CreateOrUpdate: создание единицы измерения с минимальным набором полей.
    Только обязательные по БД: name и acronym. Те же проверки и логирование, что в остальных тестах.
    """
    print("\n  === Тест: Создание единицы с минимальным набором полей (только name и acronym) ===\n")
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    payload = build_minimal_unit_payload()
    _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url, full_check=False)


# --- Обязательность (негатив) ---


@pytest.mark.negative
@pytest.mark.validation
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Обязательность: отсутствие name — ошибка")
def test_unit_create_or_update_missing_name_rejected(base_server_url, admin_auth):
    """PUT без поля name: ожидается 400 или ошибка в results."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    payload = build_payload_without_field("name")
    try:
        response = _put_unit(put_url, payload=payload, auth=admin_auth)
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"Нет связи с сервером: {e}")
    _assert_error_response(response)


@pytest.mark.negative
@pytest.mark.validation
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Обязательность: отсутствие acronym — ошибка")
def test_unit_create_or_update_missing_acronym_rejected(base_server_url, admin_auth):
    """PUT без поля acronym: ожидается 400 или ошибка в results."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    payload = build_payload_without_field("acronym")
    try:
        response = _put_unit(put_url, payload=payload, auth=admin_auth)
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"Нет связи с сервером: {e}")
    _assert_error_response(response)


# --- Уникальность (повтор по IntegrationId / Code+Name → обновление) ---


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Уникальность: повтор по integrationId — обновление (updated=1)")
def test_unit_duplicate_by_integration_id_updates(base_server_url, admin_auth):
    """Создать единицу по integrationId, затем тот же integrationId с другими полями → updated=1."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    payload1 = build_unique_unit_payload()
    response1 = _put_unit(put_url, payload=payload1, auth=admin_auth)
    assert response1.status_code == 200, response1.text
    data1 = response1.json()
    assert data1.get("added") == 1, data1
    payload2 = {**payload1, "name": f"Обновлённое имя {_unique_suffix()}"[:250], "description": "Обновлено"}
    response2 = _put_unit(put_url, payload=payload2, auth=admin_auth)
    assert response2.status_code == 200, response2.text
    data2 = response2.json()
    assert data2.get("updated") == 1, data2
    items = _get_units_list(get_url, admin_auth)
    found = _find_unit_by(items, "integrationId", payload1["integrationId"])
    assert found is not None and found.get("name") == payload2["name"], found


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Уникальность: повтор по code+name — обновление (updated=1)")
def test_unit_duplicate_by_code_name_updates(base_server_url, admin_auth):
    """Создать единицу по code+name (без integrationId), затем тот же code+name с другими полями → updated=1."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    suffix = _unique_suffix()
    code, name = f"UT{suffix}"[:30], f"ЕИ code+name {suffix}"[:250]
    payload1 = {"code": code, "name": name, "acronym": f"UT{suffix}"[:30]}
    response1 = _put_unit(put_url, payload=payload1, auth=admin_auth)
    assert response1.status_code == 200, response1.text
    assert response1.json().get("added") == 1
    payload2 = {**payload1, "description": "Обновлено по code+name", "acronym": f"UT2{suffix}"[:30]}
    response2 = _put_unit(put_url, payload=payload2, auth=admin_auth)
    assert response2.status_code == 200, response2.text
    assert response2.json().get("updated") == 1
    items = _get_units_list(get_url, admin_auth)
    found = _find_unit_by(items, "code", code)
    assert found is not None and found.get("name") == name and found.get("description") == "Обновлено по code+name"


# --- Тип (негатив) ---


@pytest.mark.negative
@pytest.mark.validation
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Тип: name не строка — 400")
def test_unit_wrong_type_name_rejected(base_server_url, admin_auth):
    """PUT с name=число/массив: ожидается 400 или ошибка в results."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    payload = build_payload_with_wrong_type("name", 12345)
    try:
        response = _put_unit(put_url, payload=payload, auth=admin_auth)
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"Нет связи с сервером: {e}")
    _assert_error_response(response)


# --- Граничные значения ---


@pytest.mark.regression
@pytest.mark.validation
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Границы: code/acronym длина 30, name длина 250 — успех")
def test_unit_boundary_max_length_success(base_server_url, admin_auth):
    """Поля ровно maxLength: code/acronym 30 символов, name 250 → 200, создание."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    suffix = _unique_suffix()
    payload = {
        "integrationId": f"unit-bnd-{suffix}"[:100],
        "code": "A" * 28 + suffix[:2],
        "name": "Б" * 248 + suffix[:2],
        "acronym": "X" * 28 + suffix[:2],
        "description": "Граница",
    }
    assert len(payload["code"]) <= 30 and len(payload["name"]) <= 250 and len(payload["acronym"]) <= 30
    _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url, full_check=False)


# --- Универсальное правило: создание и обновление по Id / IntegrationId / Code+Name ---


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Правило: создание по IntegrationId (без id)")
def test_unit_create_by_integration_id(base_server_url, admin_auth):
    """Создание без id, с уникальным integrationId → added=1."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    payload = build_unique_unit_payload()
    assert "id" not in payload or payload.get("id") is None
    _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url, full_check=False)


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Правило: создание по Code+Name (без id и integrationId)")
def test_unit_create_by_code_name(base_server_url, admin_auth):
    """Создание без id и integrationId, с уникальной парой code+name → added=1."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    suffix = _unique_suffix()
    payload = {
        "code": f"UT{suffix}"[:30],
        "name": f"ЕИ по code+name {suffix}"[:250],
        "acronym": f"UT{suffix}"[:30],
    }
    _run_put_get_and_assert_checks(base_server_url, admin_auth, payload, put_url, get_url, full_check=False)


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Правило: обновление по Id")
def test_unit_update_by_id(base_server_url, admin_auth):
    """Создать единицу, получить id из GET, PUT с id и новыми полями → updated=1."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    payload1 = build_unique_unit_payload()
    response1 = _put_unit(put_url, payload=payload1, auth=admin_auth)
    assert response1.status_code == 200 and response1.json().get("added") == 1
    items = _get_units_list(get_url, admin_auth)
    found = _find_unit_by(items, "integrationId", payload1["integrationId"])
    assert found is not None, "Созданная единица не найдена в списке"
    unit_id = found.get("id")
    assert unit_id is not None, found
    new_name = f"Обновлено по Id {_unique_suffix()}"[:250]
    payload2 = {"id": unit_id, "name": new_name, "acronym": payload1["acronym"], "integrationId": payload1["integrationId"]}
    response2 = _put_unit(put_url, payload=payload2, auth=admin_auth)
    assert response2.status_code == 200, response2.text
    assert response2.json().get("updated") == 1, response2.json()
    items2 = _get_units_list(get_url, admin_auth)
    found2 = _find_unit_by(items2, "id", unit_id)
    assert found2 is not None and found2.get("name") == new_name, found2


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Правило: обновление по IntegrationId")
def test_unit_update_by_integration_id(base_server_url, admin_auth):
    """Создать с integrationId, второй PUT с тем же integrationId, другие поля → updated=1."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    payload1 = build_unique_unit_payload()
    response1 = _put_unit(put_url, payload=payload1, auth=admin_auth)
    assert response1.status_code == 200 and response1.json().get("added") == 1
    new_name = f"Обновлено по IntegrationId {_unique_suffix()}"[:250]
    payload2 = {**payload1, "name": new_name}
    response2 = _put_unit(put_url, payload=payload2, auth=admin_auth)
    assert response2.status_code == 200 and response2.json().get("updated") == 1
    items = _get_units_list(get_url, admin_auth)
    found = _find_unit_by(items, "integrationId", payload1["integrationId"])
    assert found is not None and found.get("name") == new_name


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Правило: обновление по Code+Name")
def test_unit_update_by_code_name(base_server_url, admin_auth):
    """Создать с code+name (без id, integrationId), второй PUT с теми же code+name → updated=1."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    suffix = _unique_suffix()
    code, name = f"UT{suffix}"[:30], f"ЕИ update code+name {suffix}"[:250]
    payload1 = {"code": code, "name": name, "acronym": f"UT{suffix}"[:30]}
    response1 = _put_unit(put_url, payload=payload1, auth=admin_auth)
    assert response1.status_code == 200 and response1.json().get("added") == 1
    payload2 = {"code": code, "name": name, "acronym": f"UT2{suffix}"[:30], "description": "Обновлено по Code+Name"}
    response2 = _put_unit(put_url, payload=payload2, auth=admin_auth)
    assert response2.status_code == 200 and response2.json().get("updated") == 1
    items = _get_units_list(get_url, admin_auth)
    found = _find_unit_by(items, "code", code)
    assert found is not None and found.get("description") == "Обновлено по Code+Name"


# --- Идемпотентность и несколько сущностей ---


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Идемпотентность: один и тот же запрос дважды — added=1, затем updated=1")
def test_unit_same_request_twice_create_then_update(base_server_url, admin_auth):
    """Один и тот же payload отправить дважды: первый раз added=1, второй updated=1."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    payload = build_unique_unit_payload()
    r1 = _put_unit(put_url, payload=payload, auth=admin_auth)
    assert r1.status_code == 200, r1.text
    assert r1.json().get("added") == 1, r1.json()
    r2 = _put_unit(put_url, payload=payload, auth=admin_auth)
    assert r2.status_code == 200, r2.text
    assert r2.json().get("updated") == 1, r2.json()
    items = _get_units_list(get_url, admin_auth)
    found = _find_unit_by(items, "integrationId", payload["integrationId"])
    assert found is not None and found.get("name") == payload["name"]


# --- Запрос без тела, без авторизации, битый JSON ---


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Запрос без тела (пустой body) — 400")
def test_unit_empty_body_rejected(base_server_url, admin_auth):
    """PUT с пустым телом {} или без обязательных полей → ожидается 400/422."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    try:
        response = _put_unit(put_url, payload={}, auth=admin_auth)
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"Нет связи с сервером: {e}")
    _assert_error_response(response)


@pytest.mark.negative
@pytest.mark.fast
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Запрос без авторизации — 401")
def test_unit_no_auth_rejected(base_server_url):
    """PUT без Basic Auth → 401."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    payload = build_minimal_unit_payload()
    try:
        response = _put_unit(put_url, payload=payload, auth=None)
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"Нет связи с сервером: {e}")
    _log_check("статус без авторизации", 401, response.status_code)
    assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /Unit/CreateOrUpdate: Невалидный JSON в теле — 400")
def test_unit_invalid_json_rejected(base_server_url, admin_auth):
    """PUT с телом не-JSON (битая строка) → 400 или 415."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    raw_body = b'{"name": "x", "acronym": '
    try:
        response = _put_unit(put_url, raw_body=raw_body, auth=admin_auth)
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"Нет связи с сервером: {e}")
    assert response.status_code in (400, 415, 422), f"Ожидался 400/415/422 при битом JSON, получен {response.status_code}. {response.text}"

"""
Тесты для API Unit: GET /Unit (Получение всех объектов).
Перед позитивными проверками создаётся одна единица через PUT, т.к. БД может быть пустой.
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
    _find_unit_by,
    _log_check,
    _put_unit,
)


GET_RESPONSE_SCHEMA_NAME = "PaginatedListOfRestUnit"
REQUIRED_KEYS = ("pageNum", "totalPages", "pageSize", "total", "hasPreviousPage", "hasNextPage", "items")


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


def get_unit_get_response_schema() -> dict:
    """Загружает из swagger.json схему ответа GET /Unit (PaginatedListOfRestUnit)."""
    from tests.api.unit.steps import get_unit_get_response_schema as step_get_schema

    return step_get_schema()


def _get_unit_response(get_url, admin_auth, page_num=0, page_size=0, no_count=False, timeout=30):
    """GET /Unit, возвращает объект response (для проверки status_code и .json())."""
    from tests.api.unit.steps import _get_unit_response as step_get_response

    return step_get_response(get_url, admin_auth, page_num=page_num, page_size=page_size, no_count=no_count, timeout=timeout)


@pytest.fixture(scope="module")
def unit_created_for_get(base_server_url, admin_auth):
    """
    Создаёт одну единицу через PUT /Unit/CreateOrUpdate для использования в тестах GET.
    Возвращает get_url, admin_auth и payload созданной единицы (для поиска в items).
    """
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    payload = build_unique_unit_payload()
    response = _put_unit(put_url, payload=payload, auth=admin_auth)
    assert response.status_code == 200, response.text
    assert response.json().get("added") == 1 or response.json().get("updated") == 1, response.json()
    yield get_url, admin_auth, payload


@pytest.mark.regression
@pytest.mark.fast
@pytest.mark.test_name_ru("GET /Unit: успешный ответ 200 и структура ответа")
def test_unit_get_success_structure(unit_created_for_get):
    """
    После создания одной единицы через PUT — GET /Unit с auth.
    Проверка: 200, наличие полей пагинации и items (массив), созданная единица в items.
    """
    print("\n  === Тест: GET /Unit — успешный ответ 200 и структура ответа ===\n")
    get_url, admin_auth, payload = unit_created_for_get
    response = _get_unit_response(get_url, admin_auth)
    _log_check("код ответа сервера GET /Unit", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    for key in REQUIRED_KEYS:
        has_key = key in data
        _log_check(f"наличие поля {key!r} в ответе GET /Unit", True, has_key)
        assert has_key, f"В ответе отсутствует поле {key!r}. Ключи: {list(data.keys())}"
    items = data.get("items")
    is_list = isinstance(items, list)
    _log_check("поле items — массив", True, is_list)
    assert is_list, f"items должен быть массивом, получен {type(items)}"
    found = _find_unit_by(items, "integrationId", payload["integrationId"])
    _log_check("созданная единица в списке GET /Unit (по integrationId)", True, found is not None)
    assert found is not None, (
        f"Созданная единица (integrationId={payload['integrationId']!r}) не найдена в items. Всего: {len(items)}"
    )


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("GET /Unit: соответствие ответа схеме PaginatedListOfRestUnit")
def test_unit_get_response_schema(unit_created_for_get):
    """После создания единицы через PUT — GET с auth, валидация ответа по схеме из swagger."""
    print("\n  === Тест: GET /Unit — соответствие ответа схеме PaginatedListOfRestUnit ===\n")
    get_url, admin_auth, _ = unit_created_for_get
    response = _get_unit_response(get_url, admin_auth)
    _log_check("код ответа сервера GET /Unit", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    schema = get_unit_get_response_schema()
    schema_valid = True
    schema_error = None
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        schema_valid = False
        schema_error = str(e)
    _log_check("соответствие ответа GET /Unit схеме PaginatedListOfRestUnit", True, schema_valid if schema_valid else schema_error)
    if not schema_valid:
        pytest.fail(f"Ответ не соответствует схеме: {schema_error}. Ответ: {data}")


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("GET /Unit: пагинация — pageSize ограничивает число записей")
def test_unit_get_pagination(unit_created_for_get):
    """После PUT одной единицы — GET с pageNum=0, pageSize=5; проверка len(items) <= 5."""
    print("\n  === Тест: GET /Unit — пагинация (pageSize ограничивает число записей) ===\n")
    get_url, admin_auth, _ = unit_created_for_get
    response = _get_unit_response(get_url, admin_auth, page_num=0, page_size=5)
    _log_check("код ответа сервера GET /Unit", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    items = data.get("items") or []
    _log_check("число элементов в items (не более 5)", "<= 5", len(items))
    assert len(items) <= 5, f"Ожидалось не более 5 элементов в items, получено {len(items)}"
    if "pageSize" in data:
        _log_check("поле pageSize в ответе", 5, data["pageSize"])
        assert data["pageSize"] == 5, f"Ожидался pageSize=5 в ответе, получен {data['pageSize']}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("GET /Unit: запрос без авторизации — 401")
def test_unit_get_no_auth_returns_401(base_server_url):
    """GET /Unit без заголовка Authorization — ожидается 401."""
    print("\n  === Тест: GET /Unit — запрос без авторизации (ожидается 401) ===\n")
    base = base_server_url.rstrip("/")
    get_url = f"{base}/Unit"
    response = _get_unit_response(get_url, admin_auth=None)
    _log_check("статус без авторизации", 401, response.status_code)
    assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}. {response.text}"

"""
Тесты для API UnitGroup: GET /UnitGroup (Получение всех объектов).
Перед позитивными проверками создаётся одна Unit (через Unit API) и одна UnitGroup через PUT.
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

from tests.api.unitgroup.test_unitgroup_create_or_update import (
    _find_unitgroup_by,
    _get_unitgroups_list,
    _log_check,
    _merge_allof,
    _openapi_nullable_to_jsonschema,
    _project_root,
    _put_unitgroup,
    build_unique_unitgroup_payload,
    ensure_one_unit_and_get_ref,
)

GET_RESPONSE_SCHEMA_NAME = "PaginatedListOfRestUnitGroup"
REQUIRED_KEYS = ("pageNum", "totalPages", "pageSize", "total", "hasPreviousPage", "hasNextPage", "items")


def get_unitgroup_get_response_schema() -> dict:
    """Загружает из swagger.json схему ответа GET /UnitGroup (PaginatedListOfRestUnitGroup)."""
    from tests.api.unitgroup.steps import get_unitgroup_get_response_schema as step_get_schema

    return step_get_schema()


def _get_unitgroup_response(get_url, admin_auth, page_num=0, page_size=0, no_count=False, timeout=30):
    """GET /UnitGroup, возвращает объект response."""
    from tests.api.unitgroup.steps import _get_unitgroup_response as step_get_response

    return step_get_response(
        get_url,
        admin_auth,
        page_num=page_num,
        page_size=page_size,
        no_count=no_count,
        timeout=timeout,
    )


@pytest.fixture(scope="module")
def unitgroup_created_for_get(base_server_url, admin_auth):
    """
    Создаёт одну Unit через PUT /Unit/CreateOrUpdate и одну UnitGroup через PUT /UnitGroup/CreateOrUpdate.
    Возвращает get_url, admin_auth и payload созданной группы (для поиска в items).
    """
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    get_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    response = _put_unitgroup(put_url, payload=payload, auth=admin_auth)
    assert response.status_code == 200, response.text
    assert response.json().get("added") == 1 or response.json().get("updated") == 1, response.json()
    yield get_url, admin_auth, payload


@pytest.mark.regression
@pytest.mark.fast
@pytest.mark.test_name_ru("GET /UnitGroup: успешный ответ 200 и структура ответа")
def test_unitgroup_get_success_structure(unitgroup_created_for_get):
    """После создания одной группы через PUT — GET /UnitGroup с auth. 200, поля пагинации и items, созданная группа в items."""
    print("\n  === Тест: GET /UnitGroup — успешный ответ 200 и структура ответа ===\n")
    get_url, admin_auth, payload = unitgroup_created_for_get
    response = _get_unitgroup_response(get_url, admin_auth)
    _log_check("код ответа сервера GET /UnitGroup", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    for key in REQUIRED_KEYS:
        has_key = key in data
        _log_check(f"наличие поля {key!r} в ответе GET /UnitGroup", True, has_key)
        assert has_key, f"В ответе отсутствует поле {key!r}. Ключи: {list(data.keys())}"
    items = data.get("items")
    is_list = isinstance(items, list)
    _log_check("поле items — массив", True, is_list)
    assert is_list, f"items должен быть массивом, получен {type(items)}"
    found = _find_unitgroup_by(items, "integrationId", payload["integrationId"])
    _log_check("созданная группа в списке GET /UnitGroup (по integrationId)", True, found is not None)
    assert found is not None, (
        f"Созданная группа (integrationId={payload['integrationId']!r}) не найдена в items. Всего: {len(items)}"
    )


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("GET /UnitGroup: соответствие ответа схеме PaginatedListOfRestUnitGroup")
def test_unitgroup_get_response_schema(unitgroup_created_for_get):
    """После создания группы через PUT — GET с auth, валидация ответа по схеме из swagger."""
    print("\n  === Тест: GET /UnitGroup — соответствие ответа схеме PaginatedListOfRestUnitGroup ===\n")
    get_url, admin_auth, _ = unitgroup_created_for_get
    response = _get_unitgroup_response(get_url, admin_auth)
    _log_check("код ответа сервера GET /UnitGroup", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    schema = get_unitgroup_get_response_schema()
    schema_valid = True
    schema_error = None
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        schema_valid = False
        schema_error = str(e)
    _log_check("соответствие ответа GET /UnitGroup схеме PaginatedListOfRestUnitGroup", True, schema_valid if schema_valid else schema_error)
    if not schema_valid:
        pytest.fail(f"Ответ не соответствует схеме: {schema_error}. Ответ: {data}")


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("GET /UnitGroup: пагинация — pageSize ограничивает число записей")
def test_unitgroup_get_pagination(unitgroup_created_for_get):
    """После PUT одной группы — GET с pageNum=0, pageSize=5; проверка len(items) <= 5."""
    print("\n  === Тест: GET /UnitGroup — пагинация (pageSize ограничивает число записей) ===\n")
    get_url, admin_auth, _ = unitgroup_created_for_get
    response = _get_unitgroup_response(get_url, admin_auth, page_num=0, page_size=5)
    _log_check("код ответа сервера GET /UnitGroup", 200, response.status_code)
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
@pytest.mark.test_name_ru("GET /UnitGroup: запрос без авторизации — 401")
def test_unitgroup_get_no_auth_returns_401(base_server_url):
    """GET /UnitGroup без заголовка Authorization — ожидается 401."""
    print("\n  === Тест: GET /UnitGroup — запрос без авторизации (ожидается 401) ===\n")
    base = base_server_url.rstrip("/")
    get_url = f"{base}/UnitGroup"
    response = _get_unitgroup_response(get_url, admin_auth=None)
    _log_check("статус без авторизации", 401, response.status_code)
    assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}. {response.text}"

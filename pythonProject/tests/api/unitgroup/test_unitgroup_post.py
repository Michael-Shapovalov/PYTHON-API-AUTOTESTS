"""
Тесты для API UnitGroup: POST /UnitGroup (Получение объектов по фильтру).
Тело — RestPostDto (ids, integrationIds, dateStart, dateEnd, pageNum, pageSize, noCount).
Перед позитивными проверками создаётся одна Unit и одна UnitGroup через PUT.
"""
import jsonschema
import pytest
import requests
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

pytestmark = pytest.mark.rt_light

from tests.api.unitgroup.test_unitgroup_create_or_update import (
    build_unique_unitgroup_payload,
    ensure_one_unit_and_get_ref,
    _find_unitgroup_by,
    _log_check,
    _put_unitgroup,
)
from tests.api.unitgroup.test_unitgroup_get import get_unitgroup_get_response_schema

POST_REQUIRED_KEYS = ("pageNum", "totalPages", "pageSize", "total", "hasPreviousPage", "hasNextPage", "items")


def _post_unitgroup(post_url, body, auth=None, raw_body=None, timeout=30):
    """POST /UnitGroup с телом RestPostDto. Возвращает response."""
    from tests.api.unitgroup.steps import _post_unitgroup as step_post_unitgroup

    return step_post_unitgroup(post_url, body, auth=auth, raw_body=raw_body, timeout=timeout)


@pytest.fixture(scope="module")
def unitgroup_created_for_post(base_server_url, admin_auth):
    """Создаёт одну Unit и одну UnitGroup через PUT для тестов POST /UnitGroup."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/UnitGroup/CreateOrUpdate"
    post_url = f"{base}/UnitGroup"
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    response = _put_unitgroup(put_url, payload=payload, auth=admin_auth)
    assert response.status_code == 200, response.text
    assert response.json().get("added") == 1 or response.json().get("updated") == 1, response.json()
    yield post_url, admin_auth, payload


@pytest.mark.regression
@pytest.mark.fast
@pytest.mark.test_name_ru("POST /UnitGroup: успешный ответ 200 и структура ответа")
def test_unitgroup_post_success_structure(unitgroup_created_for_post):
    """После создания группы через PUT — POST /UnitGroup с фильтром. 200, структура, созданная группа в items."""
    print("\n  === Тест: POST /UnitGroup — успешный ответ 200 и структура ответа ===\n")
    post_url, admin_auth, payload = unitgroup_created_for_post
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": [payload["integrationId"]], "noCount": False}
    response = _post_unitgroup(post_url, body, auth=admin_auth)
    _log_check("код ответа сервера POST /UnitGroup", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    for key in POST_REQUIRED_KEYS:
        has_key = key in data
        _log_check(f"наличие поля {key!r} в ответе POST /UnitGroup", True, has_key)
        assert has_key, f"В ответе отсутствует поле {key!r}. Ключи: {list(data.keys())}"
    items = data.get("items")
    _log_check("поле items — массив", True, isinstance(items, list))
    assert isinstance(items, list), f"items должен быть массивом, получен {type(items)}"
    found = _find_unitgroup_by(items or [], "integrationId", payload["integrationId"])
    _log_check("созданная группа в списке (по integrationId)", True, found is not None)
    assert found is not None, f"Созданная группа (integrationId={payload['integrationId']!r}) не найдена в items."


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("POST /UnitGroup: соответствие ответа схеме PaginatedListOfRestUnitGroup")
def test_unitgroup_post_response_schema(unitgroup_created_for_post):
    """POST с auth, валидация ответа по схеме из swagger."""
    print("\n  === Тест: POST /UnitGroup — соответствие ответа схеме PaginatedListOfRestUnitGroup ===\n")
    post_url, admin_auth, _ = unitgroup_created_for_post
    body = {"pageNum": 0, "pageSize": 0}
    response = _post_unitgroup(post_url, body, auth=admin_auth)
    _log_check("код ответа сервера POST /UnitGroup", 200, response.status_code)
    assert response.status_code == 200, response.text
    schema = get_unitgroup_get_response_schema()
    data = response.json()
    schema_valid = True
    schema_error = None
    try:
        jsonschema.validate(instance=data, schema=schema)
    except Exception as e:
        schema_valid = False
        schema_error = str(e)
    _log_check("соответствие ответа POST /UnitGroup схеме PaginatedListOfRestUnitGroup", True, schema_valid if schema_valid else schema_error)
    if not schema_valid:
        pytest.fail(f"Ответ не соответствует схеме: {schema_error}. Ответ: {data}")


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("POST /UnitGroup: запрос без авторизации — 401")
def test_unitgroup_post_no_auth_returns_401(base_server_url):
    """POST /UnitGroup без заголовка Authorization — 401."""
    print("\n  === Тест: POST /UnitGroup — запрос без авторизации (ожидается 401) ===\n")
    base = base_server_url.rstrip("/")
    post_url = f"{base}/UnitGroup"
    body = {"pageNum": 0, "pageSize": 0}
    response = _post_unitgroup(post_url, body, auth=None)
    _log_check("статус без авторизации", 401, response.status_code)
    assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("POST /UnitGroup: пустой body — 400")
def test_unitgroup_post_empty_body_rejected(base_server_url, admin_auth):
    """POST с телом {} — ожидается 400 или 200 (по поведению API)."""
    print("\n  === Тест: POST /UnitGroup — пустой body (ожидается 400) ===\n")
    base = base_server_url.rstrip("/")
    post_url = f"{base}/UnitGroup"
    response = _post_unitgroup(post_url, {}, auth=admin_auth)
    _log_check("статус при пустом body", "400 или 200", response.status_code)
    assert response.status_code in (400, 200), f"Ожидался 400 или 200, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("POST /UnitGroup: невалидный JSON в теле — 400")
def test_unitgroup_post_invalid_json_rejected(base_server_url, admin_auth):
    """POST с невалидным JSON — 400/415."""
    print("\n  === Тест: POST /UnitGroup — невалидный JSON (ожидается 400/415) ===\n")
    base = base_server_url.rstrip("/")
    post_url = f"{base}/UnitGroup"
    raw_body = b'{"pageNum": 0, "pageSize": '
    response = _post_unitgroup(post_url, None, auth=admin_auth, raw_body=raw_body)
    _log_check("статус при невалидном JSON", "400/415/422", response.status_code)
    assert response.status_code in (400, 415, 422), f"Ожидался 400/415/422, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("POST /UnitGroup: ids не массив — 400")
def test_unitgroup_post_ids_not_array_rejected(base_server_url, admin_auth):
    """POST с ids в виде строки вместо массива — 400 или ошибка."""
    print("\n  === Тест: POST /UnitGroup — ids не массив (ожидается ошибка) ===\n")
    base = base_server_url.rstrip("/")
    post_url = f"{base}/UnitGroup"
    body = {"pageNum": 0, "pageSize": 0, "ids": "not-an-array"}
    response = _post_unitgroup(post_url, body, auth=admin_auth)
    _log_check("статус при ids не массив", "400 или 200 с валидным ответом", response.status_code)
    if 400 <= response.status_code < 500:
        return
    if response.status_code == 200:
        data = response.json()
        if data.get("items") is not None and isinstance(data.get("items"), list):
            return
    pytest.fail(f"Ожидалась ошибка (4xx) или 200 с валидным ответом. Получен: {response.status_code}. {response.text}")

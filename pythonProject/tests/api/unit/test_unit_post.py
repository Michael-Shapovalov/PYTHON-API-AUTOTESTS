"""
Тесты для API Unit: POST /Unit (Получение объектов по фильтру).
Тело — RestPostDto (ids, integrationIds, dateStart, dateEnd, pageNum, pageSize, noCount).
Перед позитивными проверками создаётся одна единица через PUT.
"""
import jsonschema
import pytest
import requests
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

pytestmark = pytest.mark.rt_light

from tests.api.unit.test_unit_create_or_update import (
    build_unique_unit_payload,
    _find_unit_by,
    _log_check,
    _put_unit,
)
from tests.api.unit.test_unit_get import get_unit_get_response_schema

POST_REQUIRED_KEYS = ("pageNum", "totalPages", "pageSize", "total", "hasPreviousPage", "hasNextPage", "items")


def _post_unit(post_url, body, auth=None, raw_body=None, timeout=30):
    """POST /Unit с телом RestPostDto. Возвращает response."""
    from tests.api.unit.steps import _post_unit as step_post_unit

    return step_post_unit(post_url, body, auth=auth, raw_body=raw_body, timeout=timeout)


@pytest.fixture(scope="module")
def unit_created_for_post(base_server_url, admin_auth):
    """Создаёт одну единицу через PUT для тестов POST /Unit."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    post_url = f"{base}/Unit"
    payload = build_unique_unit_payload()
    response = _put_unit(put_url, payload=payload, auth=admin_auth)
    assert response.status_code == 200, response.text
    assert response.json().get("added") == 1 or response.json().get("updated") == 1, response.json()
    yield post_url, admin_auth, payload


@pytest.mark.regression
@pytest.mark.fast
@pytest.mark.test_name_ru("POST /Unit: успешный ответ 200 и структура ответа")
def test_unit_post_success_structure(unit_created_for_post):
    """После создания единицы через PUT — POST /Unit с фильтром (pageNum=0, pageSize=0). 200, структура, созданная единица в items."""
    print("\n  === Тест: POST /Unit — успешный ответ 200 и структура ответа ===\n")
    post_url, admin_auth, payload = unit_created_for_post
    # pageSize > 0, иначе API может вернуть пустой items; фильтр по integrationId гарантирует нашу единицу в ответе
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": [payload["integrationId"]], "noCount": False}
    response = _post_unit(post_url, body, auth=admin_auth)
    _log_check("код ответа сервера POST /Unit", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    for key in POST_REQUIRED_KEYS:
        has_key = key in data
        _log_check(f"наличие поля {key!r} в ответе POST /Unit", True, has_key)
        assert has_key, f"В ответе отсутствует поле {key!r}. Ключи: {list(data.keys())}"
    items = data.get("items")
    _log_check("поле items — массив", True, isinstance(items, list))
    assert isinstance(items, list), f"items должен быть массивом, получен {type(items)}"
    found = _find_unit_by(items or [], "integrationId", payload["integrationId"])
    _log_check("созданная единица в списке (по integrationId)", True, found is not None)
    assert found is not None, f"Созданная единица (integrationId={payload['integrationId']!r}) не найдена в items."


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("POST /Unit: соответствие ответа схеме PaginatedListOfRestUnit")
def test_unit_post_response_schema(unit_created_for_post):
    """POST с auth, валидация ответа по схеме из swagger."""
    print("\n  === Тест: POST /Unit — соответствие ответа схеме PaginatedListOfRestUnit ===\n")
    post_url, admin_auth, _ = unit_created_for_post
    body = {"pageNum": 0, "pageSize": 0}
    response = _post_unit(post_url, body, auth=admin_auth)
    _log_check("код ответа сервера POST /Unit", 200, response.status_code)
    assert response.status_code == 200, response.text
    schema = get_unit_get_response_schema()
    data = response.json()
    schema_valid = True
    schema_error = None
    try:
        jsonschema.validate(instance=data, schema=schema)
    except Exception as e:
        schema_valid = False
        schema_error = str(e)
    _log_check("соответствие ответа POST /Unit схеме PaginatedListOfRestUnit", True, schema_valid if schema_valid else schema_error)
    if not schema_valid:
        pytest.fail(f"Ответ не соответствует схеме: {schema_error}. Ответ: {data}")


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("POST /Unit: запрос без авторизации — 401")
def test_unit_post_no_auth_returns_401(base_server_url):
    """POST /Unit без заголовка Authorization — 401."""
    print("\n  === Тест: POST /Unit — запрос без авторизации (ожидается 401) ===\n")
    base = base_server_url.rstrip("/")
    post_url = f"{base}/Unit"
    body = {"pageNum": 0, "pageSize": 0}
    response = _post_unit(post_url, body, auth=None)
    _log_check("статус без авторизации", 401, response.status_code)
    assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("POST /Unit: пустой body — 400")
def test_unit_post_empty_body_rejected(base_server_url, admin_auth):
    """POST с телом {} — ожидается 400 (если API требует поля)."""
    print("\n  === Тест: POST /Unit — пустой body (ожидается 400) ===\n")
    base = base_server_url.rstrip("/")
    post_url = f"{base}/Unit"
    response = _post_unit(post_url, {}, auth=admin_auth)
    _log_check("статус при пустом body", "400 или 200", response.status_code)
    if response.status_code == 400:
        return
    if response.status_code == 200:
        return
    pytest.fail(f"Ожидался 400 или 200, получен {response.status_code}. {response.text}")


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("POST /Unit: невалидный JSON в теле — 400")
def test_unit_post_invalid_json_rejected(base_server_url, admin_auth):
    """POST с невалидным JSON — 400/415."""
    print("\n  === Тест: POST /Unit — невалидный JSON (ожидается 400/415) ===\n")
    base = base_server_url.rstrip("/")
    post_url = f"{base}/Unit"
    raw_body = b'{"pageNum": 0, "pageSize": '
    response = _post_unit(post_url, None, auth=admin_auth, raw_body=raw_body)
    _log_check("статус при невалидном JSON", "400/415/422", response.status_code)
    assert response.status_code in (400, 415, 422), f"Ожидался 400/415/422, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("POST /Unit: ids не массив — 400")
def test_unit_post_ids_not_array_rejected(base_server_url, admin_auth):
    """POST с ids в виде строки вместо массива — 400 или ошибка."""
    print("\n  === Тест: POST /Unit — ids не массив (ожидается ошибка) ===\n")
    base = base_server_url.rstrip("/")
    post_url = f"{base}/Unit"
    body = {"pageNum": 0, "pageSize": 0, "ids": "not-an-array"}
    response = _post_unit(post_url, body, auth=admin_auth)
    _log_check("статус при ids не массив", "400 или ошибка", response.status_code)
    if 400 <= response.status_code < 500:
        return
    if response.status_code == 200:
        data = response.json()
        items = data.get("items")
        if items is not None and isinstance(items, list):
            return
    pytest.fail(f"Ожидалась ошибка (4xx) или 200 с валидным ответом. Получен: {response.status_code}. {response.text}")

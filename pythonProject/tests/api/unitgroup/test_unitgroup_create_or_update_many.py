"""
Тесты для API UnitGroup: PUT /UnitGroup/CreateOrUpdateMany.
Тело — массив RestUnitGroup; ответ 200 — RestResponseDtoOfRestUnitGroup.
"""
import jsonschema
import pytest
import requests
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError

pytestmark = pytest.mark.rt_light

from tests.api.unitgroup.test_unitgroup_create_or_update import (
    build_unique_unitgroup_payload,
    ensure_one_unit_and_get_ref,
    get_unitgroup_create_or_update_response_schema,
    _log_check,
)

RESPONSE_KEYS = ("count", "added", "updated", "deleted", "errors", "results")


def _put_create_or_update_many(base_url, payloads, auth, raw_body=None, timeout=30):
    """PUT /UnitGroup/CreateOrUpdateMany. payloads — список RestUnitGroup или None при raw_body."""
    from tests.api.unitgroup.steps import _put_create_or_update_many as step_put_many

    return step_put_many(base_url, payloads, auth, raw_body=raw_body, timeout=timeout)


@pytest.mark.regression
@pytest.mark.fast
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdateMany: успешный ответ 200 и структура (один элемент)")
def test_unitgroup_create_or_update_many_success_one(base_server_url, admin_auth):
    """Массив из одной группы — 200, count/added/updated/results, один результат без errorMessage."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdateMany — успешный ответ 200 и структура (один элемент) ===\n")
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    response = _put_create_or_update_many(base_server_url, [payload], admin_auth)
    _log_check("код ответа PUT /UnitGroup/CreateOrUpdateMany", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    for key in RESPONSE_KEYS:
        has_key = key in data
        _log_check(f"наличие поля {key!r}", True, has_key)
        assert has_key, f"В ответе отсутствует поле {key!r}. Ключи: {list(data.keys())}"
    added = data.get("added")
    results = data.get("results") or []
    _log_check("added >= 1 при одной новой группе", True, (added or 0) >= 1)
    assert (added or 0) >= 1, f"Ожидался added >= 1, получен added={added}. Ответ: {data}"
    _log_check("один элемент в results", 1, len(results))
    assert len(results) == 1, f"Ожидался 1 элемент в results, получено {len(results)}"
    first = results[0] if results else {}
    err_msg = first.get("errorMessage") or first.get("error")
    _log_check("результат без ошибки (errorMessage)", "отсутствует/пусто", err_msg or "—")
    assert not err_msg, f"Ожидалось отсутствие ошибки в results[0], получено: {err_msg}"


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdateMany: соответствие ответа схеме RestResponseDtoOfRestUnitGroup")
def test_unitgroup_create_or_update_many_response_schema(base_server_url, admin_auth):
    """Один элемент в теле — 200, валидация ответа по схеме."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdateMany — соответствие ответа схеме ===\n")
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    response = _put_create_or_update_many(base_server_url, [payload], admin_auth)
    _log_check("код ответа PUT /UnitGroup/CreateOrUpdateMany", 200, response.status_code)
    assert response.status_code == 200, response.text
    schema = get_unitgroup_create_or_update_response_schema()
    data = response.json()
    try:
        jsonschema.validate(instance=data, schema=schema)
        schema_valid = True
        schema_error = None
    except jsonschema.ValidationError as e:
        schema_valid = False
        schema_error = str(e)
    _log_check("соответствие ответа схеме RestResponseDtoOfRestUnitGroup", True, schema_valid if schema_valid else schema_error)
    if not schema_valid:
        pytest.fail(f"Ответ не соответствует схеме: {schema_error}. Ответ: {data}")


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdateMany: пустой массив [] — 200, без падения")
def test_unitgroup_create_or_update_many_empty_array(base_server_url, admin_auth):
    """Тело [] — 200, count=0 (или по документации)."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdateMany — пустой массив [] ===\n")
    response = _put_create_or_update_many(base_server_url, [], admin_auth)
    _log_check("код ответа при пустом массиве", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    count = data.get("count")
    _log_check("count при пустом массиве", "0 или отсутствует", count)
    assert count == 0 or count is None or (isinstance(count, int) and count >= 0), f"Неожиданный count: {count}"


@pytest.mark.regression
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdateMany: несколько элементов (2–3) — 200, все в results")
def test_unitgroup_create_or_update_many_several_items(base_server_url, admin_auth):
    """Массив из 2–3 групп — 200, added/updated суммарно, все в results."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdateMany — несколько элементов (2–3) ===\n")
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payloads = [build_unique_unitgroup_payload(base_unit_ref) for _ in range(3)]
    response = _put_create_or_update_many(base_server_url, payloads, admin_auth)
    _log_check("код ответа PUT /UnitGroup/CreateOrUpdateMany", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    results = data.get("results") or []
    _log_check("число элементов в results", 3, len(results))
    assert len(results) == 3, f"Ожидалось 3 элемента в results, получено {len(results)}"
    total = (data.get("added") or 0) + (data.get("updated") or 0)
    _log_check("added + updated (суммарно)", ">= 1", total)
    assert total >= 1, f"Ожидалось added+updated >= 1, получено {total}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdateMany: запрос без авторизации — 401")
def test_unitgroup_create_or_update_many_no_auth_returns_401(base_server_url):
    """PUT CreateOrUpdateMany без auth — 401. Payload с заглушкой baseUnit (id=1), проверяется только 401."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdateMany — без авторизации (401) ===\n")
    payload = build_unique_unitgroup_payload({"id": 1})
    response = _put_create_or_update_many(base_server_url, [payload], auth=None)
    _log_check("статус без авторизации", 401, response.status_code)
    assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdateMany: тело не массив — 400")
def test_unitgroup_create_or_update_many_body_not_array(base_server_url, admin_auth):
    """Тело — один объект без обёртки в массив — 400 или ошибка."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdateMany — тело не массив (ожидается 400) ===\n")
    base_unit_ref = ensure_one_unit_and_get_ref(base_server_url, admin_auth)
    payload = build_unique_unitgroup_payload(base_unit_ref)
    response = _put_create_or_update_many(base_server_url, payload, admin_auth)
    _log_check("статус при теле не массив", "400 или ошибка", response.status_code)
    if 400 <= response.status_code < 500:
        return
    if response.status_code == 200:
        data = response.json()
        if data.get("errors") or (data.get("results") and (data.get("results")[0] or {}).get("errorMessage")):
            return
    pytest.fail(f"Ожидалась ошибка (4xx или 200 с ошибкой). Получен: {response.status_code}. {response.text}")


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PUT /UnitGroup/CreateOrUpdateMany: невалидный JSON — 400")
def test_unitgroup_create_or_update_many_invalid_json(base_server_url, admin_auth):
    """Невалидный JSON в теле — 400."""
    print("\n  === Тест: PUT /UnitGroup/CreateOrUpdateMany — невалидный JSON ===\n")
    raw_body = b'[{"code": "x", "name": "y"'
    response = _put_create_or_update_many(base_server_url, None, admin_auth, raw_body=raw_body)
    _log_check("статус при невалидном JSON", "400/415/422", response.status_code)
    assert response.status_code in (400, 415, 422), f"Ожидался 400/415/422, получен {response.status_code}. {response.text}"

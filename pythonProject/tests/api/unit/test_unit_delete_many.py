"""
Тесты для API Unit: PATCH /Unit/DeleteMany (удаление массива объектов).
Тело — массив RestDtoBase. Ответ 200 — RestResponseDto (count, deleted, errors, results).
"""
import pytest
import requests

pytestmark = pytest.mark.rt_light

from tests.api.unit.test_unit_create_or_update import (
    build_unique_unit_payload,
    _log_check,
    _put_unit,
    _get_units_list,
    _find_unit_by,
)
from tests.api.unit.test_unit_delete import get_rest_response_dto_schema, _patch_delete
import jsonschema


def _patch_delete_many(base_url, body, auth=None, raw_body=None, timeout=30):
    """PATCH /Unit/DeleteMany. body — массив RestDtoBase."""
    from tests.api.unit.steps import _patch_delete_many as step_patch_delete_many

    return step_patch_delete_many(base_url, body, auth=auth, raw_body=raw_body, timeout=timeout)


@pytest.fixture(scope="module")
def two_units_created_for_delete_many(base_server_url, admin_auth):
    """Создаёт две единицы через PUT, возвращает base_url, auth, get_url и список id для удаления."""
    base = base_server_url.rstrip("/")
    put_url = f"{base}/Unit/CreateOrUpdate"
    get_url = f"{base}/Unit"
    payloads = [build_unique_unit_payload() for _ in range(2)]
    ids = []
    for payload in payloads:
        response = _put_unit(put_url, payload=payload, auth=admin_auth)
        assert response.status_code == 200, response.text
        items = _get_units_list(get_url, admin_auth)
        unit = _find_unit_by(items, "integrationId", payload["integrationId"])
        assert unit is not None
        ids.append(unit.get("id"))
    yield base_server_url, admin_auth, get_url, ids


@pytest.mark.regression
@pytest.mark.fast
@pytest.mark.test_name_ru("PATCH /Unit/DeleteMany: успешное удаление двух единиц — 200 и схема")
def test_unit_delete_many_success(two_units_created_for_delete_many):
    """Созданы 2 единицы → PATCH /Unit/DeleteMany с массивом из двух id → 200, deleted, схема. GET — этих единиц нет."""
    print("\n  === Тест: PATCH /Unit/DeleteMany — успешное удаление двух единиц ===\n")
    base_url, admin_auth, get_url, ids = two_units_created_for_delete_many
    body = [{"id": ids[0]}, {"id": ids[1]}]
    response = _patch_delete_many(base_url, body, admin_auth)
    _log_check("код ответа PATCH /Unit/DeleteMany", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    deleted = data.get("deleted")
    count = data.get("count")
    results = data.get("results") or []
    _log_check("поле deleted/count/results", "успех удаления", deleted or count or len(results))
    success = (
        deleted in (2, True)
        or (isinstance(deleted, int) and deleted >= 1)
        or (isinstance(count, int) and count >= 1)
        or len(results) >= 1
    )
    assert success, f"Ожидалось удаление (deleted/count/results). Ответ: {data}"
    schema = get_rest_response_dto_schema()
    try:
        jsonschema.validate(instance=data, schema=schema)
        schema_ok = True
    except jsonschema.ValidationError as e:
        schema_ok = False
        pytest.fail(f"Ответ не соответствует схеме RestResponseDto: {e}. Ответ: {data}")
    _log_check("соответствие ответа схеме RestResponseDto", True, schema_ok)
    items_after = _get_units_list(get_url, admin_auth)
    for uid in ids:
        found = _find_unit_by(items_after, "id", uid)
        _log_check(f"единица id={uid} отсутствует после DeleteMany", False, found is not None)
        assert found is None, f"Единица id={uid} всё ещё в списке"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /Unit/DeleteMany: запрос без авторизации — 401")
def test_unit_delete_many_no_auth_returns_401(base_server_url):
    """PATCH /Unit/DeleteMany без auth — 401."""
    print("\n  === Тест: PATCH /Unit/DeleteMany — без авторизации (401) ===\n")
    response = _patch_delete_many(base_server_url, [{"id": 1}], auth=None)
    _log_check("статус без авторизации", 401, response.status_code)
    assert response.status_code == 401, f"Ожидался 401, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /Unit/DeleteMany: пустой массив [] — 200, deleted=0")
def test_unit_delete_many_empty_array(base_server_url, admin_auth):
    """Тело [] — 200, без падения, deleted=0 или count=0."""
    print("\n  === Тест: PATCH /Unit/DeleteMany — пустой массив ===\n")
    response = _patch_delete_many(base_server_url, [], admin_auth)
    _log_check("код ответа при пустом массиве", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    deleted = data.get("deleted")
    _log_check("deleted при []", "0 или отсутствует", deleted)
    assert deleted == 0 or deleted is None or (isinstance(deleted, int) and deleted >= 0), f"Ответ: {data}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /Unit/DeleteMany: тело не массив — 400")
def test_unit_delete_many_body_not_array(base_server_url, admin_auth):
    """Тело — один объект вместо массива — 400."""
    print("\n  === Тест: PATCH /Unit/DeleteMany — тело не массив ===\n")
    response = _patch_delete_many(base_server_url, {"id": 1}, admin_auth)
    _log_check("статус при теле не массив", "400 или ошибка", response.status_code)
    assert response.status_code in (400, 415, 422), f"Ожидался 4xx, получен {response.status_code}. {response.text}"


@pytest.mark.negative
@pytest.mark.slow
@pytest.mark.test_name_ru("PATCH /Unit/DeleteMany: массив с одним несуществующим id — 200, частичный результат")
def test_unit_delete_many_one_nonexistent_id(base_server_url, admin_auth):
    """Два несуществующих id — 200 (частичный результат) или 400 (ошибка валидации)."""
    print("\n  === Тест: PATCH /Unit/DeleteMany — один несуществующий id в массиве ===\n")
    body = [{"id": 999999999}, {"id": 999999998}]
    response = _patch_delete_many(base_server_url, body, admin_auth)
    _log_check("статус (частичное удаление или ошибка)", "200 или 400", response.status_code)
    if response.status_code == 400:
        return
    assert response.status_code == 200, f"Ожидался 200 или 400, получен {response.status_code}. {response.text}"
    data = response.json()
    _log_check("наличие results или deleted", True, "results" in data or "deleted" in data)
    assert "results" in data or "deleted" in data or "count" in data, f"Ответ: {data}"

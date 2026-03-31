"""
Smoke-тесты для API Personnel: последовательный сценарий (создание → обновление одного → пачка → обновление пачки → GET с проверкой полей → Delete → POST фильтр → DeleteMany → финальный POST-поиск чистоты).
Состояние между тестами передаётся через fixture smoke_state (scope=module). Порядок выполнения — pytest-order.
Personnel требует существующих ProductionUnit и Profession; в smoke используются фиксированные ссылки (id), задаваемые в фикстурах.
Проверки и предусловия (guards) — в tests.api.smoke_checks; подготовка payload для update — в steps.
"""
import copy

import pytest
import testit

from tests.utils.testit_smoke_docs import get_smoke_tc_description

from tests.api.smoke_checks import (
    assert_create_one_response,
    assert_create_many_response,
    assert_delete_many_response,
    assert_delete_one_response,
    assert_list_contains_and_names,
    assert_post_filter_count,
    assert_post_filter_items_empty,
    assert_update_many_response,
    assert_update_one_response,
    get_required_state,
    get_required_state_list,
    run_smoke_request,
)
from tests.api.personnel.steps import (
    _find_personnel_by,
    _get_personnel_list,
    _patch_delete,
    _patch_delete_many,
    _post_personnel,
    _put_create_or_update_many,
    _put_personnel,
    build_updated_payload_smoke,
    build_updated_payloads_smoke,
    build_unique_personnel_payload,
)


# --- Фикстуры ---


@pytest.fixture(scope="module")
def smoke_base_production_unit_ref():
    """Базовый производственный участок для Personnel (id нужно подставить из боевой БД)."""
    return {"id": 2}


@pytest.fixture(scope="module")
def smoke_base_profession_ref():
    """Базовая профессия для Personnel (id нужно подставить из боевой БД)."""
    return {"id": 1}


@pytest.fixture(scope="module")
def smoke_state():
    """Общее состояние smoke-сценария: id, integrationId, payload и обновлённые значения полей для A, B1, B2."""
    return {
        "pers_a_id": None,
        "pers_a_integration_id": None,
        "pers_a_payload": None,
        "pers_a_name_updated": None,
        "pers_b_ids": [],
        "pers_b_integration_ids": [],
        "pers_b_payloads": [],
        "pers_b_names_updated": [],
    }


@pytest.fixture(scope="module")
def smoke_urls(base_server_url):
    """URL для smoke-тестов Personnel."""
    base = base_server_url.rstrip("/")
    return {
        "put_url": f"{base}/Personnel/CreateOrUpdate",
        "put_many_url": base,
        "get_url": f"{base}/Personnel",
        "post_url": f"{base}/Personnel",
    }


# --- Тесты ---


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(30)
@pytest.mark.test_name_ru("Smoke: PUT /Personnel/CreateOrUpdate — создание одного объекта")
@testit.externalId("smoke_personnel_01_create_one")
@testit.displayName("Smoke: PUT /Personnel/CreateOrUpdate — создание одного объекта")
@testit.title("Smoke: PUT /Personnel/CreateOrUpdate — создание одного объекта")
@testit.description(get_smoke_tc_description("personnel", 1))
@testit.nameSpace("API/Smoke")
@testit.className("Personnel")
@testit.labels("api", "smoke", "personnel")
def test_01_create_one(smoke_state, smoke_urls, smoke_base_production_unit_ref, smoke_base_profession_ref, admin_auth):
    """PUT /Personnel/CreateOrUpdate с минимально валидным payload. 200, added==1, errors==0, в ответе entity.id."""
    print("\n  === Smoke: 1. PUT /Personnel/CreateOrUpdate — создание одного объекта ===\n")
    payload = build_unique_personnel_payload(smoke_base_production_unit_ref, smoke_base_profession_ref)
    response = run_smoke_request(lambda: _put_personnel(smoke_urls["put_url"], payload=payload, auth=admin_auth))
    uid, iid = assert_create_one_response(response, payload)
    smoke_state["pers_a_id"] = uid
    smoke_state["pers_a_integration_id"] = iid
    smoke_state["pers_a_payload"] = copy.deepcopy(payload)


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(31)
@pytest.mark.test_name_ru("Smoke: PUT /Personnel/CreateOrUpdate — обновление одного объекта")
@testit.externalId("smoke_personnel_01b_update_one")
@testit.displayName("Smoke: PUT /Personnel/CreateOrUpdate — обновление одного объекта")
@testit.title("Smoke: PUT /Personnel/CreateOrUpdate — обновление одного объекта")
@testit.description(get_smoke_tc_description("personnel", 2))
@testit.nameSpace("API/Smoke")
@testit.className("Personnel")
@testit.labels("api", "smoke", "personnel")
def test_01b_update_one(smoke_state, smoke_urls, admin_auth):
    """PUT /Personnel/CreateOrUpdate — обновление объекта A (тот же integrationId), поле name/fullName изменено. 200, result Updated, updated: 1."""
    print("\n  === Smoke: 1b. PUT /Personnel/CreateOrUpdate — обновление одного объекта ===\n")
    payload = get_required_state(
        smoke_state,
        "pers_a_payload",
        "pers_a_payload не сохранён (запустите test_01_create_one)",
    )
    payload_updated, name_updated = build_updated_payload_smoke(payload)
    response = run_smoke_request(lambda: _put_personnel(smoke_urls["put_url"], payload=payload_updated, auth=admin_auth))
    assert_update_one_response(response)
    smoke_state["pers_a_name_updated"] = name_updated


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(32)
@pytest.mark.test_name_ru("Smoke: PUT /Personnel/CreateOrUpdateMany — создание двух объектов")
@testit.externalId("smoke_personnel_02_create_many")
@testit.displayName("Smoke: PUT /Personnel/CreateOrUpdateMany — создание двух объектов")
@testit.title("Smoke: PUT /Personnel/CreateOrUpdateMany — создание двух объектов")
@testit.description(get_smoke_tc_description("personnel", 3))
@testit.nameSpace("API/Smoke")
@testit.className("Personnel")
@testit.labels("api", "smoke", "personnel")
def test_02_create_many(smoke_state, smoke_urls, smoke_base_production_unit_ref, smoke_base_profession_ref, admin_auth):
    """PUT /Personnel/CreateOrUpdateMany, массив из двух объектов. 200, added==2, errors==0, два элемента в results."""
    print("\n  === Smoke: 2. PUT /Personnel/CreateOrUpdateMany — создание двух объектов ===\n")
    payloads = [
        build_unique_personnel_payload(smoke_base_production_unit_ref, smoke_base_profession_ref)
        for _ in range(2)
    ]
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads, admin_auth))
    ids, integration_ids = assert_create_many_response(response, payloads)
    smoke_state["pers_b_ids"] = ids
    smoke_state["pers_b_integration_ids"] = integration_ids
    smoke_state["pers_b_payloads"] = copy.deepcopy(payloads)


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(33)
@pytest.mark.test_name_ru("Smoke: PUT /Personnel/CreateOrUpdateMany — обновление двух объектов")
@testit.externalId("smoke_personnel_02b_update_many")
@testit.displayName("Smoke: PUT /Personnel/CreateOrUpdateMany — обновление двух объектов")
@testit.title("Smoke: PUT /Personnel/CreateOrUpdateMany — обновление двух объектов")
@testit.description(get_smoke_tc_description("personnel", 4))
@testit.nameSpace("API/Smoke")
@testit.className("Personnel")
@testit.labels("api", "smoke", "personnel")
def test_02b_update_many(smoke_state, smoke_urls, admin_auth):
    """PUT /Personnel/CreateOrUpdateMany — обновление B1, B2 (те же integrationId), у каждого изменено поле name/fullName. 200, updated: 2."""
    print("\n  === Smoke: 2b. PUT /Personnel/CreateOrUpdateMany — обновление двух объектов ===\n")
    payloads = get_required_state_list(
        smoke_state,
        "pers_b_payloads",
        2,
        "pers_b_payloads не заполнены (запустите test_02_create_many)",
    )
    payloads_updated, names_updated = build_updated_payloads_smoke(payloads)
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads_updated, admin_auth))
    assert_update_many_response(response, count=2)
    smoke_state["pers_b_names_updated"] = names_updated


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(34)
@pytest.mark.test_name_ru("Smoke: GET /Personnel — в списке есть A, B1, B2 и поля после обновления")
@testit.externalId("smoke_personnel_03_get_list")
@testit.displayName("Smoke: GET /Personnel — в списке есть A, B1, B2 и поля после обновления")
@testit.title("Smoke: GET /Personnel — в списке есть A, B1, B2 и поля после обновления")
@testit.description(get_smoke_tc_description("personnel", 5))
@testit.nameSpace("API/Smoke")
@testit.className("Personnel")
@testit.labels("api", "smoke", "personnel")
def test_03_get_list(smoke_state, smoke_urls, admin_auth):
    """GET /Personnel. 200, items — массив, в нём есть A, B1, B2 (по integrationId) и поля name совпадают с обновлёнными."""
    print("\n  === Smoke: 3. GET /Personnel — список содержит созданные объекты и значения после обновления ===\n")
    try:
        items = _get_personnel_list(smoke_urls["get_url"], admin_auth, page_size=5000)
    except AssertionError as e:
        pytest.fail(f"GET /Personnel не вернул 200 или items: {e}")
    id_a = get_required_state(
        smoke_state,
        "pers_a_integration_id",
        "pers_a_integration_id не в state (запустите предыдущие шаги)",
    )
    ids_b = get_required_state_list(
        smoke_state,
        "pers_b_integration_ids",
        2,
        "pers_b_integration_ids не заполнены",
    )
    name_a_expected = smoke_state.get("pers_a_name_updated")
    names_b_expected = smoke_state.get("pers_b_names_updated") or []
    assert_list_contains_and_names(
        items,
        id_a,
        ids_b,
        _find_personnel_by,
        name_a_expected=name_a_expected,
        names_b_expected=names_b_expected,
    )


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(35)
@pytest.mark.test_name_ru("Smoke: PATCH /Personnel/Delete — удаление объекта A")
@testit.externalId("smoke_personnel_04_delete_one")
@testit.displayName("Smoke: PATCH /Personnel/Delete — удаление объекта A")
@testit.title("Smoke: PATCH /Personnel/Delete — удаление объекта A")
@testit.description(get_smoke_tc_description("personnel", 6))
@testit.nameSpace("API/Smoke")
@testit.className("Personnel")
@testit.labels("api", "smoke", "personnel")
def test_04_delete_one(smoke_state, smoke_urls, admin_auth):
    """PATCH /Personnel/Delete по integrationId объекта A. 200/204, deleted==1 при наличии тела."""
    print("\n  === Smoke: 4. PATCH /Personnel/Delete — удаление объекта A ===\n")
    pers_a_integration_id = get_required_state(
        smoke_state,
        "pers_a_integration_id",
        "pers_a_integration_id не сохранён в smoke_state (запустите test_01_create_one)",
    )
    response = run_smoke_request(
        lambda: _patch_delete(
            smoke_urls["put_many_url"], {"integrationId": pers_a_integration_id}, admin_auth
        )
    )
    assert_delete_one_response(response)


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(36)
@pytest.mark.test_name_ru("Smoke: POST /Personnel — фильтр по B1 и B2")
@testit.externalId("smoke_personnel_05_post_filter")
@testit.displayName("Smoke: POST /Personnel — фильтр по B1 и B2")
@testit.title("Smoke: POST /Personnel — фильтр по B1 и B2")
@testit.description(get_smoke_tc_description("personnel", 7))
@testit.nameSpace("API/Smoke")
@testit.className("Personnel")
@testit.labels("api", "smoke", "personnel")
def test_05_post_filter(smoke_state, smoke_urls, admin_auth):
    """POST /Personnel с фильтром по integrationIds B1 и B2. 200, в items ровно B1 и B2."""
    print("\n  === Smoke: 5. POST /Personnel — фильтр по B1 и B2 ===\n")
    integration_ids_b = get_required_state_list(
        smoke_state,
        "pers_b_integration_ids",
        2,
        "pers_b_integration_ids не заполнены",
    )
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids_b, "noCount": False}
    response = _post_personnel(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_count(response, 2)


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(37)
@pytest.mark.test_name_ru("Smoke: PATCH /Personnel/DeleteMany — удаление B1 и B2")
@testit.externalId("smoke_personnel_06_delete_many")
@testit.displayName("Smoke: PATCH /Personnel/DeleteMany — удаление B1 и B2")
@testit.title("Smoke: PATCH /Personnel/DeleteMany — удаление B1 и B2")
@testit.description(get_smoke_tc_description("personnel", 8))
@testit.nameSpace("API/Smoke")
@testit.className("Personnel")
@testit.labels("api", "smoke", "personnel")
def test_06_delete_many(smoke_state, smoke_urls, admin_auth):
    """PATCH /Personnel/DeleteMany по integrationId объектов B1 и B2. 200/204, deleted==2 при наличии тела."""
    print("\n  === Smoke: 6. PATCH /Personnel/DeleteMany — удаление B1 и B2 ===\n")
    ids_b_integration = get_required_state_list(
        smoke_state,
        "pers_b_integration_ids",
        2,
        "pers_b_integration_ids не заполнены",
    )
    body = [{"integrationId": ids_b_integration[0]}, {"integrationId": ids_b_integration[1]}]
    response = _patch_delete_many(smoke_urls["put_many_url"], body, admin_auth)
    assert_delete_many_response(response, expected_deleted=2)


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(38)
@pytest.mark.test_name_ru("Smoke: POST /Personnel — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.externalId("smoke_personnel_07_post_clean")
@testit.displayName("Smoke: POST /Personnel — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.title("Smoke: POST /Personnel — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.description(get_smoke_tc_description("personnel", 9))
@testit.nameSpace("API/Smoke")
@testit.className("Personnel")
@testit.labels("api", "smoke", "personnel")
def test_07_post_clean(smoke_state, smoke_urls, admin_auth):
    """Финальный POST /Personnel. Фильтр по integrationIds A, B1, B2 и проверка, что items пустой (объекты действительно удалены)."""
    print("\n  === Smoke: 7. POST /Personnel — финальная проверка чистоты (фильтр по A, B1, B2) ===\n")
    id_a = get_required_state(
        smoke_state,
        "pers_a_integration_id",
        "pers_a_integration_id не сохранён в smoke_state (запустите предыдущие шаги)",
    )
    ids_b = get_required_state_list(
        smoke_state,
        "pers_b_integration_ids",
        2,
        "pers_b_integration_ids не заполнены (запустите предыдущие шаги)",
    )
    integration_ids = [id_a] + list(ids_b)
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids, "noCount": False}
    response = _post_personnel(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_items_empty(response)


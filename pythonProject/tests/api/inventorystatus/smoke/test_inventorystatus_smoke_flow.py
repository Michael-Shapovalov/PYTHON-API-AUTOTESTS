"""
Smoke-тесты для API InventoryStatus: последовательный сценарий (создание → обновление одного → пачка → обновление пачки → GET с проверкой полей → Delete → POST фильтр → DeleteMany → финальный POST-поиск чистоты).
Состояние между тестами передаётся через fixture smoke_state (scope=module). Порядок выполнения — pytest-order.
Проверки и предусловия (guards) — в tests.api.smoke_checks; подготовка payload для update — в steps.
"""
import copy

import pytest
import testit

from tests.utils.testit_smoke_docs import get_smoke_tc_description

from tests.api.smoke_checks import (
    assert_create_many_response,
    assert_create_one_response,
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
from tests.api.inventorystatus.steps import (
    _find_by,
    _get_list,
    _patch_delete,
    _patch_delete_many,
    _post_filter,
    _put_create_or_update_many,
    _put_inventorystatus,
    build_unique_inventorystatus_payload,
    build_updated_payload_smoke,
    build_updated_payloads_smoke,
)


@pytest.fixture(scope="module")
def smoke_state():
    return {
        "a_id": None,
        "a_integration_id": None,
        "a_payload": None,
        "a_name_updated": None,
        "b_ids": [],
        "b_integration_ids": [],
        "b_payloads": [],
        "b_names_updated": [],
    }


@pytest.fixture(scope="module")
def smoke_urls(base_server_url):
    base = base_server_url.rstrip("/")
    return {
        "put_url": f"{base}/InventoryStatus/CreateOrUpdate",
        "put_many_url": base,
        "get_url": f"{base}/InventoryStatus",
        "post_url": f"{base}/InventoryStatus",
    }


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(50)
@pytest.mark.test_name_ru("Smoke: PUT /InventoryStatus/CreateOrUpdate — создание одного объекта")
@testit.externalId("smoke_inventorystatus_01_create_one")
@testit.displayName("Smoke: PUT /InventoryStatus/CreateOrUpdate — создание одного объекта")
@testit.title("Smoke: PUT /InventoryStatus/CreateOrUpdate — создание одного объекта")
@testit.description(get_smoke_tc_description("inventorystatus", 1))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatus")
@testit.labels("api", "smoke", "inventorystatus")
def test_01_create_one(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 1. PUT /InventoryStatus/CreateOrUpdate — создание одного объекта ===\n")
    payload = build_unique_inventorystatus_payload()
    response = run_smoke_request(lambda: _put_inventorystatus(smoke_urls['put_url'], payload=payload, auth=admin_auth))
    uid, iid = assert_create_one_response(response, payload)
    smoke_state["a_id"] = uid
    smoke_state["a_integration_id"] = iid
    smoke_state["a_payload"] = copy.deepcopy(payload)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(51)
@pytest.mark.test_name_ru("Smoke: PUT /InventoryStatus/CreateOrUpdate — обновление одного объекта")
@testit.externalId("smoke_inventorystatus_01b_update_one")
@testit.displayName("Smoke: PUT /InventoryStatus/CreateOrUpdate — обновление одного объекта")
@testit.title("Smoke: PUT /InventoryStatus/CreateOrUpdate — обновление одного объекта")
@testit.description(get_smoke_tc_description("inventorystatus", 2))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatus")
@testit.labels("api", "smoke", "inventorystatus")
def test_01b_update_one(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 1b. PUT /InventoryStatus/CreateOrUpdate — обновление одного объекта ===\n")
    payload = get_required_state(smoke_state, "a_payload", "a_payload не сохранён (запустите test_01_create_one)")
    payload_updated, name_updated = build_updated_payload_smoke(payload)
    response = run_smoke_request(lambda: _put_inventorystatus(smoke_urls['put_url'], payload=payload_updated, auth=admin_auth))
    assert_update_one_response(response)
    smoke_state["a_name_updated"] = name_updated


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(52)
@pytest.mark.test_name_ru("Smoke: PUT /InventoryStatus/CreateOrUpdateMany — создание двух объектов")
@testit.externalId("smoke_inventorystatus_02_create_many")
@testit.displayName("Smoke: PUT /InventoryStatus/CreateOrUpdateMany — создание двух объектов")
@testit.title("Smoke: PUT /InventoryStatus/CreateOrUpdateMany — создание двух объектов")
@testit.description(get_smoke_tc_description("inventorystatus", 3))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatus")
@testit.labels("api", "smoke", "inventorystatus")
def test_02_create_many(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 2. PUT /InventoryStatus/CreateOrUpdateMany — создание двух объектов ===\n")
    payloads = [build_unique_inventorystatus_payload() for _ in range(2)]
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls['put_many_url'], payloads, admin_auth))
    ids, integration_ids = assert_create_many_response(response, payloads)
    smoke_state["b_ids"] = ids
    smoke_state["b_integration_ids"] = integration_ids
    smoke_state["b_payloads"] = copy.deepcopy(payloads)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(53)
@pytest.mark.test_name_ru("Smoke: PUT /InventoryStatus/CreateOrUpdateMany — обновление двух объектов")
@testit.externalId("smoke_inventorystatus_02b_update_many")
@testit.displayName("Smoke: PUT /InventoryStatus/CreateOrUpdateMany — обновление двух объектов")
@testit.title("Smoke: PUT /InventoryStatus/CreateOrUpdateMany — обновление двух объектов")
@testit.description(get_smoke_tc_description("inventorystatus", 4))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatus")
@testit.labels("api", "smoke", "inventorystatus")
def test_02b_update_many(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 2b. PUT /InventoryStatus/CreateOrUpdateMany — обновление двух объектов ===\n")
    payloads = get_required_state_list(smoke_state, "b_payloads", 2, "b_payloads не заполнены (запустите test_02_create_many)")
    payloads_updated, names_updated = build_updated_payloads_smoke(payloads)
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls['put_many_url'], payloads_updated, admin_auth))
    assert_update_many_response(response, count=2)
    smoke_state["b_names_updated"] = names_updated


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(54)
@pytest.mark.test_name_ru("Smoke: GET /InventoryStatus — в списке есть A, B1, B2 и поля после обновления")
@testit.externalId("smoke_inventorystatus_03_get_list")
@testit.displayName("Smoke: GET /InventoryStatus — в списке есть A, B1, B2 и поля после обновления")
@testit.title("Smoke: GET /InventoryStatus — в списке есть A, B1, B2 и поля после обновления")
@testit.description(get_smoke_tc_description("inventorystatus", 5))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatus")
@testit.labels("api", "smoke", "inventorystatus")
def test_03_get_list(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 3. GET /InventoryStatus — список содержит созданные объекты и значения после обновления ===\n")
    try:
        items = _get_list(smoke_urls["get_url"], admin_auth, page_size=5000)
    except AssertionError as e:
        pytest.fail(f"GET /InventoryStatus не вернул 200 или items: {e}")
    id_a = get_required_state(smoke_state, "a_integration_id", "a_integration_id не в state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "b_integration_ids", 2, "b_integration_ids не заполнены")
    name_a_expected = smoke_state.get("a_name_updated")
    names_b_expected = smoke_state.get("b_names_updated") or []
    assert_list_contains_and_names(items, id_a, ids_b, _find_by, name_a_expected=name_a_expected, names_b_expected=names_b_expected)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(55)
@pytest.mark.test_name_ru("Smoke: PATCH /InventoryStatus/Delete — удаление объекта A")
@testit.externalId("smoke_inventorystatus_04_delete_one")
@testit.displayName("Smoke: PATCH /InventoryStatus/Delete — удаление объекта A")
@testit.title("Smoke: PATCH /InventoryStatus/Delete — удаление объекта A")
@testit.description(get_smoke_tc_description("inventorystatus", 6))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatus")
@testit.labels("api", "smoke", "inventorystatus")
def test_04_delete_one(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 4. PATCH /InventoryStatus/Delete — удаление объекта A ===\n")
    a_integration_id = get_required_state(
        smoke_state,
        "a_integration_id",
        "a_integration_id не сохранён в smoke_state (запустите test_01_create_one)",
    )
    response = run_smoke_request(
        lambda: _patch_delete(
            smoke_urls["put_many_url"], {"integrationId": a_integration_id}, admin_auth
        )
    )
    assert_delete_one_response(response)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(56)
@pytest.mark.test_name_ru("Smoke: POST /InventoryStatus — фильтр по B1 и B2")
@testit.externalId("smoke_inventorystatus_05_post_filter")
@testit.displayName("Smoke: POST /InventoryStatus — фильтр по B1 и B2")
@testit.title("Smoke: POST /InventoryStatus — фильтр по B1 и B2")
@testit.description(get_smoke_tc_description("inventorystatus", 7))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatus")
@testit.labels("api", "smoke", "inventorystatus")
def test_05_post_filter(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 5. POST /InventoryStatus — фильтр по B1 и B2 ===\n")
    integration_ids_b = get_required_state_list(smoke_state, "b_integration_ids", 2, "b_integration_ids не заполнены")
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids_b, "noCount": False}
    response = _post_filter(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_count(response, 2)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(57)
@pytest.mark.test_name_ru("Smoke: PATCH /InventoryStatus/DeleteMany — удаление B1 и B2")
@testit.externalId("smoke_inventorystatus_06_delete_many")
@testit.displayName("Smoke: PATCH /InventoryStatus/DeleteMany — удаление B1 и B2")
@testit.title("Smoke: PATCH /InventoryStatus/DeleteMany — удаление B1 и B2")
@testit.description(get_smoke_tc_description("inventorystatus", 8))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatus")
@testit.labels("api", "smoke", "inventorystatus")
def test_06_delete_many(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 6. PATCH /InventoryStatus/DeleteMany — удаление B1 и B2 ===\n")
    ids_b_integration = get_required_state_list(
        smoke_state,
        "b_integration_ids",
        2,
        "b_integration_ids не заполнены",
    )
    body = [{"integrationId": ids_b_integration[0]}, {"integrationId": ids_b_integration[1]}]
    response = _patch_delete_many(smoke_urls["put_many_url"], body, admin_auth)
    assert_delete_many_response(response, expected_deleted=2)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(58)
@pytest.mark.test_name_ru("Smoke: POST /InventoryStatus — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.externalId("smoke_inventorystatus_07_post_clean")
@testit.displayName("Smoke: POST /InventoryStatus — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.title("Smoke: POST /InventoryStatus — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.description(get_smoke_tc_description("inventorystatus", 9))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatus")
@testit.labels("api", "smoke", "inventorystatus")
def test_07_post_clean(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 7. POST /InventoryStatus — финальная проверка чистоты (фильтр по A, B1, B2) ===\n")
    id_a = get_required_state(smoke_state, "a_integration_id", "a_integration_id не сохранён в smoke_state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "b_integration_ids", 2, "b_integration_ids не заполнены (запустите предыдущие шаги)")
    integration_ids = [id_a] + list(ids_b)
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids, "noCount": False}
    response = _post_filter(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_items_empty(response)


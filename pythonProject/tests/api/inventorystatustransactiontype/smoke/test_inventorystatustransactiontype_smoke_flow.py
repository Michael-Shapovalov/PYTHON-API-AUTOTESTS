"""
Smoke-тесты для API InventoryStatusTransactionType: последовательный сценарий (создание → обновление одного → пачка → обновление пачки → GET с проверкой наличия → Delete → POST фильтр → DeleteMany → финальный POST-поиск чистоты).
Состояние между тестами передаётся через fixture smoke_state (scope=module). Порядок выполнения — pytest-order.
Для связей используются фиксированные существующие id из БД: InventoryStatusId и InventoryTransactionTypeId (в фикстурах ниже).
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
from tests.api.inventorystatustransactiontype.steps import (
    _find_by,
    _get_list,
    _patch_delete,
    _patch_delete_many,
    _post_filter,
    _put_many,
    _put_one,
    build_unique_inventorystatustransactiontype_payload,
    build_updated_payload_smoke,
    build_updated_payloads_smoke,
)


@pytest.fixture(scope="module")
def smoke_base_inventorystatus_ref():
    """Фиксированный InventoryStatus из БД (id заменить на актуальный при необходимости)."""
    return {"id": 3}

@pytest.fixture(scope="module")
def smoke_base_inventorystatus_ref_2():
    """Второй фиксированный InventoryStatus из БД (для CreateMany нужен другой status id)."""
    return {"id": 2}

@pytest.fixture(scope="module")
def smoke_base_inventorystatus_ref_3():
    """Третий фиксированный InventoryStatus из БД (для CreateMany — статус 1)."""
    return {"id": 1}


@pytest.fixture(scope="module")
def smoke_base_inventorytransactiontype_ref():
    """Фиксированный InventoryTransactionType из БД (id заменить на актуальный при необходимости)."""
    return {"id": 1}

@pytest.fixture(scope="module")
def smoke_base_inventorytransactiontype_ref_2():
    """Второй фиксированный InventoryTransactionType из БД (для CreateMany нужен другой id из-за уникальности пары)."""
    return {"id": 5}

@pytest.fixture(scope="module")
def smoke_base_inventorytransactiontype_ref_3():
    """Третий фиксированный InventoryTransactionType из БД (для CreateMany — тип 4)."""
    return {"id": 4}


@pytest.fixture(scope="module")
def smoke_state():
    return {
        "a_id": None,
        "a_integration_id": None,
        "a_payload": None,
        "b_ids": [],
        "b_integration_ids": [],
        "b_payloads": [],
    }


@pytest.fixture(scope="module")
def smoke_urls(base_server_url):
    base = base_server_url.rstrip("/")
    return {
        "put_url": f"{base}/InventoryStatusTransactionType/CreateOrUpdate",
        "put_many_url": base,
        "get_url": f"{base}/InventoryStatusTransactionType",
        "post_url": f"{base}/InventoryStatusTransactionType",
    }


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(60)
@pytest.mark.test_name_ru("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdate — создание одного объекта")
@testit.externalId("smoke_inventorystatustransactiontype_01_create_one")
@testit.displayName("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdate — создание одного объекта")
@testit.title("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdate — создание одного объекта")
@testit.description(get_smoke_tc_description("inventorystatustransactiontype", 1))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatusTransactionType")
@testit.labels("api", "smoke", "inventorystatustransactiontype")
def test_01_create_one(smoke_state, smoke_urls, smoke_base_inventorystatus_ref, smoke_base_inventorytransactiontype_ref, admin_auth):
    print("\n  === Smoke: 1. PUT /InventoryStatusTransactionType/CreateOrUpdate — создание одного объекта ===\n")
    payload = build_unique_inventorystatustransactiontype_payload(smoke_base_inventorystatus_ref, smoke_base_inventorytransactiontype_ref)
    response = run_smoke_request(lambda: _put_one(smoke_urls["put_url"], payload=payload, auth=admin_auth))
    uid, iid = assert_create_one_response(response, payload)
    smoke_state["a_id"] = uid
    smoke_state["a_integration_id"] = iid
    smoke_state["a_payload"] = copy.deepcopy(payload)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(61)
@pytest.mark.test_name_ru("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdate — обновление одного объекта")
@testit.externalId("smoke_inventorystatustransactiontype_01b_update_one")
@testit.displayName("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdate — обновление одного объекта")
@testit.title("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdate — обновление одного объекта")
@testit.description(get_smoke_tc_description("inventorystatustransactiontype", 2))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatusTransactionType")
@testit.labels("api", "smoke", "inventorystatustransactiontype")
def test_01b_update_one(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 1b. PUT /InventoryStatusTransactionType/CreateOrUpdate — обновление одного объекта ===\n")
    payload = get_required_state(smoke_state, "a_payload", "a_payload не сохранён (запустите test_01_create_one)")
    payload_updated, _ = build_updated_payload_smoke(payload)
    response = run_smoke_request(lambda: _put_one(smoke_urls["put_url"], payload=payload_updated, auth=admin_auth))
    assert_update_one_response(response)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(62)
@pytest.mark.test_name_ru("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdateMany — создание двух объектов")
@testit.externalId("smoke_inventorystatustransactiontype_02_create_many")
@testit.displayName("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdateMany — создание двух объектов")
@testit.title("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdateMany — создание двух объектов")
@testit.description(get_smoke_tc_description("inventorystatustransactiontype", 3))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatusTransactionType")
@testit.labels("api", "smoke", "inventorystatustransactiontype")
def test_02_create_many(
    smoke_state,
    smoke_urls,
    smoke_base_inventorystatus_ref,
    smoke_base_inventorystatus_ref_2,
    smoke_base_inventorystatus_ref_3,
    smoke_base_inventorytransactiontype_ref,
    admin_auth,
):
    print("\n  === Smoke: 2. PUT /InventoryStatusTransactionType/CreateOrUpdateMany — создание двух объектов ===\n")
    # Без дополнительных запросов: фиксированные пары для CreateOrUpdateMany.
    # B1: (InventoryStatusId=2, InventoryTransactionTypeId=38)
    # B2: (InventoryStatusId=1, InventoryTransactionTypeId=39)
    payloads = [
        build_unique_inventorystatustransactiontype_payload(
            smoke_base_inventorystatus_ref_2,
            {"id": 38},
        ),
        build_unique_inventorystatustransactiontype_payload(
            smoke_base_inventorystatus_ref_3,
            {"id": 39},
        ),
    ]
    response = run_smoke_request(lambda: _put_many(smoke_urls["put_many_url"], payloads, admin_auth))
    ids, integration_ids = assert_create_many_response(response, payloads)
    smoke_state["b_ids"] = ids
    smoke_state["b_integration_ids"] = integration_ids
    smoke_state["b_payloads"] = copy.deepcopy(payloads)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(63)
@pytest.mark.test_name_ru("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdateMany — обновление двух объектов")
@testit.externalId("smoke_inventorystatustransactiontype_02b_update_many")
@testit.displayName("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdateMany — обновление двух объектов")
@testit.title("Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdateMany — обновление двух объектов")
@testit.description(get_smoke_tc_description("inventorystatustransactiontype", 4))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatusTransactionType")
@testit.labels("api", "smoke", "inventorystatustransactiontype")
def test_02b_update_many(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 2b. PUT /InventoryStatusTransactionType/CreateOrUpdateMany — обновление двух объектов ===\n")
    payloads = get_required_state_list(smoke_state, "b_payloads", 2, "b_payloads не заполнены (запустите test_02_create_many)")
    payloads_updated, _ = build_updated_payloads_smoke(payloads)
    response = run_smoke_request(lambda: _put_many(smoke_urls["put_many_url"], payloads_updated, admin_auth))
    assert_update_many_response(response, count=2)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(64)
@pytest.mark.test_name_ru("Smoke: GET /InventoryStatusTransactionType — в списке есть A, B1, B2")
@testit.externalId("smoke_inventorystatustransactiontype_03_get_list")
@testit.displayName("Smoke: GET /InventoryStatusTransactionType — в списке есть A, B1, B2")
@testit.title("Smoke: GET /InventoryStatusTransactionType — в списке есть A, B1, B2")
@testit.description(get_smoke_tc_description("inventorystatustransactiontype", 5))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatusTransactionType")
@testit.labels("api", "smoke", "inventorystatustransactiontype")
def test_03_get_list(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 3. GET /InventoryStatusTransactionType — список содержит созданные объекты ===\n")
    try:
        items = _get_list(smoke_urls["get_url"], admin_auth, page_size=5000)
    except AssertionError as e:
        pytest.fail(f"GET /InventoryStatusTransactionType не вернул 200 или items: {e}")
    id_a = get_required_state(smoke_state, "a_integration_id", "a_integration_id не в state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "b_integration_ids", 2, "b_integration_ids не заполнены")
    # Для этой сущности name может отсутствовать; assert_list_contains_and_names проверит только наличие, если name_* не задан.
    assert_list_contains_and_names(items, id_a, ids_b, _find_by, name_a_expected=None, names_b_expected=None)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(65)
@pytest.mark.test_name_ru("Smoke: PATCH /InventoryStatusTransactionType/Delete — удаление объекта A")
@testit.externalId("smoke_inventorystatustransactiontype_04_delete_one")
@testit.displayName("Smoke: PATCH /InventoryStatusTransactionType/Delete — удаление объекта A")
@testit.title("Smoke: PATCH /InventoryStatusTransactionType/Delete — удаление объекта A")
@testit.description(get_smoke_tc_description("inventorystatustransactiontype", 6))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatusTransactionType")
@testit.labels("api", "smoke", "inventorystatustransactiontype")
def test_04_delete_one(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 4. PATCH /InventoryStatusTransactionType/Delete — удаление объекта A ===\n")
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
@pytest.mark.order(66)
@pytest.mark.test_name_ru("Smoke: POST /InventoryStatusTransactionType — фильтр по B1 и B2")
@testit.externalId("smoke_inventorystatustransactiontype_05_post_filter")
@testit.displayName("Smoke: POST /InventoryStatusTransactionType — фильтр по B1 и B2")
@testit.title("Smoke: POST /InventoryStatusTransactionType — фильтр по B1 и B2")
@testit.description(get_smoke_tc_description("inventorystatustransactiontype", 7))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatusTransactionType")
@testit.labels("api", "smoke", "inventorystatustransactiontype")
def test_05_post_filter(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 5. POST /InventoryStatusTransactionType — фильтр по B1 и B2 ===\n")
    integration_ids_b = get_required_state_list(smoke_state, "b_integration_ids", 2, "b_integration_ids не заполнены")
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids_b, "noCount": False}
    response = _post_filter(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_count(response, 2)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(67)
@pytest.mark.test_name_ru("Smoke: PATCH /InventoryStatusTransactionType/DeleteMany — удаление B1 и B2")
@testit.externalId("smoke_inventorystatustransactiontype_06_delete_many")
@testit.displayName("Smoke: PATCH /InventoryStatusTransactionType/DeleteMany — удаление B1 и B2")
@testit.title("Smoke: PATCH /InventoryStatusTransactionType/DeleteMany — удаление B1 и B2")
@testit.description(get_smoke_tc_description("inventorystatustransactiontype", 8))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatusTransactionType")
@testit.labels("api", "smoke", "inventorystatustransactiontype")
def test_06_delete_many(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 6. PATCH /InventoryStatusTransactionType/DeleteMany — удаление B1 и B2 ===\n")
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
@pytest.mark.order(68)
@pytest.mark.test_name_ru("Smoke: POST /InventoryStatusTransactionType — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.externalId("smoke_inventorystatustransactiontype_07_post_clean")
@testit.displayName("Smoke: POST /InventoryStatusTransactionType — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.title("Smoke: POST /InventoryStatusTransactionType — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.description(get_smoke_tc_description("inventorystatustransactiontype", 9))
@testit.nameSpace("API/Smoke")
@testit.className("InventoryStatusTransactionType")
@testit.labels("api", "smoke", "inventorystatustransactiontype")
def test_07_post_clean(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 7. POST /InventoryStatusTransactionType — финальная проверка чистоты (фильтр по A, B1, B2) ===\n")
    id_a = get_required_state(smoke_state, "a_integration_id", "a_integration_id не сохранён в smoke_state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "b_integration_ids", 2, "b_integration_ids не заполнены (запустите предыдущие шаги)")
    integration_ids = [id_a] + list(ids_b)
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids, "noCount": False}
    response = _post_filter(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_items_empty(response)


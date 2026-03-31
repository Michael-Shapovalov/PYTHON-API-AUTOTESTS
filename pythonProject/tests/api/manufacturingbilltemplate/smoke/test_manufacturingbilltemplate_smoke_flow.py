"""
Smoke-тесты для API ManufacturingBillTemplate:
последовательный сценарий (создание → обновление одного → пачка → обновление пачки → GET с проверкой полей → Delete → POST фильтр → DeleteMany → финальная проверка чистоты).
Состояние между тестами передаётся через fixture smoke_state (scope=module). Порядок выполнения — pytest-order.
"""

import copy

import pytest
import testit

from tests.utils.testit_smoke_docs import get_smoke_tc_description

from tests.api.manufacturingbilltemplate.steps import (
    _find_mbt_by,
    _get_mbt_list,
    _patch_delete,
    _patch_delete_many,
    _post_mbt,
    _put_create_or_update_many,
    _put_mbt,
    build_updated_payload_smoke,
    build_updated_payloads_smoke,
    build_unique_manufacturingbilltemplate_payload,
)
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


# --- Фикстуры ---


@pytest.fixture(scope="module")
def smoke_state():
    """Общее состояние smoke-сценария ManufacturingBillTemplate."""
    return {
        "mbt_a_id": None,
        "mbt_a_integration_id": None,
        "mbt_a_payload": None,
        "mbt_a_name_updated": None,
        "mbt_b_ids": [],
        "mbt_b_integration_ids": [],
        "mbt_b_payloads": [],
        "mbt_b_names_updated": [],
    }


@pytest.fixture(scope="module")
def smoke_urls(base_server_url):
    """URL для smoke-тестов ManufacturingBillTemplate."""
    base = base_server_url.rstrip("/")
    return {
        "put_url": f"{base}/ManufacturingBillTemplate/CreateOrUpdate",
        "put_many_url": base,
        "get_url": f"{base}/ManufacturingBillTemplate",
        "post_url": f"{base}/ManufacturingBillTemplate",
    }


# --- Тесты ---


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(70)
@pytest.mark.test_name_ru("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdate — создание одного объекта")
@testit.externalId("smoke_mbt_01_create_one")
@testit.displayName("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdate — создание одного объекта")
@testit.title("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdate — создание одного объекта")
@testit.description(get_smoke_tc_description("manufacturingbilltemplate", 1))
@testit.nameSpace("API/Smoke")
@testit.className("ManufacturingBillTemplate")
@testit.labels("api", "smoke", "manufacturingbilltemplate")
def test_01_create_one(smoke_state, smoke_urls, admin_auth):
    """PUT /ManufacturingBillTemplate/CreateOrUpdate с минимально валидным payload. 200, added==1, errors==0."""
    print("\n  === Smoke: 1. PUT /ManufacturingBillTemplate/CreateOrUpdate — создание одного объекта ===\n")
    payload = build_unique_manufacturingbilltemplate_payload()
    response = run_smoke_request(lambda: _put_mbt(smoke_urls["put_url"], payload=payload, auth=admin_auth))
    uid, iid = assert_create_one_response(response, payload)
    smoke_state["mbt_a_id"] = uid
    smoke_state["mbt_a_integration_id"] = iid
    smoke_state["mbt_a_payload"] = copy.deepcopy(payload)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(71)
@pytest.mark.test_name_ru("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdate — обновление одного объекта")
@testit.externalId("smoke_mbt_01b_update_one")
@testit.displayName("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdate — обновление одного объекта")
@testit.title("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdate — обновление одного объекта")
@testit.description(get_smoke_tc_description("manufacturingbilltemplate", 2))
@testit.nameSpace("API/Smoke")
@testit.className("ManufacturingBillTemplate")
@testit.labels("api", "smoke", "manufacturingbilltemplate")
def test_01b_update_one(smoke_state, smoke_urls, admin_auth):
    """PUT /ManufacturingBillTemplate/CreateOrUpdate — обновление объекта A (тот же integrationId), поле name изменено."""
    print("\n  === Smoke: 1b. PUT /ManufacturingBillTemplate/CreateOrUpdate — обновление одного объекта ===\n")
    payload = get_required_state(smoke_state, "mbt_a_payload", "mbt_a_payload не сохранён в smoke_state (запустите test_01_create_one)")
    payload_updated, name_updated = build_updated_payload_smoke(payload)
    response = run_smoke_request(lambda: _put_mbt(smoke_urls["put_url"], payload=payload_updated, auth=admin_auth))
    assert_update_one_response(response)
    smoke_state["mbt_a_name_updated"] = name_updated


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(72)
@pytest.mark.test_name_ru("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdateMany — создание двух объектов")
@testit.externalId("smoke_mbt_02_create_many")
@testit.displayName("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdateMany — создание двух объектов")
@testit.title("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdateMany — создание двух объектов")
@testit.description(get_smoke_tc_description("manufacturingbilltemplate", 3))
@testit.nameSpace("API/Smoke")
@testit.className("ManufacturingBillTemplate")
@testit.labels("api", "smoke", "manufacturingbilltemplate")
def test_02_create_many(smoke_state, smoke_urls, admin_auth):
    """PUT /ManufacturingBillTemplate/CreateOrUpdateMany — создание массива из двух объектов."""
    print("\n  === Smoke: 2. PUT /ManufacturingBillTemplate/CreateOrUpdateMany — создание двух объектов ===\n")
    payloads = [build_unique_manufacturingbilltemplate_payload() for _ in range(2)]
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads, admin_auth))
    ids, integration_ids = assert_create_many_response(response, payloads)
    smoke_state["mbt_b_ids"] = ids
    smoke_state["mbt_b_integration_ids"] = integration_ids
    smoke_state["mbt_b_payloads"] = copy.deepcopy(payloads)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(73)
@pytest.mark.test_name_ru("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdateMany — обновление двух объектов")
@testit.externalId("smoke_mbt_02b_update_many")
@testit.displayName("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdateMany — обновление двух объектов")
@testit.title("Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdateMany — обновление двух объектов")
@testit.description(get_smoke_tc_description("manufacturingbilltemplate", 4))
@testit.nameSpace("API/Smoke")
@testit.className("ManufacturingBillTemplate")
@testit.labels("api", "smoke", "manufacturingbilltemplate")
def test_02b_update_many(smoke_state, smoke_urls, admin_auth):
    """PUT /ManufacturingBillTemplate/CreateOrUpdateMany — обновление B1 и B2 (те же integrationId), поле name изменено."""
    print("\n  === Smoke: 2b. PUT /ManufacturingBillTemplate/CreateOrUpdateMany — обновление двух объектов ===\n")
    payloads = get_required_state_list(smoke_state, "mbt_b_payloads", 2, "mbt_b_payloads не заполнены (запустите test_02_create_many)")
    payloads_updated, names_updated = build_updated_payloads_smoke(payloads)
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads_updated, admin_auth))
    assert_update_many_response(response, count=2)
    smoke_state["mbt_b_names_updated"] = names_updated


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(74)
@pytest.mark.test_name_ru("Smoke: GET /ManufacturingBillTemplate — в списке есть A, B1, B2")
@testit.externalId("smoke_mbt_03_get_list")
@testit.displayName("Smoke: GET /ManufacturingBillTemplate — в списке есть A, B1, B2")
@testit.title("Smoke: GET /ManufacturingBillTemplate — в списке есть A, B1, B2")
@testit.description(get_smoke_tc_description("manufacturingbilltemplate", 5))
@testit.nameSpace("API/Smoke")
@testit.className("ManufacturingBillTemplate")
@testit.labels("api", "smoke", "manufacturingbilltemplate")
def test_03_get_list(smoke_state, smoke_urls, admin_auth):
    """GET /ManufacturingBillTemplate. items содержит A, B1, B2 и name совпадает с ожидаемым после обновления."""
    print("\n  === Smoke: 3. GET /ManufacturingBillTemplate — список содержит созданные объекты и значения после обновления ===\n")
    items = _get_mbt_list(smoke_urls["get_url"], admin_auth, page_size=5000)
    id_a = get_required_state(smoke_state, "mbt_a_integration_id", "mbt_a_integration_id не в state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "mbt_b_integration_ids", 2, "mbt_b_integration_ids не заполнены")
    name_a_expected = smoke_state.get("mbt_a_name_updated")
    names_b_expected = smoke_state.get("mbt_b_names_updated") or []
    assert_list_contains_and_names(
        items,
        id_a,
        ids_b,
        _find_mbt_by,
        name_a_expected=name_a_expected,
        names_b_expected=names_b_expected,
    )


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(75)
@pytest.mark.test_name_ru("Smoke: PATCH /ManufacturingBillTemplate/Delete — удаление объекта A")
@testit.externalId("smoke_mbt_04_delete_one")
@testit.displayName("Smoke: PATCH /ManufacturingBillTemplate/Delete — удаление объекта A")
@testit.title("Smoke: PATCH /ManufacturingBillTemplate/Delete — удаление объекта A")
@testit.description(get_smoke_tc_description("manufacturingbilltemplate", 6))
@testit.nameSpace("API/Smoke")
@testit.className("ManufacturingBillTemplate")
@testit.labels("api", "smoke", "manufacturingbilltemplate")
def test_04_delete_one(smoke_state, smoke_urls, admin_auth):
    """PATCH /ManufacturingBillTemplate/Delete по integrationId объекта A."""
    print("\n  === Smoke: 4. PATCH /ManufacturingBillTemplate/Delete — удаление объекта A ===\n")
    mbt_a_integration_id = get_required_state(
        smoke_state,
        "mbt_a_integration_id",
        "mbt_a_integration_id не сохранён в smoke_state (запустите test_01_create_one)",
    )
    response = run_smoke_request(
        lambda: _patch_delete(smoke_urls["put_many_url"], {"integrationId": mbt_a_integration_id}, admin_auth)
    )
    assert_delete_one_response(response)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(76)
@pytest.mark.test_name_ru("Smoke: POST /ManufacturingBillTemplate — фильтр по B1 и B2")
@testit.externalId("smoke_mbt_05_post_filter")
@testit.displayName("Smoke: POST /ManufacturingBillTemplate — фильтр по B1 и B2")
@testit.title("Smoke: POST /ManufacturingBillTemplate — фильтр по B1 и B2")
@testit.description(get_smoke_tc_description("manufacturingbilltemplate", 7))
@testit.nameSpace("API/Smoke")
@testit.className("ManufacturingBillTemplate")
@testit.labels("api", "smoke", "manufacturingbilltemplate")
def test_05_post_filter(smoke_state, smoke_urls, admin_auth):
    """POST /ManufacturingBillTemplate с фильтром по integrationIds B1 и B2."""
    print("\n  === Smoke: 5. POST /ManufacturingBillTemplate — фильтр по B1 и B2 ===\n")
    integration_ids_b = get_required_state_list(smoke_state, "mbt_b_integration_ids", 2, "mbt_b_integration_ids не заполнены")
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids_b, "noCount": False}
    response = _post_mbt(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_count(response, 2)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(77)
@pytest.mark.test_name_ru("Smoke: PATCH /ManufacturingBillTemplate/DeleteMany — удаление B1 и B2")
@testit.externalId("smoke_mbt_06_delete_many")
@testit.displayName("Smoke: PATCH /ManufacturingBillTemplate/DeleteMany — удаление B1 и B2")
@testit.title("Smoke: PATCH /ManufacturingBillTemplate/DeleteMany — удаление B1 и B2")
@testit.description(get_smoke_tc_description("manufacturingbilltemplate", 8))
@testit.nameSpace("API/Smoke")
@testit.className("ManufacturingBillTemplate")
@testit.labels("api", "smoke", "manufacturingbilltemplate")
def test_06_delete_many(smoke_state, smoke_urls, admin_auth):
    """PATCH /ManufacturingBillTemplate/DeleteMany по integrationId объектов B1 и B2."""
    print("\n  === Smoke: 6. PATCH /ManufacturingBillTemplate/DeleteMany — удаление B1 и B2 ===\n")
    ids_b_integration = get_required_state_list(smoke_state, "mbt_b_integration_ids", 2, "mbt_b_integration_ids не заполнены")
    body = [{"integrationId": ids_b_integration[0]}, {"integrationId": ids_b_integration[1]}]
    response = _patch_delete_many(smoke_urls["put_many_url"], body, admin_auth)
    assert_delete_many_response(response, expected_deleted=2)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(78)
@pytest.mark.test_name_ru("Smoke: POST /ManufacturingBillTemplate — финальная проверка чистоты")
@testit.externalId("smoke_mbt_07_post_clean")
@testit.displayName("Smoke: POST /ManufacturingBillTemplate — финальная проверка чистоты")
@testit.title("Smoke: POST /ManufacturingBillTemplate — финальная проверка чистоты")
@testit.description(get_smoke_tc_description("manufacturingbilltemplate", 9))
@testit.nameSpace("API/Smoke")
@testit.className("ManufacturingBillTemplate")
@testit.labels("api", "smoke", "manufacturingbilltemplate")
def test_07_post_clean(smoke_state, smoke_urls, admin_auth):
    """Финальный POST /ManufacturingBillTemplate. Фильтр по integrationIds A, B1, B2 и проверка, что items пустой."""
    print("\n  === Smoke: 7. POST /ManufacturingBillTemplate — финальная проверка чистоты (фильтр по A, B1, B2) ===\n")
    id_a = get_required_state(smoke_state, "mbt_a_integration_id", "mbt_a_integration_id не сохранён в smoke_state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "mbt_b_integration_ids", 2, "mbt_b_integration_ids не заполнены (запустите предыдущие шаги)")
    integration_ids = [id_a] + list(ids_b)
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids, "noCount": False}
    response = _post_mbt(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_items_empty(response)


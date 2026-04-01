"""
Smoke-тесты для API ProcessOperation:
последовательный сценарий (создание → обновление одного → пачка → обновление пачки → GET с проверкой полей → Delete → POST фильтр → DeleteMany → финальная проверка чистоты).
Состояние между тестами передаётся через fixture smoke_state (scope=module). Порядок выполнения — pytest-order.

Вложенные позиции (material/equipment/labour/tooling) в smoke не передаются (без доп. запросов на внешние зависимости).
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
from tests.api.processoperation.steps import (
    _find_processoperation_by,
    _get_processoperation_list,
    _patch_delete,
    _patch_delete_many,
    _post_processoperation,
    _put_create_or_update_many,
    _put_processoperation,
    build_updated_payload_smoke,
    build_updated_payloads_smoke,
    build_unique_processoperation_payload,
)


@pytest.fixture(scope="module")
def smoke_base_process_segment_ref():
    return {"id": 1}


@pytest.fixture(scope="module")
def smoke_base_shop_floor_ref():
    return {"id": 2}


@pytest.fixture(scope="module")
def smoke_base_shop_floor_area_ref():
    return {"id": 15}


@pytest.fixture(scope="module")
def smoke_state():
    return {
        "po_a_id": None,
        "po_a_integration_id": None,
        "po_a_payload": None,
        "po_a_name_updated": None,
        "po_b_ids": [],
        "po_b_integration_ids": [],
        "po_b_payloads": [],
        "po_b_names_updated": [],
    }


@pytest.fixture(scope="module")
def smoke_urls(base_server_url):
    base = base_server_url.rstrip("/")
    return {
        "put_url": f"{base}/ProcessOperation/CreateOrUpdate",
        "put_many_url": base,
        "get_url": f"{base}/ProcessOperation",
        "post_url": f"{base}/ProcessOperation",
    }


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(110)
@pytest.mark.test_name_ru("Smoke: PUT /ProcessOperation/CreateOrUpdate — создание одного объекта")
@testit.externalId("smoke_processoperation_01_create_one")
@testit.displayName("Smoke: PUT /ProcessOperation/CreateOrUpdate — создание одного объекта")
@testit.title("Smoke: PUT /ProcessOperation/CreateOrUpdate — создание одного объекта")
@testit.description(get_smoke_tc_description("processoperation", 1))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessOperation")
@testit.labels("api", "smoke", "processoperation")
def test_01_create_one(
    smoke_state,
    smoke_urls,
    smoke_base_process_segment_ref,
    smoke_base_shop_floor_ref,
    smoke_base_shop_floor_area_ref,
    admin_auth,
):
    print("\n  === Smoke: 1. PUT /ProcessOperation/CreateOrUpdate — создание одного объекта ===\n")
    payload = build_unique_processoperation_payload(
        smoke_base_process_segment_ref,
        smoke_base_shop_floor_ref,
        smoke_base_shop_floor_area_ref,
    )
    response = run_smoke_request(lambda: _put_processoperation(smoke_urls["put_url"], payload=payload, auth=admin_auth))
    uid, iid = assert_create_one_response(response, payload)
    smoke_state["po_a_id"] = uid
    smoke_state["po_a_integration_id"] = iid
    smoke_state["po_a_payload"] = copy.deepcopy(payload)


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(111)
@pytest.mark.test_name_ru("Smoke: PUT /ProcessOperation/CreateOrUpdate — обновление одного объекта")
@testit.externalId("smoke_processoperation_01b_update_one")
@testit.displayName("Smoke: PUT /ProcessOperation/CreateOrUpdate — обновление одного объекта")
@testit.title("Smoke: PUT /ProcessOperation/CreateOrUpdate — обновление одного объекта")
@testit.description(get_smoke_tc_description("processoperation", 2))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessOperation")
@testit.labels("api", "smoke", "processoperation")
def test_01b_update_one(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 1b. PUT /ProcessOperation/CreateOrUpdate — обновление одного объекта ===\n")
    payload = get_required_state(smoke_state, "po_a_payload", "po_a_payload не сохранён (запустите test_01_create_one)")
    payload_updated, name_updated = build_updated_payload_smoke(payload)
    response = run_smoke_request(lambda: _put_processoperation(smoke_urls["put_url"], payload=payload_updated, auth=admin_auth))
    assert_update_one_response(response)
    smoke_state["po_a_name_updated"] = name_updated


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(112)
@pytest.mark.test_name_ru("Smoke: PUT /ProcessOperation/CreateOrUpdateMany — создание двух объектов")
@testit.externalId("smoke_processoperation_02_create_many")
@testit.displayName("Smoke: PUT /ProcessOperation/CreateOrUpdateMany — создание двух объектов")
@testit.title("Smoke: PUT /ProcessOperation/CreateOrUpdateMany — создание двух объектов")
@testit.description(get_smoke_tc_description("processoperation", 3))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessOperation")
@testit.labels("api", "smoke", "processoperation")
def test_02_create_many(
    smoke_state,
    smoke_urls,
    smoke_base_process_segment_ref,
    smoke_base_shop_floor_ref,
    smoke_base_shop_floor_area_ref,
    admin_auth,
):
    print("\n  === Smoke: 2. PUT /ProcessOperation/CreateOrUpdateMany — создание двух объектов ===\n")
    payloads = [
        build_unique_processoperation_payload(
            smoke_base_process_segment_ref,
            smoke_base_shop_floor_ref,
            smoke_base_shop_floor_area_ref,
        )
        for _ in range(2)
    ]
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads, auth=admin_auth))
    ids, integration_ids = assert_create_many_response(response, payloads)
    smoke_state["po_b_ids"] = ids
    smoke_state["po_b_integration_ids"] = integration_ids
    smoke_state["po_b_payloads"] = copy.deepcopy(payloads)


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(113)
@pytest.mark.test_name_ru("Smoke: PUT /ProcessOperation/CreateOrUpdateMany — обновление двух объектов")
@testit.externalId("smoke_processoperation_02b_update_many")
@testit.displayName("Smoke: PUT /ProcessOperation/CreateOrUpdateMany — обновление двух объектов")
@testit.title("Smoke: PUT /ProcessOperation/CreateOrUpdateMany — обновление двух объектов")
@testit.description(get_smoke_tc_description("processoperation", 4))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessOperation")
@testit.labels("api", "smoke", "processoperation")
def test_02b_update_many(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 2b. PUT /ProcessOperation/CreateOrUpdateMany — обновление двух объектов ===\n")
    payloads = get_required_state_list(smoke_state, "po_b_payloads", 2, "po_b_payloads не заполнены (запустите test_02_create_many)")
    payloads_updated, names_updated = build_updated_payloads_smoke(payloads)
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads_updated, auth=admin_auth))
    assert_update_many_response(response, count=2)
    smoke_state["po_b_names_updated"] = names_updated


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(114)
@pytest.mark.test_name_ru("Smoke: GET /ProcessOperation — в списке есть A, B1, B2 и поля после обновления")
@testit.externalId("smoke_processoperation_03_get_list")
@testit.displayName("Smoke: GET /ProcessOperation — в списке есть A, B1, B2 и поля после обновления")
@testit.title("Smoke: GET /ProcessOperation — в списке есть A, B1, B2 и поля после обновления")
@testit.description(get_smoke_tc_description("processoperation", 5))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessOperation")
@testit.labels("api", "smoke", "processoperation")
def test_03_get_list(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 3. GET /ProcessOperation — список содержит созданные объекты и значения после обновления ===\n")
    items = _get_processoperation_list(smoke_urls["get_url"], admin_auth, page_size=5000)
    id_a = get_required_state(smoke_state, "po_a_integration_id", "po_a_integration_id не в state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "po_b_integration_ids", 2, "po_b_integration_ids не заполнены")
    name_a_expected = smoke_state.get("po_a_name_updated")
    names_b_expected = smoke_state.get("po_b_names_updated") or []
    assert_list_contains_and_names(
        items,
        id_a,
        ids_b,
        _find_processoperation_by,
        name_a_expected=name_a_expected,
        names_b_expected=names_b_expected,
        field_name="name",
    )


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(115)
@pytest.mark.test_name_ru("Smoke: PATCH /ProcessOperation/Delete — удаление объекта A")
@testit.externalId("smoke_processoperation_04_delete_one")
@testit.displayName("Smoke: PATCH /ProcessOperation/Delete — удаление объекта A")
@testit.title("Smoke: PATCH /ProcessOperation/Delete — удаление объекта A")
@testit.description(get_smoke_tc_description("processoperation", 6))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessOperation")
@testit.labels("api", "smoke", "processoperation")
def test_04_delete_one(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 4. PATCH /ProcessOperation/Delete — удаление объекта A ===\n")
    po_a_integration_id = get_required_state(smoke_state, "po_a_integration_id", "po_a_integration_id не сохранён (запустите test_01_create_one)")
    response = run_smoke_request(lambda: _patch_delete(smoke_urls["put_many_url"], {"integrationId": po_a_integration_id}, auth=admin_auth))
    assert_delete_one_response(response)


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(116)
@pytest.mark.test_name_ru("Smoke: POST /ProcessOperation — фильтр по B1 и B2")
@testit.externalId("smoke_processoperation_05_post_filter")
@testit.displayName("Smoke: POST /ProcessOperation — фильтр по B1 и B2")
@testit.title("Smoke: POST /ProcessOperation — фильтр по B1 и B2")
@testit.description(get_smoke_tc_description("processoperation", 7))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessOperation")
@testit.labels("api", "smoke", "processoperation")
def test_05_post_filter(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 5. POST /ProcessOperation — фильтр по B1 и B2 ===\n")
    integration_ids_b = get_required_state_list(smoke_state, "po_b_integration_ids", 2, "po_b_integration_ids не заполнены")
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids_b, "noCount": False}
    response = _post_processoperation(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_count(response, 2)


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(117)
@pytest.mark.test_name_ru("Smoke: PATCH /ProcessOperation/DeleteMany — удаление B1 и B2")
@testit.externalId("smoke_processoperation_06_delete_many")
@testit.displayName("Smoke: PATCH /ProcessOperation/DeleteMany — удаление B1 и B2")
@testit.title("Smoke: PATCH /ProcessOperation/DeleteMany — удаление B1 и B2")
@testit.description(get_smoke_tc_description("processoperation", 8))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessOperation")
@testit.labels("api", "smoke", "processoperation")
def test_06_delete_many(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 6. PATCH /ProcessOperation/DeleteMany — удаление B1 и B2 ===\n")
    ids_b_integration = get_required_state_list(smoke_state, "po_b_integration_ids", 2, "po_b_integration_ids не заполнены")
    body = [{"integrationId": ids_b_integration[0]}, {"integrationId": ids_b_integration[1]}]
    response = _patch_delete_many(smoke_urls["put_many_url"], body, auth=admin_auth)
    assert_delete_many_response(response, expected_deleted=2)


@pytest.mark.smoke
@pytest.mark.rt_heavy
@pytest.mark.order(118)
@pytest.mark.test_name_ru("Smoke: POST /ProcessOperation — финальная проверка чистоты")
@testit.externalId("smoke_processoperation_07_post_clean")
@testit.displayName("Smoke: POST /ProcessOperation — финальная проверка чистоты")
@testit.title("Smoke: POST /ProcessOperation — финальная проверка чистоты")
@testit.description(get_smoke_tc_description("processoperation", 9))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessOperation")
@testit.labels("api", "smoke", "processoperation")
def test_07_post_clean(smoke_state, smoke_urls, admin_auth):
    print("\n  === Smoke: 7. POST /ProcessOperation — финальная проверка чистоты (фильтр по A, B1, B2) ===\n")
    id_a = get_required_state(smoke_state, "po_a_integration_id", "po_a_integration_id не сохранён (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "po_b_integration_ids", 2, "po_b_integration_ids не заполнены (запустите предыдущие шаги)")
    integration_ids = [id_a] + list(ids_b)
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids, "noCount": False}
    response = _post_processoperation(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_items_empty(response)


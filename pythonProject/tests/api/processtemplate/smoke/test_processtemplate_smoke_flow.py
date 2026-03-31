"""
Smoke-тесты для API ProcessTemplate:
последовательный сценарий (создание → обновление одного → пачка → обновление пачки → GET с проверкой полей → Delete → POST фильтр → DeleteMany → финальная проверка чистоты).
Состояние между тестами передаётся через fixture smoke_state (scope=module). Порядок выполнения — pytest-order.
"""

import copy

import pytest
import testit

from tests.utils.testit_smoke_docs import get_smoke_tc_description

from tests.api.processtemplate.steps import (
    _find_pt_by,
    _get_pt_list,
    _patch_delete,
    _patch_delete_many,
    _post_pt,
    _put_create_or_update_many,
    _put_pt,
    build_updated_payload_smoke,
    build_updated_payloads_smoke,
    build_unique_processtemplate_payload,
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
def smoke_base_default_unit_ref():
    """ЕИ по умолчанию для ProcessTemplate: Unit id=2 (фиксированная ссылка)."""
    return {"id": 2}


@pytest.fixture(scope="module")
def smoke_state():
    """Общее состояние smoke-сценария ProcessTemplate."""
    return {
        "pt_a_id": None,
        "pt_a_integration_id": None,
        "pt_a_payload": None,
        "pt_a_name_updated": None,
        "pt_b_ids": [],
        "pt_b_integration_ids": [],
        "pt_b_payloads": [],
        "pt_b_names_updated": [],
    }


@pytest.fixture(scope="module")
def smoke_urls(base_server_url):
    """URL для smoke-тестов ProcessTemplate."""
    base = base_server_url.rstrip("/")
    return {
        "put_url": f"{base}/ProcessTemplate/CreateOrUpdate",
        "put_many_url": base,
        "get_url": f"{base}/ProcessTemplate",
        "post_url": f"{base}/ProcessTemplate",
    }


# --- Тесты ---


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(80)
@pytest.mark.test_name_ru("Smoke: PUT /ProcessTemplate/CreateOrUpdate — создание одного объекта")
@testit.externalId("smoke_pt_01_create_one")
@testit.displayName("Smoke: PUT /ProcessTemplate/CreateOrUpdate — создание одного объекта")
@testit.title("Smoke: PUT /ProcessTemplate/CreateOrUpdate — создание одного объекта")
@testit.description(get_smoke_tc_description("processtemplate", 1))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessTemplate")
@testit.labels("api", "smoke", "processtemplate")
def test_01_create_one(smoke_state, smoke_urls, smoke_base_default_unit_ref, admin_auth):
    """PUT /ProcessTemplate/CreateOrUpdate с минимально валидным payload."""
    print("\n  === Smoke: 1. PUT /ProcessTemplate/CreateOrUpdate — создание одного объекта ===\n")
    payload = build_unique_processtemplate_payload(smoke_base_default_unit_ref)
    response = run_smoke_request(lambda: _put_pt(smoke_urls["put_url"], payload=payload, auth=admin_auth))
    uid, iid = assert_create_one_response(response, payload)
    smoke_state["pt_a_id"] = uid
    smoke_state["pt_a_integration_id"] = iid
    smoke_state["pt_a_payload"] = copy.deepcopy(payload)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(81)
@pytest.mark.test_name_ru("Smoke: PUT /ProcessTemplate/CreateOrUpdate — обновление одного объекта")
@testit.externalId("smoke_pt_01b_update_one")
@testit.displayName("Smoke: PUT /ProcessTemplate/CreateOrUpdate — обновление одного объекта")
@testit.title("Smoke: PUT /ProcessTemplate/CreateOrUpdate — обновление одного объекта")
@testit.description(get_smoke_tc_description("processtemplate", 2))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessTemplate")
@testit.labels("api", "smoke", "processtemplate")
def test_01b_update_one(smoke_state, smoke_urls, admin_auth):
    """PUT /ProcessTemplate/CreateOrUpdate — обновление объекта A (тот же integrationId), поле name изменено."""
    print("\n  === Smoke: 1b. PUT /ProcessTemplate/CreateOrUpdate — обновление одного объекта ===\n")
    payload = get_required_state(smoke_state, "pt_a_payload", "pt_a_payload не сохранён в smoke_state (запустите test_01_create_one)")
    payload_updated, name_updated = build_updated_payload_smoke(payload)
    response = run_smoke_request(lambda: _put_pt(smoke_urls["put_url"], payload=payload_updated, auth=admin_auth))
    assert_update_one_response(response)
    smoke_state["pt_a_name_updated"] = name_updated


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(82)
@pytest.mark.test_name_ru("Smoke: PUT /ProcessTemplate/CreateOrUpdateMany — создание двух объектов")
@testit.externalId("smoke_pt_02_create_many")
@testit.displayName("Smoke: PUT /ProcessTemplate/CreateOrUpdateMany — создание двух объектов")
@testit.title("Smoke: PUT /ProcessTemplate/CreateOrUpdateMany — создание двух объектов")
@testit.description(get_smoke_tc_description("processtemplate", 3))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessTemplate")
@testit.labels("api", "smoke", "processtemplate")
def test_02_create_many(smoke_state, smoke_urls, smoke_base_default_unit_ref, admin_auth):
    """PUT /ProcessTemplate/CreateOrUpdateMany — создание массива из двух объектов."""
    print("\n  === Smoke: 2. PUT /ProcessTemplate/CreateOrUpdateMany — создание двух объектов ===\n")
    payloads = [build_unique_processtemplate_payload(smoke_base_default_unit_ref) for _ in range(2)]
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads, admin_auth))
    ids, integration_ids = assert_create_many_response(response, payloads)
    smoke_state["pt_b_ids"] = ids
    smoke_state["pt_b_integration_ids"] = integration_ids
    smoke_state["pt_b_payloads"] = copy.deepcopy(payloads)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(83)
@pytest.mark.test_name_ru("Smoke: PUT /ProcessTemplate/CreateOrUpdateMany — обновление двух объектов")
@testit.externalId("smoke_pt_02b_update_many")
@testit.displayName("Smoke: PUT /ProcessTemplate/CreateOrUpdateMany — обновление двух объектов")
@testit.title("Smoke: PUT /ProcessTemplate/CreateOrUpdateMany — обновление двух объектов")
@testit.description(get_smoke_tc_description("processtemplate", 4))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessTemplate")
@testit.labels("api", "smoke", "processtemplate")
def test_02b_update_many(smoke_state, smoke_urls, admin_auth):
    """PUT /ProcessTemplate/CreateOrUpdateMany — обновление B1 и B2 (те же integrationId), поле name изменено."""
    print("\n  === Smoke: 2b. PUT /ProcessTemplate/CreateOrUpdateMany — обновление двух объектов ===\n")
    payloads = get_required_state_list(smoke_state, "pt_b_payloads", 2, "pt_b_payloads не заполнены (запустите test_02_create_many)")
    payloads_updated, names_updated = build_updated_payloads_smoke(payloads)
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads_updated, admin_auth))
    assert_update_many_response(response, count=2)
    smoke_state["pt_b_names_updated"] = names_updated


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(84)
@pytest.mark.test_name_ru("Smoke: GET /ProcessTemplate — в списке есть A, B1, B2")
@testit.externalId("smoke_pt_03_get_list")
@testit.displayName("Smoke: GET /ProcessTemplate — в списке есть A, B1, B2")
@testit.title("Smoke: GET /ProcessTemplate — в списке есть A, B1, B2")
@testit.description(get_smoke_tc_description("processtemplate", 5))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessTemplate")
@testit.labels("api", "smoke", "processtemplate")
def test_03_get_list(smoke_state, smoke_urls, admin_auth):
    """GET /ProcessTemplate. items содержит A, B1, B2 и name совпадает с ожидаемым после обновления."""
    print("\n  === Smoke: 3. GET /ProcessTemplate — список содержит созданные объекты и значения после обновления ===\n")
    items = _get_pt_list(smoke_urls["get_url"], admin_auth, page_size=5000)
    id_a = get_required_state(smoke_state, "pt_a_integration_id", "pt_a_integration_id не в state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "pt_b_integration_ids", 2, "pt_b_integration_ids не заполнены")
    name_a_expected = smoke_state.get("pt_a_name_updated")
    names_b_expected = smoke_state.get("pt_b_names_updated") or []
    assert_list_contains_and_names(
        items,
        id_a,
        ids_b,
        _find_pt_by,
        name_a_expected=name_a_expected,
        names_b_expected=names_b_expected,
    )


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(85)
@pytest.mark.test_name_ru("Smoke: PATCH /ProcessTemplate/Delete — удаление объекта A")
@testit.externalId("smoke_pt_04_delete_one")
@testit.displayName("Smoke: PATCH /ProcessTemplate/Delete — удаление объекта A")
@testit.title("Smoke: PATCH /ProcessTemplate/Delete — удаление объекта A")
@testit.description(get_smoke_tc_description("processtemplate", 6))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessTemplate")
@testit.labels("api", "smoke", "processtemplate")
def test_04_delete_one(smoke_state, smoke_urls, admin_auth):
    """PATCH /ProcessTemplate/Delete по integrationId объекта A."""
    print("\n  === Smoke: 4. PATCH /ProcessTemplate/Delete — удаление объекта A ===\n")
    pt_a_integration_id = get_required_state(
        smoke_state,
        "pt_a_integration_id",
        "pt_a_integration_id не сохранён в smoke_state (запустите test_01_create_one)",
    )
    response = run_smoke_request(lambda: _patch_delete(smoke_urls["put_many_url"], {"integrationId": pt_a_integration_id}, admin_auth))
    assert_delete_one_response(response)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(86)
@pytest.mark.test_name_ru("Smoke: POST /ProcessTemplate — фильтр по B1 и B2")
@testit.externalId("smoke_pt_05_post_filter")
@testit.displayName("Smoke: POST /ProcessTemplate — фильтр по B1 и B2")
@testit.title("Smoke: POST /ProcessTemplate — фильтр по B1 и B2")
@testit.description(get_smoke_tc_description("processtemplate", 7))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessTemplate")
@testit.labels("api", "smoke", "processtemplate")
def test_05_post_filter(smoke_state, smoke_urls, admin_auth):
    """POST /ProcessTemplate с фильтром по integrationIds B1 и B2."""
    print("\n  === Smoke: 5. POST /ProcessTemplate — фильтр по B1 и B2 ===\n")
    integration_ids_b = get_required_state_list(smoke_state, "pt_b_integration_ids", 2, "pt_b_integration_ids не заполнены")
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids_b, "noCount": False}
    response = _post_pt(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_count(response, 2)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(87)
@pytest.mark.test_name_ru("Smoke: PATCH /ProcessTemplate/DeleteMany — удаление B1 и B2")
@testit.externalId("smoke_pt_06_delete_many")
@testit.displayName("Smoke: PATCH /ProcessTemplate/DeleteMany — удаление B1 и B2")
@testit.title("Smoke: PATCH /ProcessTemplate/DeleteMany — удаление B1 и B2")
@testit.description(get_smoke_tc_description("processtemplate", 8))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessTemplate")
@testit.labels("api", "smoke", "processtemplate")
def test_06_delete_many(smoke_state, smoke_urls, admin_auth):
    """PATCH /ProcessTemplate/DeleteMany по integrationId объектов B1 и B2."""
    print("\n  === Smoke: 6. PATCH /ProcessTemplate/DeleteMany — удаление B1 и B2 ===\n")
    ids_b_integration = get_required_state_list(smoke_state, "pt_b_integration_ids", 2, "pt_b_integration_ids не заполнены")
    body = [{"integrationId": ids_b_integration[0]}, {"integrationId": ids_b_integration[1]}]
    response = _patch_delete_many(smoke_urls["put_many_url"], body, admin_auth)
    assert_delete_many_response(response, expected_deleted=2)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(88)
@pytest.mark.test_name_ru("Smoke: POST /ProcessTemplate — финальная проверка чистоты")
@testit.externalId("smoke_pt_07_post_clean")
@testit.displayName("Smoke: POST /ProcessTemplate — финальная проверка чистоты")
@testit.title("Smoke: POST /ProcessTemplate — финальная проверка чистоты")
@testit.description(get_smoke_tc_description("processtemplate", 9))
@testit.nameSpace("API/Smoke")
@testit.className("ProcessTemplate")
@testit.labels("api", "smoke", "processtemplate")
def test_07_post_clean(smoke_state, smoke_urls, admin_auth):
    """Финальный POST /ProcessTemplate. Проверка, что items пустой."""
    print("\n  === Smoke: 7. POST /ProcessTemplate — финальная проверка чистоты (фильтр по A, B1, B2) ===\n")
    id_a = get_required_state(smoke_state, "pt_a_integration_id", "pt_a_integration_id не сохранён в smoke_state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "pt_b_integration_ids", 2, "pt_b_integration_ids не заполнены (запустите предыдущие шаги)")
    integration_ids = [id_a] + list(ids_b)
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids, "noCount": False}
    response = _post_pt(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_items_empty(response)


"""
Smoke-тесты для API Company: последовательный сценарий
(create one -> update one -> create many -> update many -> get -> delete one -> post filter -> delete many -> post clean).
"""
import copy

import pytest
import testit

from tests.api.company.steps import (
    _find_company_by,
    _get_company_list,
    _patch_delete,
    _patch_delete_many,
    _post_company,
    _put_company,
    _put_create_or_update_many,
    build_unique_company_payload,
    build_updated_payload_smoke,
    build_updated_payloads_smoke,
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
from tests.utils.testit_smoke_docs import get_smoke_tc_description


@pytest.fixture(scope="module")
def smoke_base_contractor_ref():
    return {"integrationId": "0900000061"}


@pytest.fixture(scope="module")
def smoke_state():
    return {
        "company_a_id": None,
        "company_a_integration_id": None,
        "company_a_payload": None,
        "company_a_name_updated": None,
        "company_b_ids": [],
        "company_b_integration_ids": [],
        "company_b_payloads": [],
        "company_b_names_updated": [],
    }


@pytest.fixture(scope="module")
def smoke_urls(base_server_url):
    base = base_server_url.rstrip("/")
    return {
        "put_url": f"{base}/Company/CreateOrUpdate",
        "put_many_url": base,
        "get_url": f"{base}/Company",
        "post_url": f"{base}/Company",
    }


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(140)
@pytest.mark.test_name_ru("Smoke: PUT /Company/CreateOrUpdate — создание одного объекта")
@testit.externalId("smoke_company_01_create_one")
@testit.displayName("Smoke: PUT /Company/CreateOrUpdate — создание одного объекта")
@testit.title("Smoke: PUT /Company/CreateOrUpdate — создание одного объекта")
@testit.description(get_smoke_tc_description("company", 1))
@testit.nameSpace("API/Smoke")
@testit.className("Company")
@testit.labels("api", "smoke", "company")
def test_01_create_one(smoke_state, smoke_urls, smoke_base_contractor_ref, admin_auth):
    payload = build_unique_company_payload(smoke_base_contractor_ref)
    response = run_smoke_request(lambda: _put_company(smoke_urls["put_url"], payload=payload, auth=admin_auth))
    uid, iid = assert_create_one_response(response, payload)
    smoke_state["company_a_id"] = uid
    smoke_state["company_a_integration_id"] = iid
    smoke_state["company_a_payload"] = copy.deepcopy(payload)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(141)
@pytest.mark.test_name_ru("Smoke: PUT /Company/CreateOrUpdate — обновление одного объекта")
@testit.externalId("smoke_company_01b_update_one")
@testit.displayName("Smoke: PUT /Company/CreateOrUpdate — обновление одного объекта")
@testit.title("Smoke: PUT /Company/CreateOrUpdate — обновление одного объекта")
@testit.description(get_smoke_tc_description("company", 2))
@testit.nameSpace("API/Smoke")
@testit.className("Company")
@testit.labels("api", "smoke", "company")
def test_01b_update_one(smoke_state, smoke_urls, admin_auth):
    payload = get_required_state(smoke_state, "company_a_payload", "company_a_payload не сохранён (запустите test_01_create_one)")
    payload_updated, name_updated = build_updated_payload_smoke(payload)
    response = run_smoke_request(lambda: _put_company(smoke_urls["put_url"], payload=payload_updated, auth=admin_auth))
    assert_update_one_response(response)
    smoke_state["company_a_name_updated"] = name_updated


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(142)
@pytest.mark.test_name_ru("Smoke: PUT /Company/CreateOrUpdateMany — создание двух объектов")
@testit.externalId("smoke_company_02_create_many")
@testit.displayName("Smoke: PUT /Company/CreateOrUpdateMany — создание двух объектов")
@testit.title("Smoke: PUT /Company/CreateOrUpdateMany — создание двух объектов")
@testit.description(get_smoke_tc_description("company", 3))
@testit.nameSpace("API/Smoke")
@testit.className("Company")
@testit.labels("api", "smoke", "company")
def test_02_create_many(smoke_state, smoke_urls, smoke_base_contractor_ref, admin_auth):
    payloads = [build_unique_company_payload(smoke_base_contractor_ref) for _ in range(2)]
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads, admin_auth))
    ids, integration_ids = assert_create_many_response(response, payloads)
    smoke_state["company_b_ids"] = ids
    smoke_state["company_b_integration_ids"] = integration_ids
    smoke_state["company_b_payloads"] = copy.deepcopy(payloads)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(143)
@pytest.mark.test_name_ru("Smoke: PUT /Company/CreateOrUpdateMany — обновление двух объектов")
@testit.externalId("smoke_company_02b_update_many")
@testit.displayName("Smoke: PUT /Company/CreateOrUpdateMany — обновление двух объектов")
@testit.title("Smoke: PUT /Company/CreateOrUpdateMany — обновление двух объектов")
@testit.description(get_smoke_tc_description("company", 4))
@testit.nameSpace("API/Smoke")
@testit.className("Company")
@testit.labels("api", "smoke", "company")
def test_02b_update_many(smoke_state, smoke_urls, admin_auth):
    payloads = get_required_state_list(
        smoke_state,
        "company_b_payloads",
        2,
        "company_b_payloads не заполнены (запустите test_02_create_many)",
    )
    payloads_updated, names_updated = build_updated_payloads_smoke(payloads)
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads_updated, admin_auth))
    assert_update_many_response(response, count=2)
    smoke_state["company_b_names_updated"] = names_updated


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(144)
@pytest.mark.test_name_ru("Smoke: GET /Company — в списке есть A, B1, B2")
@testit.externalId("smoke_company_03_get_list")
@testit.displayName("Smoke: GET /Company — в списке есть A, B1, B2")
@testit.title("Smoke: GET /Company — в списке есть A, B1, B2")
@testit.description(get_smoke_tc_description("company", 5))
@testit.nameSpace("API/Smoke")
@testit.className("Company")
@testit.labels("api", "smoke", "company")
def test_03_get_list(smoke_state, smoke_urls, admin_auth):
    items = _get_company_list(smoke_urls["get_url"], admin_auth, page_size=5000)
    id_a = get_required_state(smoke_state, "company_a_integration_id", "company_a_integration_id не в state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "company_b_integration_ids", 2, "company_b_integration_ids не заполнены")
    name_a_expected = smoke_state.get("company_a_name_updated")
    names_b_expected = smoke_state.get("company_b_names_updated") or []
    assert_list_contains_and_names(
        items,
        id_a,
        ids_b,
        _find_company_by,
        name_a_expected=name_a_expected,
        names_b_expected=names_b_expected,
    )


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(145)
@pytest.mark.test_name_ru("Smoke: PATCH /Company/Delete — удаление объекта A")
@testit.externalId("smoke_company_04_delete_one")
@testit.displayName("Smoke: PATCH /Company/Delete — удаление объекта A")
@testit.title("Smoke: PATCH /Company/Delete — удаление объекта A")
@testit.description(get_smoke_tc_description("company", 6))
@testit.nameSpace("API/Smoke")
@testit.className("Company")
@testit.labels("api", "smoke", "company")
def test_04_delete_one(smoke_state, smoke_urls, admin_auth):
    company_a_integration_id = get_required_state(
        smoke_state,
        "company_a_integration_id",
        "company_a_integration_id не сохранён в smoke_state (запустите test_01_create_one)",
    )
    response = run_smoke_request(
        lambda: _patch_delete(smoke_urls["put_many_url"], {"integrationId": company_a_integration_id}, admin_auth)
    )
    assert_delete_one_response(response)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(146)
@pytest.mark.test_name_ru("Smoke: POST /Company — фильтр по B1 и B2")
@testit.externalId("smoke_company_05_post_filter")
@testit.displayName("Smoke: POST /Company — фильтр по B1 и B2")
@testit.title("Smoke: POST /Company — фильтр по B1 и B2")
@testit.description(get_smoke_tc_description("company", 7))
@testit.nameSpace("API/Smoke")
@testit.className("Company")
@testit.labels("api", "smoke", "company")
def test_05_post_filter(smoke_state, smoke_urls, admin_auth):
    integration_ids_b = get_required_state_list(smoke_state, "company_b_integration_ids", 2, "company_b_integration_ids не заполнены")
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids_b, "noCount": False}
    response = _post_company(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_count(response, 2)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(147)
@pytest.mark.test_name_ru("Smoke: PATCH /Company/DeleteMany — удаление B1 и B2")
@testit.externalId("smoke_company_06_delete_many")
@testit.displayName("Smoke: PATCH /Company/DeleteMany — удаление B1 и B2")
@testit.title("Smoke: PATCH /Company/DeleteMany — удаление B1 и B2")
@testit.description(get_smoke_tc_description("company", 8))
@testit.nameSpace("API/Smoke")
@testit.className("Company")
@testit.labels("api", "smoke", "company")
def test_06_delete_many(smoke_state, smoke_urls, admin_auth):
    ids_b_integration = get_required_state_list(smoke_state, "company_b_integration_ids", 2, "company_b_integration_ids не заполнены")
    body = [{"integrationId": ids_b_integration[0]}, {"integrationId": ids_b_integration[1]}]
    response = _patch_delete_many(smoke_urls["put_many_url"], body, admin_auth)
    assert_delete_many_response(response, expected_deleted=2)


@pytest.mark.smoke
@pytest.mark.rt_medium
@pytest.mark.order(148)
@pytest.mark.test_name_ru("Smoke: POST /Company — финальная проверка чистоты")
@testit.externalId("smoke_company_07_post_clean")
@testit.displayName("Smoke: POST /Company — финальная проверка чистоты")
@testit.title("Smoke: POST /Company — финальная проверка чистоты")
@testit.description(get_smoke_tc_description("company", 9))
@testit.nameSpace("API/Smoke")
@testit.className("Company")
@testit.labels("api", "smoke", "company")
def test_07_post_clean(smoke_state, smoke_urls, admin_auth):
    id_a = get_required_state(
        smoke_state,
        "company_a_integration_id",
        "company_a_integration_id не сохранён в smoke_state (запустите предыдущие шаги)",
    )
    ids_b = get_required_state_list(
        smoke_state,
        "company_b_integration_ids",
        2,
        "company_b_integration_ids не заполнены (запустите предыдущие шаги)",
    )
    integration_ids = [id_a] + list(ids_b)
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids, "noCount": False}
    response = _post_company(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_items_empty(response)


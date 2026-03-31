"""
Smoke-тесты для API UnitGroup: последовательный сценарий (создание → обновление одного → пачка → обновление пачки → GET с проверкой полей → Delete → POST фильтр → DeleteMany → финальный POST-поиск чистоты).
Состояние между тестами передаётся через fixture smoke_state (scope=module). Порядок выполнения — pytest-order.
Для UnitGroup требуется baseUnit (ссылка на Unit) — создаётся один раз в smoke_base_unit_ref.
Проверки и предусловия (guards) — в tests.api.smoke_checks; подготовка payload для update — в steps.
"""
import copy
import pytest
import testit

pytestmark = pytest.mark.rt_light

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
from tests.api.unitgroup.steps import (
    _find_unitgroup_by,
    _get_unitgroups_list,
    _patch_delete,
    _patch_delete_many,
    _post_unitgroup,
    _put_create_or_update_many,
    _put_unitgroup,
    build_updated_payload_smoke,
    build_updated_payloads_smoke,
    build_unique_unitgroup_payload,
    ensure_one_unit_and_get_ref,
)


@pytest.fixture(scope="module")
def smoke_base_unit_ref(base_server_url, admin_auth):
    """Одна Unit для baseUnit во всех smoke-тестах UnitGroup (создаётся один раз на модуль)."""
    return ensure_one_unit_and_get_ref(base_server_url, admin_auth)


@pytest.fixture(scope="module")
def smoke_state():
    """Общее состояние smoke-сценария: id, integrationId, payload и обновлённые значения полей для A, B1, B2."""
    return {
        "unitgroup_a_id": None,
        "unitgroup_a_integration_id": None,
        "unitgroup_a_payload": None,
        "unitgroup_a_name_updated": None,
        "unitgroup_b_ids": [],
        "unitgroup_b_integration_ids": [],
        "unitgroup_b_payloads": [],
        "unitgroup_b_names_updated": [],
    }


@pytest.fixture(scope="module")
def smoke_urls(base_server_url):
    """URL для smoke-тестов UnitGroup."""
    base = base_server_url.rstrip("/")
    return {
        "put_url": f"{base}/UnitGroup/CreateOrUpdate",
        "put_many_url": base,
        "get_url": f"{base}/UnitGroup",
        "post_url": f"{base}/UnitGroup",
    }


@pytest.mark.smoke
@pytest.mark.order(8)
@pytest.mark.test_name_ru("Smoke: PUT /UnitGroup/CreateOrUpdate — создание одного объекта")
@testit.externalId("smoke_unitgroup_01_create_one")
@testit.displayName("Smoke: PUT /UnitGroup/CreateOrUpdate — создание одного объекта")
@testit.title("Smoke: PUT /UnitGroup/CreateOrUpdate — создание одного объекта")
@testit.description(get_smoke_tc_description("unitgroup", 1))
@testit.nameSpace("API/Smoke")
@testit.className("UnitGroup")
@testit.labels("api", "smoke", "unitgroup")
def test_01_create_one(smoke_state, smoke_urls, smoke_base_unit_ref, admin_auth):
    """PUT /UnitGroup/CreateOrUpdate с минимально валидным payload. 200, added==1, errors==0, results[0].entity.id."""
    print("\n  === Smoke: 1. PUT /UnitGroup/CreateOrUpdate — создание одного объекта ===\n")
    payload = build_unique_unitgroup_payload(smoke_base_unit_ref)
    response = run_smoke_request(lambda: _put_unitgroup(smoke_urls["put_url"], payload=payload, auth=admin_auth))
    uid, iid = assert_create_one_response(response, payload)
    smoke_state["unitgroup_a_id"] = uid
    smoke_state["unitgroup_a_integration_id"] = iid
    smoke_state["unitgroup_a_payload"] = copy.deepcopy(payload)


@pytest.mark.smoke
@pytest.mark.order(9)
@pytest.mark.test_name_ru("Smoke: PUT /UnitGroup/CreateOrUpdate — обновление одного объекта")
@testit.externalId("smoke_unitgroup_01b_update_one")
@testit.displayName("Smoke: PUT /UnitGroup/CreateOrUpdate — обновление одного объекта")
@testit.title("Smoke: PUT /UnitGroup/CreateOrUpdate — обновление одного объекта")
@testit.description(get_smoke_tc_description("unitgroup", 2))
@testit.nameSpace("API/Smoke")
@testit.className("UnitGroup")
@testit.labels("api", "smoke", "unitgroup")
def test_01b_update_one(smoke_state, smoke_urls, admin_auth):
    """PUT /UnitGroup/CreateOrUpdate — обновление объекта A (тот же integrationId), поле name изменено. 200, result Updated, updated: 1."""
    print("\n  === Smoke: 1b. PUT /UnitGroup/CreateOrUpdate — обновление одного объекта ===\n")
    payload = get_required_state(smoke_state, "unitgroup_a_payload", "unitgroup_a_payload не сохранён (запустите test_01_create_one)")
    payload_updated, name_updated = build_updated_payload_smoke(payload)
    response = run_smoke_request(lambda: _put_unitgroup(smoke_urls["put_url"], payload=payload_updated, auth=admin_auth))
    assert_update_one_response(response)
    smoke_state["unitgroup_a_name_updated"] = name_updated


@pytest.mark.smoke
@pytest.mark.order(10)
@pytest.mark.test_name_ru("Smoke: PUT /UnitGroup/CreateOrUpdateMany — создание двух объектов")
@testit.externalId("smoke_unitgroup_02_create_many")
@testit.displayName("Smoke: PUT /UnitGroup/CreateOrUpdateMany — создание двух объектов")
@testit.title("Smoke: PUT /UnitGroup/CreateOrUpdateMany — создание двух объектов")
@testit.description(get_smoke_tc_description("unitgroup", 3))
@testit.nameSpace("API/Smoke")
@testit.className("UnitGroup")
@testit.labels("api", "smoke", "unitgroup")
def test_02_create_many(smoke_state, smoke_urls, smoke_base_unit_ref, admin_auth):
    """PUT /UnitGroup/CreateOrUpdateMany, массив из двух объектов. 200, added==2, errors==0, два элемента в results."""
    print("\n  === Smoke: 2. PUT /UnitGroup/CreateOrUpdateMany — создание двух объектов ===\n")
    payloads = [build_unique_unitgroup_payload(smoke_base_unit_ref) for _ in range(2)]
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads, admin_auth))
    ids, integration_ids = assert_create_many_response(response, payloads)
    smoke_state["unitgroup_b_ids"] = ids
    smoke_state["unitgroup_b_integration_ids"] = integration_ids
    smoke_state["unitgroup_b_payloads"] = copy.deepcopy(payloads)


@pytest.mark.smoke
@pytest.mark.order(11)
@pytest.mark.test_name_ru("Smoke: PUT /UnitGroup/CreateOrUpdateMany — обновление двух объектов")
@testit.externalId("smoke_unitgroup_02b_update_many")
@testit.displayName("Smoke: PUT /UnitGroup/CreateOrUpdateMany — обновление двух объектов")
@testit.title("Smoke: PUT /UnitGroup/CreateOrUpdateMany — обновление двух объектов")
@testit.description(get_smoke_tc_description("unitgroup", 4))
@testit.nameSpace("API/Smoke")
@testit.className("UnitGroup")
@testit.labels("api", "smoke", "unitgroup")
def test_02b_update_many(smoke_state, smoke_urls, admin_auth):
    """PUT /UnitGroup/CreateOrUpdateMany — обновление B1, B2 (те же integrationId), у каждого изменено поле name. 200, updated: 2."""
    print("\n  === Smoke: 2b. PUT /UnitGroup/CreateOrUpdateMany — обновление двух объектов ===\n")
    payloads = get_required_state_list(smoke_state, "unitgroup_b_payloads", 2, "unitgroup_b_payloads не заполнены (запустите test_02_create_many)")
    payloads_updated, names_updated = build_updated_payloads_smoke(payloads)
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads_updated, admin_auth))
    assert_update_many_response(response, count=2)
    smoke_state["unitgroup_b_names_updated"] = names_updated


@pytest.mark.smoke
@pytest.mark.order(12)
@pytest.mark.test_name_ru("Smoke: GET /UnitGroup — в списке есть A, B1, B2 и поля после обновления")
@testit.externalId("smoke_unitgroup_03_get_list")
@testit.displayName("Smoke: GET /UnitGroup — в списке есть A, B1, B2 и поля после обновления")
@testit.title("Smoke: GET /UnitGroup — в списке есть A, B1, B2 и поля после обновления")
@testit.description(get_smoke_tc_description("unitgroup", 5))
@testit.nameSpace("API/Smoke")
@testit.className("UnitGroup")
@testit.labels("api", "smoke", "unitgroup")
def test_03_get_list(smoke_state, smoke_urls, admin_auth):
    """GET /UnitGroup. 200, items — массив, в нём есть A, B1, B2 (по integrationId) и поля name совпадают с обновлёнными."""
    print("\n  === Smoke: 3. GET /UnitGroup — список содержит созданные объекты и значения после обновления ===\n")
    try:
        items = _get_unitgroups_list(smoke_urls["get_url"], admin_auth, page_size=5000)
    except AssertionError as e:
        pytest.fail(f"GET /UnitGroup не вернул 200 или items: {e}")
    id_a = get_required_state(smoke_state, "unitgroup_a_integration_id", "unitgroup_a_integration_id не в state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "unitgroup_b_integration_ids", 2, "unitgroup_b_integration_ids не заполнены")
    name_a_expected = smoke_state.get("unitgroup_a_name_updated")
    names_b_expected = smoke_state.get("unitgroup_b_names_updated") or []
    assert_list_contains_and_names(
        items, id_a, ids_b, _find_unitgroup_by,
        name_a_expected=name_a_expected,
        names_b_expected=names_b_expected,
    )


@pytest.mark.smoke
@pytest.mark.order(13)
@pytest.mark.test_name_ru("Smoke: PATCH /UnitGroup/Delete — удаление объекта A")
@testit.externalId("smoke_unitgroup_04_delete_one")
@testit.displayName("Smoke: PATCH /UnitGroup/Delete — удаление объекта A")
@testit.title("Smoke: PATCH /UnitGroup/Delete — удаление объекта A")
@testit.description(get_smoke_tc_description("unitgroup", 6))
@testit.nameSpace("API/Smoke")
@testit.className("UnitGroup")
@testit.labels("api", "smoke", "unitgroup")
def test_04_delete_one(smoke_state, smoke_urls, admin_auth):
    """PATCH /UnitGroup/Delete по integrationId объекта A. 200/204, deleted==1 при наличии тела."""
    print("\n  === Smoke: 4. PATCH /UnitGroup/Delete — удаление объекта A ===\n")
    ug_a_integration_id = get_required_state(
        smoke_state,
        "unitgroup_a_integration_id",
        "unitgroup_a_integration_id не сохранён в smoke_state (запустите test_01_create_one)",
    )
    response = run_smoke_request(
        lambda: _patch_delete(smoke_urls["put_many_url"], {"integrationId": ug_a_integration_id}, admin_auth)
    )
    assert_delete_one_response(response)


@pytest.mark.smoke
@pytest.mark.order(14)
@pytest.mark.test_name_ru("Smoke: POST /UnitGroup — фильтр по B1 и B2")
@testit.externalId("smoke_unitgroup_05_post_filter")
@testit.displayName("Smoke: POST /UnitGroup — фильтр по B1 и B2")
@testit.title("Smoke: POST /UnitGroup — фильтр по B1 и B2")
@testit.description(get_smoke_tc_description("unitgroup", 7))
@testit.nameSpace("API/Smoke")
@testit.className("UnitGroup")
@testit.labels("api", "smoke", "unitgroup")
def test_05_post_filter(smoke_state, smoke_urls, admin_auth):
    """POST /UnitGroup с фильтром по integrationIds B1 и B2. 200, в items ровно B1 и B2."""
    print("\n  === Smoke: 5. POST /UnitGroup — фильтр по B1 и B2 ===\n")
    integration_ids_b = get_required_state_list(smoke_state, "unitgroup_b_integration_ids", 2, "unitgroup_b_integration_ids не заполнены")
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids_b, "noCount": False}
    response = _post_unitgroup(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_count(response, 2)


@pytest.mark.smoke
@pytest.mark.order(15)
@pytest.mark.test_name_ru("Smoke: PATCH /UnitGroup/DeleteMany — удаление B1 и B2")
@testit.externalId("smoke_unitgroup_06_delete_many")
@testit.displayName("Smoke: PATCH /UnitGroup/DeleteMany — удаление B1 и B2")
@testit.title("Smoke: PATCH /UnitGroup/DeleteMany — удаление B1 и B2")
@testit.description(get_smoke_tc_description("unitgroup", 8))
@testit.nameSpace("API/Smoke")
@testit.className("UnitGroup")
@testit.labels("api", "smoke", "unitgroup")
def test_06_delete_many(smoke_state, smoke_urls, admin_auth):
    """PATCH /UnitGroup/DeleteMany по integrationId объектов B1 и B2. 200/204, deleted==2 при наличии тела."""
    print("\n  === Smoke: 6. PATCH /UnitGroup/DeleteMany — удаление B1 и B2 ===\n")
    ids_b_integration = get_required_state_list(
        smoke_state,
        "unitgroup_b_integration_ids",
        2,
        "unitgroup_b_integration_ids не заполнены",
    )
    body = [{"integrationId": ids_b_integration[0]}, {"integrationId": ids_b_integration[1]}]
    response = _patch_delete_many(smoke_urls["put_many_url"], body, admin_auth)
    assert_delete_many_response(response, expected_deleted=2)


@pytest.mark.smoke
@pytest.mark.order(16)
@pytest.mark.test_name_ru("Smoke: POST /UnitGroup — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.externalId("smoke_unitgroup_07_post_clean")
@testit.displayName("Smoke: POST /UnitGroup — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.title("Smoke: POST /UnitGroup — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.description(get_smoke_tc_description("unitgroup", 9))
@testit.nameSpace("API/Smoke")
@testit.className("UnitGroup")
@testit.labels("api", "smoke", "unitgroup")
def test_07_post_clean(smoke_state, smoke_urls, admin_auth):
    """Финальный POST /UnitGroup. Фильтр по integrationIds A, B1, B2 и проверка, что items пустой (объекты действительно удалены)."""
    print("\n  === Smoke: 7. POST /UnitGroup — финальная проверка чистоты (фильтр по A, B1, B2) ===\n")
    id_a = get_required_state(smoke_state, "unitgroup_a_integration_id", "unitgroup_a_integration_id не сохранён в smoke_state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "unitgroup_b_integration_ids", 2, "unitgroup_b_integration_ids не заполнены (запустите предыдущие шаги)")
    integration_ids = [id_a] + list(ids_b)
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids, "noCount": False}
    response = _post_unitgroup(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_items_empty(response)

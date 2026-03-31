"""
Smoke-тесты для API Item: последовательный сценарий (создание → обновление одного → пачка → обновление пачки → GET с проверкой полей → Delete → POST фильтр → DeleteMany → финальный POST-поиск чистоты).
Состояние между тестами передаётся через fixture smoke_state (scope=module). Порядок выполнения — pytest-order.
Item требует Unit (поле unit); используется фиксированная единица «шт» из БД: id=68 (Штука, Acronym=шт, Code=796). Без запроса GET /Unit. Класс номенклатуры — Сборочная единица (itemClass: 4).
Проверки и предусловия (guards) — в tests.api.smoke_checks; подготовка payload для update — в steps.
"""
import copy
import pytest
import testit

pytestmark = pytest.mark.rt_medium

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
from tests.api.item.steps import (
    _find_item_by,
    _get_items_list,
    _patch_delete,
    _patch_delete_many,
    _post_item,
    _put_create_or_update_many,
    _put_item,
    build_updated_payload_smoke,
    build_updated_payloads_smoke,
    build_unique_item_payload,
)


# --- Фикстуры ---

@pytest.fixture(scope="module")
def smoke_base_unit_ref():
    """Единица «шт» из БД (id=68): Штука, Acronym=шт, Code=796. Без запроса GET /Unit."""
    return {"id": 68}


@pytest.fixture(scope="module")
def smoke_state():
    """Общее состояние smoke-сценария: id, integrationId, payload и обновлённые значения полей для A, B1, B2."""
    return {
        "item_a_id": None,
        "item_a_integration_id": None,
        "item_a_payload": None,
        "item_a_name_updated": None,
        "item_b_ids": [],
        "item_b_integration_ids": [],
        "item_b_payloads": [],
        "item_b_names_updated": [],
    }


@pytest.fixture(scope="module")
def smoke_urls(base_server_url):
    """URL для smoke-тестов Item."""
    base = base_server_url.rstrip("/")
    return {
        "put_url": f"{base}/Item/CreateOrUpdate",
        "put_many_url": base,
        "get_url": f"{base}/Item",
        "post_url": f"{base}/Item",
    }


# --- Тесты ---

@pytest.mark.smoke
@pytest.mark.order(15)
@pytest.mark.test_name_ru("Smoke: PUT /Item/CreateOrUpdate — создание одного объекта")
@testit.externalId("smoke_item_01_create_one")
@testit.displayName("Smoke: PUT /Item/CreateOrUpdate — создание одного объекта")
@testit.title("Smoke: PUT /Item/CreateOrUpdate — создание одного объекта")
@testit.description(get_smoke_tc_description("item", 1))
@testit.nameSpace("API/Smoke")
@testit.className("Item")
@testit.labels("api", "smoke", "item")
def test_01_create_one(smoke_state, smoke_urls, smoke_base_unit_ref, admin_auth):
    """PUT /Item/CreateOrUpdate с минимально валидным payload. 200, added==1, errors==0, results[0].entity.id."""
    print("\n  === Smoke: 1. PUT /Item/CreateOrUpdate — создание одного объекта ===\n")
    payload = build_unique_item_payload(smoke_base_unit_ref)
    response = run_smoke_request(lambda: _put_item(smoke_urls["put_url"], payload=payload, auth=admin_auth))
    uid, iid = assert_create_one_response(response, payload)
    smoke_state["item_a_id"] = uid
    smoke_state["item_a_integration_id"] = iid
    smoke_state["item_a_payload"] = copy.deepcopy(payload)


@pytest.mark.smoke
@pytest.mark.order(16)
@pytest.mark.test_name_ru("Smoke: PUT /Item/CreateOrUpdate — обновление одного объекта")
@testit.externalId("smoke_item_01b_update_one")
@testit.displayName("Smoke: PUT /Item/CreateOrUpdate — обновление одного объекта")
@testit.title("Smoke: PUT /Item/CreateOrUpdate — обновление одного объекта")
@testit.description(get_smoke_tc_description("item", 2))
@testit.nameSpace("API/Smoke")
@testit.className("Item")
@testit.labels("api", "smoke", "item")
def test_01b_update_one(smoke_state, smoke_urls, admin_auth):
    """PUT /Item/CreateOrUpdate — обновление объекта A (тот же integrationId), поле name изменено. 200, result Updated, updated: 1."""
    print("\n  === Smoke: 1b. PUT /Item/CreateOrUpdate — обновление одного объекта ===\n")
    payload = get_required_state(smoke_state, "item_a_payload", "item_a_payload не сохранён (запустите test_01_create_one)")
    payload_updated, name_updated = build_updated_payload_smoke(payload)
    response = run_smoke_request(lambda: _put_item(smoke_urls["put_url"], payload=payload_updated, auth=admin_auth))
    assert_update_one_response(response)
    smoke_state["item_a_name_updated"] = name_updated


@pytest.mark.smoke
@pytest.mark.order(17)
@pytest.mark.test_name_ru("Smoke: PUT /Item/CreateOrUpdateMany — создание двух объектов")
@testit.externalId("smoke_item_02_create_many")
@testit.displayName("Smoke: PUT /Item/CreateOrUpdateMany — создание двух объектов")
@testit.title("Smoke: PUT /Item/CreateOrUpdateMany — создание двух объектов")
@testit.description(get_smoke_tc_description("item", 3))
@testit.nameSpace("API/Smoke")
@testit.className("Item")
@testit.labels("api", "smoke", "item")
def test_02_create_many(smoke_state, smoke_urls, smoke_base_unit_ref, admin_auth):
    """PUT /Item/CreateOrUpdateMany, массив из двух объектов. 200, added==2, errors==0, два элемента в results."""
    print("\n  === Smoke: 2. PUT /Item/CreateOrUpdateMany — создание двух объектов ===\n")
    payloads = [build_unique_item_payload(smoke_base_unit_ref) for _ in range(2)]
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads, admin_auth))
    ids, integration_ids = assert_create_many_response(response, payloads)
    smoke_state["item_b_ids"] = ids
    smoke_state["item_b_integration_ids"] = integration_ids
    smoke_state["item_b_payloads"] = copy.deepcopy(payloads)


@pytest.mark.smoke
@pytest.mark.order(18)
@pytest.mark.test_name_ru("Smoke: PUT /Item/CreateOrUpdateMany — обновление двух объектов")
@testit.externalId("smoke_item_02b_update_many")
@testit.displayName("Smoke: PUT /Item/CreateOrUpdateMany — обновление двух объектов")
@testit.title("Smoke: PUT /Item/CreateOrUpdateMany — обновление двух объектов")
@testit.description(get_smoke_tc_description("item", 4))
@testit.nameSpace("API/Smoke")
@testit.className("Item")
@testit.labels("api", "smoke", "item")
def test_02b_update_many(smoke_state, smoke_urls, admin_auth):
    """PUT /Item/CreateOrUpdateMany — обновление B1, B2 (те же integrationId), у каждого изменено поле name. 200, updated: 2."""
    print("\n  === Smoke: 2b. PUT /Item/CreateOrUpdateMany — обновление двух объектов ===\n")
    payloads = get_required_state_list(smoke_state, "item_b_payloads", 2, "item_b_payloads не заполнены (запустите test_02_create_many)")
    payloads_updated, names_updated = build_updated_payloads_smoke(payloads)
    response = run_smoke_request(lambda: _put_create_or_update_many(smoke_urls["put_many_url"], payloads_updated, admin_auth))
    assert_update_many_response(response, count=2)
    smoke_state["item_b_names_updated"] = names_updated


@pytest.mark.smoke
@pytest.mark.order(19)
@pytest.mark.test_name_ru("Smoke: GET /Item — в списке есть A, B1, B2 и поля после обновления")
@testit.externalId("smoke_item_03_get_list")
@testit.displayName("Smoke: GET /Item — в списке есть A, B1, B2 и поля после обновления")
@testit.title("Smoke: GET /Item — в списке есть A, B1, B2 и поля после обновления")
@testit.description(get_smoke_tc_description("item", 5))
@testit.nameSpace("API/Smoke")
@testit.className("Item")
@testit.labels("api", "smoke", "item")
def test_03_get_list(smoke_state, smoke_urls, admin_auth):
    """GET /Item. 200, items — массив, в нём есть A, B1, B2 (по integrationId) и поля name совпадают с обновлёнными."""
    print("\n  === Smoke: 3. GET /Item — список содержит созданные объекты и значения после обновления ===\n")
    try:
        items = _get_items_list(smoke_urls["get_url"], admin_auth, page_size=5000)
    except AssertionError as e:
        pytest.fail(f"GET /Item не вернул 200 или items: {e}")
    id_a = get_required_state(smoke_state, "item_a_integration_id", "item_a_integration_id не в state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "item_b_integration_ids", 2, "item_b_integration_ids не заполнены")
    name_a_expected = smoke_state.get("item_a_name_updated")
    names_b_expected = smoke_state.get("item_b_names_updated") or []
    assert_list_contains_and_names(
        items, id_a, ids_b, _find_item_by,
        name_a_expected=name_a_expected,
        names_b_expected=names_b_expected,
    )


@pytest.mark.smoke
@pytest.mark.order(20)
@pytest.mark.test_name_ru("Smoke: PATCH /Item/Delete — удаление объекта A")
@testit.externalId("smoke_item_04_delete_one")
@testit.displayName("Smoke: PATCH /Item/Delete — удаление объекта A")
@testit.title("Smoke: PATCH /Item/Delete — удаление объекта A")
@testit.description(get_smoke_tc_description("item", 6))
@testit.nameSpace("API/Smoke")
@testit.className("Item")
@testit.labels("api", "smoke", "item")
def test_04_delete_one(smoke_state, smoke_urls, admin_auth):
    """PATCH /Item/Delete по integrationId объекта A. 200/204, deleted==1 при наличии тела."""
    print("\n  === Smoke: 4. PATCH /Item/Delete — удаление объекта A ===\n")
    item_a_integration_id = get_required_state(
        smoke_state,
        "item_a_integration_id",
        "item_a_integration_id не сохранён в smoke_state (запустите test_01_create_one)",
    )
    response = run_smoke_request(
        lambda: _patch_delete(smoke_urls["put_many_url"], {"integrationId": item_a_integration_id}, admin_auth)
    )
    assert_delete_one_response(response)


@pytest.mark.smoke
@pytest.mark.order(21)
@pytest.mark.test_name_ru("Smoke: POST /Item — фильтр по B1 и B2")
@testit.externalId("smoke_item_05_post_filter")
@testit.displayName("Smoke: POST /Item — фильтр по B1 и B2")
@testit.title("Smoke: POST /Item — фильтр по B1 и B2")
@testit.description(get_smoke_tc_description("item", 7))
@testit.nameSpace("API/Smoke")
@testit.className("Item")
@testit.labels("api", "smoke", "item")
def test_05_post_filter(smoke_state, smoke_urls, admin_auth):
    """POST /Item с фильтром по integrationIds B1 и B2. 200, в items ровно B1 и B2."""
    print("\n  === Smoke: 5. POST /Item — фильтр по B1 и B2 ===\n")
    integration_ids_b = get_required_state_list(smoke_state, "item_b_integration_ids", 2, "item_b_integration_ids не заполнены")
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids_b, "noCount": False}
    response = _post_item(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_count(response, 2)


@pytest.mark.smoke
@pytest.mark.order(22)
@pytest.mark.test_name_ru("Smoke: PATCH /Item/DeleteMany — удаление B1 и B2")
@testit.externalId("smoke_item_06_delete_many")
@testit.displayName("Smoke: PATCH /Item/DeleteMany — удаление B1 и B2")
@testit.title("Smoke: PATCH /Item/DeleteMany — удаление B1 и B2")
@testit.description(get_smoke_tc_description("item", 8))
@testit.nameSpace("API/Smoke")
@testit.className("Item")
@testit.labels("api", "smoke", "item")
def test_06_delete_many(smoke_state, smoke_urls, admin_auth):
    """PATCH /Item/DeleteMany по integrationId объектов B1 и B2. 200/204, deleted==2 при наличии тела."""
    print("\n  === Smoke: 6. PATCH /Item/DeleteMany — удаление B1 и B2 ===\n")
    ids_b_integration = get_required_state_list(
        smoke_state,
        "item_b_integration_ids",
        2,
        "item_b_integration_ids не заполнены",
    )
    body = [{"integrationId": ids_b_integration[0]}, {"integrationId": ids_b_integration[1]}]
    response = _patch_delete_many(smoke_urls["put_many_url"], body, admin_auth)
    assert_delete_many_response(response, expected_deleted=2)


@pytest.mark.smoke
@pytest.mark.order(23)
@pytest.mark.test_name_ru("Smoke: POST /Item — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.externalId("smoke_item_07_post_clean")
@testit.displayName("Smoke: POST /Item — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.title("Smoke: POST /Item — финальная проверка чистоты (фильтр по A, B1, B2)")
@testit.description(get_smoke_tc_description("item", 9))
@testit.nameSpace("API/Smoke")
@testit.className("Item")
@testit.labels("api", "smoke", "item")
def test_07_post_clean(smoke_state, smoke_urls, admin_auth):
    """Финальный POST /Item. Фильтр по integrationIds A, B1, B2 и проверка, что items пустой (объекты действительно удалены)."""
    print("\n  === Smoke: 7. POST /Item — финальная проверка чистоты (фильтр по A, B1, B2) ===\n")
    id_a = get_required_state(smoke_state, "item_a_integration_id", "item_a_integration_id не сохранён в smoke_state (запустите предыдущие шаги)")
    ids_b = get_required_state_list(smoke_state, "item_b_integration_ids", 2, "item_b_integration_ids не заполнены (запустите предыдущие шаги)")
    integration_ids = [id_a] + list(ids_b)
    body = {"pageNum": 0, "pageSize": 100, "integrationIds": integration_ids, "noCount": False}
    response = _post_item(smoke_urls["post_url"], body, auth=admin_auth)
    assert_post_filter_items_empty(response)

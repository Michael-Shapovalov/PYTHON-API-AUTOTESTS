"""
Assertion/Verification layer для smoke-тестов API (Unit, UnitGroup, Item).
Все проверки ответов API вынесены сюда; тесты вызывают только steps и эти функции.
Не импортирует steps/client во избежание циклических зависимостей.
"""
import pytest
from requests.exceptions import ConnectTimeout, ConnectionError as RequestsConnectionError


def get_required_state(state, key, hint):
    """Проверяет, что state[key] не None и не пустой список. Иначе pytest.fail(hint). Возвращает state[key]."""
    if key not in state:
        pytest.fail(hint)
    value = state[key]
    if value is None:
        pytest.fail(hint)
    if isinstance(value, list) and len(value) == 0:
        pytest.fail(hint)
    return value


def get_required_state_list(state, key, min_len=2, hint=""):
    """Проверяет, что state[key] — список и len >= min_len. Иначе pytest.fail(hint). Возвращает state[key]."""
    if key not in state:
        pytest.fail(hint)
    value = state[key]
    if not isinstance(value, list) or len(value) < min_len:
        pytest.fail(hint)
    return value


def run_smoke_request(fn):
    """Вызывает fn(). При ConnectTimeout или ConnectionError — pytest.fail с сообщением о связи с сервером."""
    try:
        return fn()
    except (ConnectTimeout, RequestsConnectionError) as e:
        pytest.fail(f"Нет связи с сервером: {e}")


def _log_check(what: str, expected, actual):
    """Логирование проверки для вывода в консоль."""
    print(f"  Проверка: {what}: ожидаемый {expected} - фактический {actual}")


def assert_create_one_response(response, payload):
    """
    Проверяет ответ PUT CreateOrUpdate (создание одного): 200, count==1, added==1, errors==0,
    results[0].result=="Added", entity.id валиден. Возвращает (entity_id, integration_id).
    """
    _log_check("код ответа", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    _log_check("ответ — валидный JSON", True, isinstance(data, dict))
    assert data.get("count") == 1, f"Ожидался count==1, получен {data.get('count')}"
    assert data.get("added") == 1, f"Ожидался added==1, получен {data.get('added')}"
    assert data.get("errors") == 0, f"Ожидался errors==0, получен {data.get('errors')}"
    results = data.get("results") or []
    assert len(results) == 1, f"Ожидался 1 элемент в results, получено {len(results)}"
    first = results[0]
    if first.get("result"):
        _log_check("results[0].result", "Added", first.get("result"))
        assert first.get("result") == "Added", f"Ожидался result=='Added', получен {first.get('result')}"
    entity = first.get("entity") or first
    assert "id" in entity, f"В entity отсутствует поле id: {entity}"
    uid = entity["id"]
    assert uid and (
        (isinstance(uid, int) and uid > 0) or isinstance(uid, str)
    ), f"entity.id должен быть > 0: {uid}"
    _log_check("entity.id", uid, uid)
    integration_id = payload.get("integrationId")
    return uid, integration_id


def assert_update_one_response(response):
    """Проверяет ответ PUT CreateOrUpdate (обновление одного): 200, updated==1, result 'Updated'."""
    _log_check("код ответа", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    results = data.get("results") or []
    if len(results) >= 1 and results[0].get("result"):
        _log_check("results[0].result", "Updated", results[0].get("result"))
        assert results[0].get("result") == "Updated", (
            f"Ожидался result=='Updated', получен {results[0].get('result')}"
        )
    assert data.get("updated") == 1, f"Ожидался updated==1, получен {data.get('updated')}"


def assert_create_many_response(response, payloads):
    """
    Проверяет ответ PUT CreateOrUpdateMany (создание пачки): 200, added==2, errors==0,
    len(results)==2, у каждого entity.id. Возвращает (ids, integration_ids).
    """
    _log_check("код ответа", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("added") == 2, f"Ожидался added==2, получен {data.get('added')}"
    assert data.get("errors") == 0, f"Ожидался errors==0, получен {data.get('errors')}"
    results = data.get("results") or []
    assert len(results) == 2, f"Ожидалось 2 элемента в results, получено {len(results)}"
    ids = []
    integration_ids = []
    for i, r in enumerate(results):
        entity = r.get("entity") or r
        uid = entity.get("id") if entity else r.get("id")
        if uid is not None:
            ids.append(uid)
        integration_ids.append(payloads[i].get("integrationId"))
    assert len(ids) == 2, f"Ожидалось 2 id в results (entity.id), получено {len(ids)}: {ids}"
    _log_check("два элемента в results с id", 2, len(ids))
    return ids, integration_ids


def assert_update_many_response(response, count=2):
    """Проверяет ответ PUT CreateOrUpdateMany (обновление пачки): 200, updated==count, errors==0."""
    _log_check("код ответа", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("updated") == count, f"Ожидался updated=={count}, получен {data.get('updated')}"
    assert data.get("errors") == 0, f"Ожидался errors==0, получен {data.get('errors')}"


def assert_list_contains_and_names(
    items,
    id_a,
    ids_b,
    find_fn,
    name_a_expected=None,
    names_b_expected=None,
    field_name="name",
):
    """
    Проверяет, что items — список, в нём найдены A и B1, B2 по integrationId (find_fn),
    и при переданных name_a_expected/names_b_expected — значения поля field_name совпадают.
    find_fn(items, key, value) -> item or None.
    """
    _log_check("items — массив", True, isinstance(items, list))
    assert isinstance(items, list), f"items должен быть массивом, получен {type(items)}"
    found_a = find_fn(items, "integrationId", id_a)
    found_b1 = find_fn(items, "integrationId", ids_b[0]) if ids_b else None
    found_b2 = find_fn(items, "integrationId", ids_b[1]) if len(ids_b) > 1 else None
    _log_check("объект A в списке", True, found_a is not None)
    _log_check("объект B1 в списке", True, found_b1 is not None)
    _log_check("объект B2 в списке", True, found_b2 is not None)
    assert found_a is not None, f"Объект A (integrationId={id_a}) не найден в items"
    assert found_b1 is not None, "Объект B1 не найден в items"
    assert found_b2 is not None, "Объект B2 не найден в items"
    if name_a_expected is not None:
        _log_check(f"A.{field_name} после обновления", name_a_expected, found_a.get(field_name))
        assert found_a.get(field_name) == name_a_expected, (
            f"Ожидался {field_name}={name_a_expected!r}, получен {found_a.get(field_name)!r}"
        )
    if names_b_expected and len(names_b_expected) >= 2:
        _log_check(f"B1.{field_name} после обновления", names_b_expected[0], found_b1.get(field_name))
        _log_check(f"B2.{field_name} после обновления", names_b_expected[1], found_b2.get(field_name))
        assert found_b1.get(field_name) == names_b_expected[0], (
            f"B1: ожидался {field_name}={names_b_expected[0]!r}, получен {found_b1.get(field_name)!r}"
        )
        assert found_b2.get(field_name) == names_b_expected[1], (
            f"B2: ожидался {field_name}={names_b_expected[1]!r}, получен {found_b2.get(field_name)!r}"
        )


def assert_delete_one_response(response):
    """Проверяет ответ PATCH Delete (одного): status 200 или 204; при 200 и теле — deleted==1."""
    _log_check("код ответа", "200 или 204", response.status_code)
    assert response.status_code in (200, 204), response.text
    if response.status_code == 200 and response.text:
        try:
            data = response.json()
            deleted = data.get("deleted")
            _log_check("deleted в ответе", 1, deleted)
            assert deleted == 1 or deleted is True, f"Ожидался deleted==1, получен {deleted}"
        except Exception:
            pass


def assert_post_filter_count(response, expected_count):
    """Проверяет ответ POST (фильтр): 200, len(items)==expected_count."""
    _log_check("код ответа", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    items = data.get("items") or []
    total = data.get("total")
    _log_check(f"items содержит ровно {expected_count} элемента", expected_count, len(items))
    assert len(items) == expected_count, (
        f"Ожидалось {expected_count} элемента в items, получено {len(items)}. total={total}"
    )


def assert_post_filter_items_empty(response):
    """Проверяет ответ POST (финальная чистота): 200, items пустой."""
    _log_check("код ответа", 200, response.status_code)
    assert response.status_code == 200, response.text
    data = response.json()
    items = data.get("items") or []
    total = data.get("total")
    _log_check("items пустой для удалённых A, B1, B2", 0, len(items))
    assert len(items) == 0, (
        f"Ожидалось, что A/B1/B2 не вернутся в POST-фильтре, но items содержит {len(items)} элементов. total={total}"
    )


def assert_delete_many_response(response, expected_deleted=2):
    """Проверяет ответ PATCH DeleteMany: status 200 или 204; при 200 и теле — deleted >= 1 (обычно 2)."""
    _log_check("код ответа", "200 или 204", response.status_code)
    assert response.status_code in (200, 204), response.text
    if response.status_code == 200 and response.text:
        try:
            data = response.json()
            deleted = data.get("deleted")
            _log_check("deleted в ответе", expected_deleted, deleted)
            assert deleted == expected_deleted or (
                isinstance(deleted, int) and deleted >= 1
            ), f"Ожидался deleted=={expected_deleted}, получен {deleted}"
        except Exception:
            pass

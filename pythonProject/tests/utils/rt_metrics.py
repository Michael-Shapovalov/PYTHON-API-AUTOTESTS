"""
SLA по времени ответа API: сбор метрик и warm-up по endpoint.
Один запрос → один замер → один assert (кроме первого запроса на endpoint — WARMUP).
"""
import time
import os
from typing import List, Dict, Any, Optional

# Текущая категория SLA для теста (выставляется фикстурой из маркера rt_light/rt_medium/rt_heavy)
_current_rt_category: Optional[str] = None


def set_rt_category(category: Optional[str]) -> None:
    global _current_rt_category
    _current_rt_category = category


def get_rt_category(service_default: str) -> str:
    """Вернуть категорию из маркера теста или service_default (Unit/UnitGroup=rt_light, Item=rt_medium)."""
    return _current_rt_category if _current_rt_category is not None else service_default


def get_rt_category_raw() -> Optional[str]:
    """Текущая категория без default (для сохранения/восстановления в фикстуре)."""
    return _current_rt_category


THRESHOLDS = {
    "rt_light": 3.0,
    "rt_medium": 5.0,
    "rt_heavy": 10.0,
}

_warmup_seen: set = set()
_records: List[Dict[str, Any]] = []


def _endpoint_key(service: str, method: str, path: str) -> str:
    return f"{service}:{method}:{path}"


def is_warmup(service: str, method: str, path: str) -> bool:
    """Первый запрос на данный endpoint считается warm-up."""
    return _endpoint_key(service, method, path) not in _warmup_seen


def mark_warmup_seen(service: str, method: str, path: str) -> None:
    _warmup_seen.add(_endpoint_key(service, method, path))


def record(
    service: str,
    method: str,
    path: str,
    category: str,
    time_sec: float,
) -> None:
    """
    Записать замер (вызывается только при первом обращении к endpoint).
    status: OK или FAIL.
    """
    threshold = THRESHOLDS.get(category, THRESHOLDS["rt_medium"])
    status = "OK" if time_sec <= threshold else "FAIL"
    _records.append({
        "service": service,
        "method": method,
        "path": path,
        "category": category,
        "time_sec": round(time_sec, 3),
        "threshold_sec": threshold,
        "status": status,
    })


def get_all() -> List[Dict[str, Any]]:
    return list(_records)


def clear() -> None:
    global _warmup_seen, _records
    _warmup_seen = set()
    _records = []


def _tk_prefix_from_current_test() -> str:
    """
    Возвращает префикс 'TK-<n>' для smoke-flow тестов по имени pytest-теста.
    Используется только для заголовков шагов, которые отправляются в TestIT.
    """
    cur = os.environ.get("PYTEST_CURRENT_TEST") or ""
    if "::" not in cur:
        return ""
    name = cur.split("::")[-1].split(" ", 1)[0].strip()
    mapping = {
        "test_01_create_one": "TK-1",
        "test_01b_update_one": "TK-2",
        "test_02_create_many": "TK-3",
        "test_02b_update_many": "TK-4",
        "test_03_get_list": "TK-5",
        "test_04_delete_one": "TK-6",
        "test_05_post_filter": "TK-7",
        "test_06_delete_many": "TK-8",
        "test_07_post_clean": "TK-9",
    }
    return mapping.get(name, "")


def timed_request(service: str, method: str, path: str, category: str, request_fn):
    """
    Выполнить request_fn(). Время замеряется и проверяется только при первом вызове
    для данного endpoint; при превышении порога тест падает. Повторные вызовы — без замера.
    """
    # TestIT UI: центральная область "Описание" показывает setup/teardown/steps.
    # Чтобы там появились шаги, оборачиваем каждый вызов endpoint в testit.step (если библиотека доступна).
    try:
        import testit as _testit  # type: ignore
    except Exception:
        _testit = None

    tk = _tk_prefix_from_current_test()
    step_title = f"{tk} {service}: {method} {path}".strip()

    def _add_step_message(msg: str) -> None:
        if _testit is None:
            return
        try:
            _testit.addMessage(msg)
        except Exception:
            # Не ломаем тесты из-за проблем TMS
            pass

    def _run():
        key = _endpoint_key(service, method, path)
        if key in _warmup_seen:
            result = request_fn()
            status_code = getattr(result, "status_code", None)
            _add_step_message(
                f"категория={category}; замер=нет; статус={status_code if status_code is not None else 'n/a'}"
            )
            return result
        t0 = time.perf_counter()
        result = request_fn()
        dt = time.perf_counter() - t0
        _warmup_seen.add(key)
        record(service, method, path, category, dt)
        threshold = THRESHOLDS.get(category, THRESHOLDS["rt_medium"])
        status_code = getattr(result, "status_code", None)
        _add_step_message(
            f"категория={category}; замер=да; время={dt:.3f}с; порог={threshold}с; статус={status_code if status_code is not None else 'n/a'}"
        )
        assert dt <= threshold, (
            f"SLA времени ответа: {service} {method} {path} — {dt:.3f} с > {threshold} с (категория {category})"
        )
        return result

    if _testit is None:
        return _run()

    with _testit.step(step_title):
        return _run()

import json
import os
import sys

# Корень проекта в PYTHONPATH (для будущих импортов api и т.д.)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# На Windows при выводе в консоль без -s или при кодировке cp1251 таблица с русскими/Unicode может падать — включаем UTF-8
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# При запуске с pytest-xdist (-n 2 и т.д.) stdout воркеров не передаётся в главный процесс (ограничение execnet).
# stderr передаётся. Перенаправляем stdout в stderr, чтобы логи и пояснения тестов (print) выводились и при параллельном запуске.
if hasattr(sys, "stdout") and hasattr(sys, "stderr"):
    sys.stdout = sys.stderr

import pytest
from dotenv import load_dotenv

load_dotenv()

# Итоги прогона: список (название_теста, результат) для таблицы в конце
_test_results = []


def pytest_sessionstart(session):
    """Очистка списка результатов перед прогоном и метрик SLA."""
    global _test_results
    _test_results = []
    try:
        from tests.utils import rt_metrics
        rt_metrics.clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _rt_category_context(request):
    """Устанавливает категорию SLA (rt_light/rt_medium/rt_heavy) из маркеров теста для steps."""
    try:
        from tests.utils import rt_metrics
        prev = rt_metrics.get_rt_category_raw()
        if request.node.get_closest_marker("rt_heavy"):
            rt_metrics.set_rt_category("rt_heavy")
        elif request.node.get_closest_marker("rt_medium"):
            rt_metrics.set_rt_category("rt_medium")
        elif request.node.get_closest_marker("rt_light"):
            rt_metrics.set_rt_category("rt_light")
        else:
            rt_metrics.set_rt_category(None)
        yield
        rt_metrics.set_rt_category(prev)
    except Exception:
        yield


def _get_test_name_ru(item):
    """Русское название теста из маркера test_name_ru или имя функции."""
    marker = item.get_closest_marker("test_name_ru")
    if marker and len(marker.args) > 0:
        return marker.args[0]
    return item.name


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Сохраняем результат теста и причину падения для итоговой таблицы."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        reason = ""
        if report.outcome == "failed":
            try:
                if getattr(report, "excinfo", None) and report.excinfo and report.excinfo.value:
                    reason = str(report.excinfo.value)
                elif getattr(report, "longrepr", None) and report.longrepr:
                    s = str(report.longrepr).strip()
                    if s:
                        last_line = s.split("\n")[-1].strip()
                        if last_line.startswith("AssertionError: "):
                            last_line = last_line[16:].strip()
                        elif last_line.startswith("Failed: "):
                            last_line = last_line[8:].strip()
                        reason = last_line
                if len(reason) > 150:
                    reason = reason[:147] + "..."
            except Exception:
                pass
        _test_results.append((_get_test_name_ru(item), report.outcome, reason))


def _safe_print(text):
    """Печать в stdout с обходом ошибок кодировки (Windows cp1251 и т.д.)."""
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        try:
            sys.stdout.buffer.write((text + "\n").encode(sys.stdout.encoding or "utf-8", errors="replace"))
            sys.stdout.buffer.flush()
        except Exception:
            pass


def _xdist_results_dir(config_or_session):
    """Каталог для обмена результатами воркеров с контроллером (pytest-xdist)."""
    config = getattr(config_or_session, "config", config_or_session)
    root = getattr(config, "rootdir", None)
    if root is not None:
        root = str(root)
    else:
        root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, ".xdist_worker_results")


def _print_results_table(results):
    """Печать итоговой таблицы: упавшие тесты с причиной; итог — всего/пройдено/не пройдено/пропущено."""
    if not results:
        return
    passed = sum(1 for r in results if r[1] == "passed")
    failed = sum(1 for r in results if r[1] == "failed")
    skipped = sum(1 for r in results if r[1] == "skipped")
    failed_only = [(r[0], r[2] if len(r) > 2 else "") for r in results if r[1] == "failed"]
    width = max(len(name) for name, _ in failed_only) if failed_only else 40
    width = min(width + 2, 70)
    border = "=" * (width + 16)
    _safe_print("\n" + border)
    _safe_print("  ИТОГИ ПРОГОНА ТЕСТОВ")
    _safe_print(border)
    if failed_only:
        for name, reason in failed_only:
            _safe_print(f"  {name:<{width}} НЕ ПРОЙДЕН")
            if reason:
                _safe_print(f"    Причина: {reason}")
    else:
        _safe_print("  (упавших тестов нет)")
    _safe_print(border)
    _safe_print(f"  Всего: {len(results)}  |  Пройдено: {passed}  |  Не пройдено: {failed}  |  Пропущено: {skipped}")
    _safe_print(border + "\n")


def _print_rt_summary(rt_records):
    """Печать сводки норм времени ответа API: число замеров, OK/FAIL/WARMUP, нарушения, топ медленных."""
    if not rt_records:
        return
    ok_count = sum(1 for r in rt_records if r.get("status") == "OK")
    fail_count = sum(1 for r in rt_records if r.get("status") == "FAIL")
    warmup_count = sum(1 for r in rt_records if r.get("status") == "WARMUP")
    border = "=" * 72
    _safe_print("\n" + border)
    _safe_print("  НОРМЫ ВРЕМЕНИ ОТВЕТА API")
    _safe_print(border)
    _safe_print(f"  Всего замеров: {len(rt_records)}  |  OK: {ok_count}  |  FAIL: {fail_count}  |  WARMUP: {warmup_count}")
    _safe_print(border)
    failures = [r for r in rt_records if r.get("status") == "FAIL"]
    if failures:
        _safe_print("  НАРУШЕНИЯ НОРМ ВРЕМЕНИ ОТВЕТА:")
        for r in failures:
            _safe_print(
                f"    {r.get('service', '')} {r.get('method', '')} {r.get('path', '')} — "
                f"{r.get('time_sec')} с > {r.get('threshold_sec')} с ({r.get('category', '')})"
            )
        _safe_print(border)
    slow = sorted([r for r in rt_records if r.get("status") != "WARMUP"], key=lambda x: x.get("time_sec", 0), reverse=True)[:10]
    if slow:
        _safe_print("  ТОП-10 ПО ВРЕМЕНИ ОТВЕТА:")
        for r in slow:
            _safe_print(f"    {r.get('service', '')} {r.get('method', '')} {r.get('path', '')} — {r.get('time_sec')} с ({r.get('status', '')})")
    _safe_print(border + "\n")


def pytest_sessionfinish(session, exitstatus):
    """Итоги: при xdist воркер пишет результаты в файл; без xdist — печать таблицы здесь."""
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id:
        # Воркер: сохраняем результаты и метрики SLA в общий каталог для сбора контроллером
        results_dir = _xdist_results_dir(session)
        try:
            os.makedirs(results_dir, exist_ok=True)
            if _test_results:
                path = os.path.join(results_dir, f"{worker_id}.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(_test_results, f, ensure_ascii=False)
            try:
                from tests.utils import rt_metrics
                rt_all = rt_metrics.get_all()
                if rt_all:
                    rt_path = os.path.join(results_dir, f"{worker_id}_rt.json")
                    with open(rt_path, "w", encoding="utf-8") as f:
                        json.dump(rt_all, f, ensure_ascii=False)
            except Exception:
                pass
        except Exception:
            pass
        return
    # Не воркер: обычный запуск — выводим таблицу и SLA, если есть результаты
    if _test_results:
        _print_results_table(_test_results)
    try:
        from tests.utils import rt_metrics
        rt_all = rt_metrics.get_all()
        if rt_all:
            _print_rt_summary(rt_all)
    except Exception:
        pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """После завершения всех воркеров: общая таблица результатов и сводка SLA по времени ответа."""
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return
    results_dir = _xdist_results_dir(config)
    if not os.path.isdir(results_dir):
        return
    all_results = []
    all_rt = []
    try:
        for fn in sorted(os.listdir(results_dir)):
            path = os.path.join(results_dir, fn)
            if fn.endswith("_rt.json"):
                with open(path, "r", encoding="utf-8") as f:
                    all_rt.extend(json.load(f))
            elif fn.endswith(".json"):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                all_results.extend(data)
        if all_results:
            all_results.sort(key=lambda x: (x[0], x[1]))
            _print_results_table(all_results)
        if all_rt:
            _print_rt_summary(all_rt)
    except Exception:
        pass
    try:
        for fn in os.listdir(results_dir):
            os.remove(os.path.join(results_dir, fn))
        os.rmdir(results_dir)
    except Exception:
        pass


@pytest.fixture(scope="session")
def base_server_url() -> str:
    """URL сервера из .env (для будущих API-тестов)."""
    url = os.getenv("BASE_SERVER_URL")
    if not url:
        pytest.fail("BASE_SERVER_URL not set in .env")
    return url


@pytest.fixture(scope="session")
def admin_auth():
    """Basic Auth из .env (для будущих API-тестов)."""
    from requests.auth import HTTPBasicAuth

    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    if not username or not password:
        pytest.fail("ADMIN_USERNAME or ADMIN_PASSWORD not set in .env")
    return HTTPBasicAuth(username, password)

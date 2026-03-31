# API Autotests (Python)

Автотесты для REST API. В проекте тестируются разделы API: **Unit** (единицы измерения), **UnitGroup** (группы единиц измерения), **Item** (номенклатурные позиции). Тесты расположены в `tests/api/unit/`, `tests/api/unitgroup/`, `tests/api/item/`, а также в подпапках **smoke** для быстрого набора проверок.

---

## Требования

- Python 3.x
- Файл **`.env`** в корне проекта с переменными:
  - `BASE_SERVER_URL` — базовый URL сервера API
  - `ADMIN_USERNAME`, `ADMIN_PASSWORD` — учётные данные для Basic Auth

Установка зависимостей: `pip install -r requirements.txt`

---

## Запуск тестов (общее)

Запуск выполняется из каталога **`tests`** (где находится `pytest.ini`). Из корня проекта: `cd tests`.

Во всех командах используется **`-s`**: логи и пояснения тестов (заголовки «=== Тест: … ===», строки «Проверка: …», итоговая таблица) выводятся в консоль. В `conftest.py` настроено перенаправление stdout → stderr, чтобы вывод был виден и при параллельном запуске с pytest-xdist (`-n 2`).

**Важно:** smoke-тесты в папках `api/unit/smoke/`, `api/unitgroup/smoke/` и `api/item/smoke/` используют общее состояние (фикстуры `scope=module`). Для двух потоков используйте `--dist loadscope`, чтобы все шаги одного smoke-файла выполнялись в одном воркере.

---

## Smoke-тесты (маркер `smoke`)

Отдельные наборы минимальных проверок в папках **`api/unit/smoke/`**, **`api/unitgroup/smoke/`** и **`api/item/smoke/`**. Порядок выполнения задаётся pytest-order: Unit (order 1–7), UnitGroup (order 8–14), Item (order 15–21).

**Запуск всех smoke-тестов (последовательно):**

```bash
cd tests
pytest api -m smoke -v -s
```

**Запуск всех smoke-тестов в 2 потока (рекомендуемый параллельный режим):**

```bash
cd tests
pytest api -m smoke -n 2 --dist loadscope -v -s
```

**Только smoke Unit:**

```bash
cd tests
pytest api/unit/smoke -m smoke -v -s
```

**Только smoke UnitGroup:**

```bash
cd tests
pytest api/unitgroup/smoke -m smoke -v -s
```

**Только smoke Item:**

```bash
cd tests
pytest api/item/smoke -m smoke -v -s
```

---

## Интеграция с Test IT (TestIT) через pytest-адаптер

В проект добавлена интеграция через пакет `testit-adapter-pytest` (см. `docs/testit_integration.md`).

1) Важно про `.env`  
`.env` подхватывается внутри тестов (через `tests/conftest.py`), но **TestIT-адаптер инициализируется раньше**, поэтому для адаптера используйте конфиг-файл.

Создайте `connection_config.ini` в корне `pythonProject` (можно скопировать из `connection_config.ini.example`) и заполните:
- `privateToken=<ваш токен>`
- `projectId=<GUID проекта>`
- `configurationId=ce89a13c-0062-48bd-85c7-e051dfd72fe3`
- `adapterMode=2` (рекомендуется: новый тест-ран на каждый запуск)

2) Установите зависимости:

```bash
pip install -r requirements.txt
```

3) Запускайте pytest с флагом `--testit` (без него адаптер не активируется):

```bash
cd tests
pytest api -m smoke --testit -v -s
```

**Что входит в smoke (для каждой сущности):**  
PUT CreateOrUpdate (один объект) → PUT CreateOrUpdateMany (два объекта) → GET (поиск созданных) → PATCH Delete (один) → POST (фильтр по оставшимся) → PATCH DeleteMany (два) → GET (финальная проверка чистоты). Созданные данные удаляются в конце сценария. Для **Item** в начале сценария создаётся одна Unit (поле unit обязательно).

---

## Тесты API Unit (Единицы измерения)

Расположение: `tests/api/unit/` (и smoke в `tests/api/unit/smoke/`).

### Smoke-набор по маркеру `fast` (тесты вне папки smoke)

Тесты с маркером **`fast`**: по одному успешному сценарию на каждый метод API плюс проверка 401 без авторизации. Всего 7 тестов.

**Команда:**

```bash
cd tests
pytest api/unit -m fast -v -s
```

**Что входит:**  
PUT /Unit/CreateOrUpdate (эталонный + 401), GET /Unit, POST /Unit, PUT /Unit/CreateOrUpdateMany, PATCH /Unit/Delete, PATCH /Unit/DeleteMany.

### Полный набор тестов Unit

Все тесты в `api/unit`: регрессия, валидация, негативные кейсы, граничные значения.

```bash
cd tests
pytest api/unit -v -s
```

**Только «медленные» тесты (без fast):**

```bash
cd tests
pytest api/unit -m slow -v -s
```

### Параллельный запуск (Unit)

Для полного прогона Unit можно использовать несколько воркеров. Smoke тоже можно запускать в 2 потока, но только с `--dist loadscope`.

```bash
cd tests
pytest api/unit -n 2 -v -s
pytest api/unit -n auto -v -s
pytest api/unit/smoke -m smoke -n 2 --dist loadscope -v -s
```

### Шпаргалка команд (Unit)

| Задача                 | Команда (из каталога `tests`)        |
|------------------------|--------------------------------------|
| Smoke (папка smoke)    | `pytest api/unit/smoke -m smoke -v -s` |
| Smoke в 2 воркера      | `pytest api/unit/smoke -m smoke -n 2 --dist loadscope -v -s` |
| Smoke (маркер fast)    | `pytest api/unit -m fast -v -s`      |
| Полный прогон          | `pytest api/unit -v -s`              |
| Полный в 2 воркера     | `pytest api/unit -n 2 -v -s`         |
| Только slow            | `pytest api/unit -m slow -v -s`      |

---

## Тесты API UnitGroup (Группы ЕИ)

Расположение: `tests/api/unitgroup/` (и smoke в `tests/api/unitgroup/smoke/`).

UnitGroup содержит ссылку на Unit (baseUnit). Тесты UnitGroup создают при необходимости единицу измерения через общие функции из `tests.api.unit` и подставляют её в payload группы.

### Smoke-набор по маркеру `fast` (тесты вне папки smoke)

Тесты с маркером **`fast`**: по одному успешному сценарию на каждый метод API плюс 401. Всего 7 тестов.

**Команда:**

```bash
cd tests
pytest api/unitgroup -m fast -v -s
```

**Что входит:**  
PUT /UnitGroup/CreateOrUpdate (эталонный + 401), GET /UnitGroup, POST /UnitGroup, PUT /UnitGroup/CreateOrUpdateMany, PATCH /UnitGroup/Delete, PATCH /UnitGroup/DeleteMany.

### Полный набор тестов UnitGroup

```bash
cd tests
pytest api/unitgroup -v -s
```

**Только «медленные» тесты:**

```bash
cd tests
pytest api/unitgroup -m slow -v -s
```

### Параллельный запуск (UnitGroup)

Для smoke используйте `--dist loadscope`, чтобы последовательный сценарий внутри модуля не дробился между воркерами.

```bash
cd tests
pytest api/unitgroup -n 2 -v -s
pytest api/unitgroup -n auto -v -s
pytest api/unitgroup/smoke -m smoke -n 2 --dist loadscope -v -s
```

### Шпаргалка команд (UnitGroup)

| Задача                 | Команда (из каталога `tests`)             |
|------------------------|-------------------------------------------|
| Smoke (папка smoke)    | `pytest api/unitgroup/smoke -m smoke -v -s` |
| Smoke в 2 воркера      | `pytest api/unitgroup/smoke -m smoke -n 2 --dist loadscope -v -s` |
| Smoke (маркер fast)    | `pytest api/unitgroup -m fast -v -s`      |
| Полный прогон          | `pytest api/unitgroup -v -s`               |
| Полный в 2 воркера     | `pytest api/unitgroup -n 2 -v -s`         |
| Только slow            | `pytest api/unitgroup -m slow -v -s`      |

---

## Соглашения по тестам

- **Логи и вывод в консоль:** в начале каждого теста — `print("\n  === Тест: <название> ===\n")`; перед каждой проверкой — `_log_check("что проверяется", ожидаемый, фактический)`.
- **Русские названия тестов:** маркер `@pytest.mark.test_name_ru("Название")` — выводятся в итоговой таблице прогона.
- **Файлы проверок (чеклисты):** все таблицы проверок по методам API лежат в папке **`docs/`** в подпапках по сущностям: `docs/unit/`, `docs/unitgroup/`. Для новых сущностей (например, Item) создаётся папка `docs/item/`, куда добавляются файлы `checks_item_<метод>.md`.

---

## Дополнительно

- **Путь к тестам:** из каталога `tests` пути указываются без префикса `tests/` (например, `api/unit`, `api/unit/smoke`). Из корня проекта — `tests/api/unit`, `tests/api -m smoke` и т.д.
- **Про «deselected»:** при запуске с `-m fast` или `-m smoke` pytest отбирает только тесты с этим маркером; остальные помечаются как deselected — это не ошибка.
- **Возможные причины падений:** (1) не задан или не подгружен `.env`; (2) API недоступен по BASE_SERVER_URL; (3) ответ API отличается от схемы в swagger; (4) smoke запущен в 2 потока без `--dist loadscope` (сценарий может разъехаться по воркерам). При падении смотрите трассу (assert или jsonschema).
- **Подробное описание проекта:** см. `ОБЗОР_ПРОЕКТА_API_ТЕСТОВ.txt` и `ОБЗОР_ИЗМЕНЕНИЙ_SMOKE_ТЕСТОВ.txt` в корне проекта.

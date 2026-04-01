## ProcessOperation — checks_smoke

Smoke-поток проверяет CRUD для `ProcessOperation` **без дополнительных API-запросов**.
Все операции удаления/фильтра выполняются **по `integrationId`**. Вложенные позиции (material/equipment/labour/tooling) **не передаются**.

| № | Сценарий | Действие | Ожидаемый результат |
|---:|---|---|---|
| 1 | Smoke: PUT `/ProcessOperation/CreateOrUpdate` — создание одного объекта | Создать объект A минимальным валидным payload | `200`, `added=1`, `errors=0`, в ответе есть `entity.id` |
| 2 | Smoke: PUT `/ProcessOperation/CreateOrUpdate` — обновление одного объекта | Обновить объект A (тот же `integrationId`), изменить `name` | `200`, `updated=1`, результат `Updated` |
| 3 | Smoke: PUT `/ProcessOperation/CreateOrUpdateMany` — создание двух объектов | Создать объекты B1,B2 (массив из 2) | `200`, `added=2`, `errors=0`, в `results` 2 объекта с `entity.id` |
| 4 | Smoke: PUT `/ProcessOperation/CreateOrUpdateMany` — обновление двух объектов | Обновить B1,B2 (те же `integrationId`), изменить `name` | `200`, `updated=2`, `errors=0` |
| 5 | Smoke: GET `/ProcessOperation` — проверка списка | Убедиться, что A,B1,B2 в `items` и `name` как после обновления | `200`, A/B1/B2 найдены по `integrationId`, `name` соответствует |
| 6 | Smoke: PATCH `/ProcessOperation/Delete` — удаление A | Удалить A по `integrationId` | `200/204`, A удалён |
| 7 | Smoke: POST `/ProcessOperation` — фильтр по B1,B2 | Фильтр по `integrationIds=[B1,B2]` | `200`, `items` содержит 2 элемента |
| 8 | Smoke: PATCH `/ProcessOperation/DeleteMany` — удаление B1,B2 | Удалить B1,B2 массивом `{integrationId}` | `200/204`, B1,B2 удалены |
| 9 | Smoke: POST `/ProcessOperation` — финальная чистота | Фильтр по `integrationIds=[A,B1,B2]` | `200`, `items` пустой |

---

### ТК-1. Smoke: PUT /ProcessOperation/CreateOrUpdate — создание одного объекта

**Предусловия:** API доступен, Basic Auth.

**Шаги:**
1. Сформировать payload `ProcessOperation` (A): уникальные `integrationId/number/numberInProcess`, фиксированные ссылки `processSegment/shopFloor/shopFloorArea`, `manufacturingOperationType`.
2. Выполнить `PUT /ProcessOperation/CreateOrUpdate`.
3. Проверить `200`, `count=1`, `added=1`, `errors=0`.
4. Проверить `results[0].entity.id` и сохранить `entity.id` + `integrationId` в state.

**Ожидаемый результат:** `200`, объект A создан.

### ТК-2. Smoke: PUT /ProcessOperation/CreateOrUpdate — обновление одного объекта

**Предусловия:** ТК-1 выполнен (A создан).

**Шаги:**
1. Взять payload A из state.
2. Изменить поле `name`.
3. Выполнить `PUT /ProcessOperation/CreateOrUpdate`.
4. Проверить `200`, `updated=1`, результат `Updated`. Сохранить новое `name` в state.

**Ожидаемый результат:** `200`, объект A обновлён.

### ТК-3. Smoke: PUT /ProcessOperation/CreateOrUpdateMany — создание двух объектов

**Предусловия:** API доступен, Basic Auth.

**Шаги:**
1. Сформировать массив payloads (B1,B2) из 2 объектов с уникальными `integrationId/number/numberInProcess`.
2. Выполнить `PUT /ProcessOperation/CreateOrUpdateMany`.
3. Проверить `200`, `added=2`, `errors=0`, в `results` 2 элемента с `entity.id`.
4. Сохранить `integrationId` B1,B2 и payloads в state.

**Ожидаемый результат:** `200`, B1,B2 созданы.

### ТК-4. Smoke: PUT /ProcessOperation/CreateOrUpdateMany — обновление двух объектов

**Предусловия:** ТК-3 выполнен (B1,B2 созданы).

**Шаги:**
1. Взять payloads B1,B2 из state.
2. Изменить `name` у каждого.
3. Выполнить `PUT /ProcessOperation/CreateOrUpdateMany`.
4. Проверить `200`, `updated=2`, `errors=0`. Сохранить новые `name` в state.

**Ожидаемый результат:** `200`, B1,B2 обновлены.

### ТК-5. Smoke: GET /ProcessOperation — проверка списка

**Предусловия:** ТК-1..ТК-4 выполнены.

**Шаги:**
1. Выполнить `GET /ProcessOperation` (pageSize большой).
2. Проверить `200`.
3. Найти A,B1,B2 по `integrationId`.
4. Проверить, что `name` совпадает с обновлёнными значениями из state.

**Ожидаемый результат:** `200`, A,B1,B2 присутствуют и значения корректны.

### ТК-6. Smoke: PATCH /ProcessOperation/Delete — удаление A

**Предусловия:** A создан (ТК-1).

**Шаги:**
1. Выполнить `PATCH /ProcessOperation/Delete` с телом `{integrationId: A}`.
2. Проверить `200/204` и (если есть) `deleted=1`.

**Ожидаемый результат:** A удалён.

### ТК-7. Smoke: POST /ProcessOperation — фильтр по B1,B2

**Предусловия:** B1,B2 созданы (ТК-3).

**Шаги:**
1. Выполнить `POST /ProcessOperation` с `integrationIds=[B1,B2]`.
2. Проверить `200`, `items` содержит 2 элемента.

**Ожидаемый результат:** B1,B2 возвращаются фильтром.

### ТК-8. Smoke: PATCH /ProcessOperation/DeleteMany — удаление B1,B2

**Предусловия:** B1,B2 созданы (ТК-3).

**Шаги:**
1. Выполнить `PATCH /ProcessOperation/DeleteMany` с массивом `[{integrationId:B1},{integrationId:B2}]`.
2. Проверить `200/204` и (если есть) `deleted=2`.

**Ожидаемый результат:** B1,B2 удалены.

### ТК-9. Smoke: POST /ProcessOperation — финальная проверка чистоты

**Предусловия:** ТК-6 и ТК-8 выполнены.

**Шаги:**
1. Выполнить `POST /ProcessOperation` с `integrationIds=[A,B1,B2]`.
2. Проверить `200`, `items` пустой.

**Ожидаемый результат:** A,B1,B2 не возвращаются, данные очищены.


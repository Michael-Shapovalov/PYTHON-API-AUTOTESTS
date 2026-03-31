# Таблица проверок Smoke: WarehouseBinType (тип складской ячейки)

Последовательный сценарий smoke для API WarehouseBinType: создание одного (A) -> обновление одного (A) -> создание двух (B1, B2) -> обновление пачки (B1, B2) -> GET с проверкой наличия/name -> удаление A по integrationId -> POST-фильтр B1/B2 -> удаление B1/B2 по integrationId -> финальный POST-фильтр чистоты.

| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | Smoke: PUT /WarehouseBinType/CreateOrUpdate — создание одного объекта | PUT с уникальными integrationId/code/name | 200, added==1, errors==0, сохранены id/integrationId A |
| 2 | Smoke: PUT /WarehouseBinType/CreateOrUpdate — обновление одного объекта | PUT того же A по integrationId, изменён name | 200, updated==1 |
| 3 | Smoke: PUT /WarehouseBinType/CreateOrUpdateMany — создание двух объектов | PUT массива B1/B2 с уникальными integrationId | 200, added==2 |
| 4 | Smoke: PUT /WarehouseBinType/CreateOrUpdateMany — обновление двух объектов | PUT того же массива B1/B2 по тем же integrationId | 200, updated==2 |
| 5 | Smoke: GET /WarehouseBinType — в списке есть A, B1, B2 | Поиск по integrationId и проверка обновлённых name | 200; A/B1/B2 найдены |
| 6 | Smoke: PATCH /WarehouseBinType/Delete — удаление объекта A | PATCH Delete с телом { integrationId: integrationId_A } | 200 или 204; при 200 deleted==1 |
| 7 | Smoke: POST /WarehouseBinType — фильтр по B1 и B2 | POST с integrationIds B1/B2 | 200; items ровно 2 |
| 8 | Smoke: PATCH /WarehouseBinType/DeleteMany — удаление B1 и B2 | PATCH DeleteMany с integrationId B1/B2 | 200 или 204; при 200 deleted==2 (или >=1) |
| 9 | Smoke: POST /WarehouseBinType — финальная проверка чистоты | POST по integrationIds A/B1/B2 | 200; items пуст |

---

## Подробные тест-кейсы

### ТК-1. Smoke: PUT /WarehouseBinType/CreateOrUpdate — создание одного объекта (A)

**Предусловия:** API доступен, Basic Auth.

**Шаги:**
1. Сформировать payload с уникальными `integrationId`, `code`, `name` (и `presentation`).
2. Выполнить PUT /WarehouseBinType/CreateOrUpdate.
3. Проверить 200, `count==1`, `added==1`, `errors==0`.
4. Сохранить `id` и `integrationId` объекта A.

**Ожидаемый результат:** Объект A создан, данные сохранены в состоянии smoke.

---

### ТК-2. Smoke: PUT /WarehouseBinType/CreateOrUpdate — обновление одного объекта (A)

**Предусловия:** Выполнен ТК-1.

**Шаги:**
1. Взять payload A и изменить `name`.
2. Выполнить PUT /WarehouseBinType/CreateOrUpdate с тем же `integrationId`.
3. Проверить 200, `updated==1`.

**Ожидаемый результат:** Объект A обновлён.

---

### ТК-3. Smoke: PUT /WarehouseBinType/CreateOrUpdateMany — создание двух объектов (B1, B2)

**Предусловия:** Выполнен ТК-2.

**Шаги:**
1. Сформировать массив из двух payload (B1, B2) с уникальными `integrationId`.
2. Выполнить PUT /WarehouseBinType/CreateOrUpdateMany.
3. Проверить 200, `added==2`, `errors==0`.
4. Сохранить `integrationId` объектов B1 и B2.

**Ожидаемый результат:** B1 и B2 созданы.

---

### ТК-4. Smoke: PUT /WarehouseBinType/CreateOrUpdateMany — обновление двух объектов (B1, B2)

**Предусловия:** Выполнен ТК-3.

**Шаги:**
1. Обновить `name` для B1 и B2.
2. Выполнить PUT /WarehouseBinType/CreateOrUpdateMany по тем же `integrationId`.
3. Проверить 200, `updated==2`.

**Ожидаемый результат:** B1 и B2 обновлены.

---

### ТК-5. Smoke: GET /WarehouseBinType — в списке есть A, B1, B2

**Предусловия:** Известны integrationId A, B1, B2 и ожидаемые name после обновления.

**Шаги:**
1. Выполнить GET /WarehouseBinType.
2. Найти A, B1, B2 по `integrationId`.
3. Сверить `name` c ожидаемыми.

**Ожидаемый результат:** Все три объекта есть в списке с корректными name.

---

### ТК-6. Smoke: PATCH /WarehouseBinType/Delete — удаление объекта A

**Предусловия:** Сохранён `integrationId` объекта A.

**Шаги:**
1. Выполнить PATCH /WarehouseBinType/Delete с телом `{ integrationId: integrationId_A }`.
2. Проверить 200/204; при 200 — `deleted==1`.

**Ожидаемый результат:** A удалён.

---

### ТК-7. Smoke: POST /WarehouseBinType — фильтр по B1 и B2

**Предусловия:** Сохранены `integrationId` B1/B2.

**Шаги:**
1. Выполнить POST /WarehouseBinType с `integrationIds: [B1, B2]`.
2. Проверить 200 и `items` длиной 2.

**Ожидаемый результат:** Возвращаются только B1 и B2.

---

### ТК-8. Smoke: PATCH /WarehouseBinType/DeleteMany — удаление B1 и B2

**Предусловия:** Сохранены `integrationId` B1 и B2.

**Шаги:**
1. Выполнить PATCH /WarehouseBinType/DeleteMany с телом `[{integrationId: B1}, {integrationId: B2}]`.
2. Проверить 200/204; при 200 — `deleted==2` (или `>=1`).

**Ожидаемый результат:** B1 и B2 удалены.

---

### ТК-9. Smoke: POST /WarehouseBinType — финальная проверка чистоты

**Предусловия:** A, B1, B2 удалены.

**Шаги:**
1. Выполнить POST /WarehouseBinType с `integrationIds: [A, B1, B2]`.
2. Проверить `items` пуст.

**Ожидаемый результат:** Удалённые объекты не возвращаются.


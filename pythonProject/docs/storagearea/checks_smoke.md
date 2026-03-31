# Таблица проверок Smoke: StorageArea (зона хранения)

Последовательный сценарий smoke для API StorageArea: создание одного (A) -> обновление одного (A) -> создание двух (B1, B2) -> обновление пачки (B1, B2) -> GET с проверкой наличия/name -> удаление A по integrationId -> POST-фильтр B1/B2 -> удаление B1/B2 по integrationId -> финальный POST-фильтр чистоты.

Для всех payload используется фиксированная ссылка на склад: `warehouse: { id: 63 }` (без дополнительных запросов).

| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | Smoke: PUT /StorageArea/CreateOrUpdate — создание одного объекта | PUT с warehouse{id=63}, уникальными integrationId/code/name | 200, added==1, errors==0 |
| 2 | Smoke: PUT /StorageArea/CreateOrUpdate — обновление одного объекта | PUT того же A по integrationId, изменён name | 200, updated==1 |
| 3 | Smoke: PUT /StorageArea/CreateOrUpdateMany — создание двух объектов | PUT массива B1/B2 по той же warehouse-ссылке | 200, added==2 |
| 4 | Smoke: PUT /StorageArea/CreateOrUpdateMany — обновление двух объектов | PUT того же массива B1/B2 по integrationId | 200, updated==2 |
| 5 | Smoke: GET /StorageArea — в списке есть A, B1, B2 | Поиск A/B1/B2 по integrationId | 200, объекты найдены |
| 6 | Smoke: PATCH /StorageArea/Delete — удаление объекта A | PATCH Delete с телом { integrationId: integrationId_A } | 200/204; при 200 deleted==1 |
| 7 | Smoke: POST /StorageArea — фильтр по B1 и B2 | POST с integrationIds B1/B2 | 200, items ровно 2 |
| 8 | Smoke: PATCH /StorageArea/DeleteMany — удаление B1 и B2 | PATCH DeleteMany с integrationId B1/B2 | 200/204; при 200 deleted==2 (или >=1) |
| 9 | Smoke: POST /StorageArea — финальная проверка чистоты | POST по integrationIds A/B1/B2 | 200, items пуст |

---

## Подробные тест-кейсы

### ТК-1. Smoke: PUT /StorageArea/CreateOrUpdate — создание одного объекта (A)

**Предусловия:** API доступен, Basic Auth; Warehouse с `id=63` существует.

**Шаги:**
1. Сформировать payload: `warehouse: {id:63}`, уникальные `integrationId/code/name`.
2. Выполнить PUT /StorageArea/CreateOrUpdate.
3. Проверить 200, `count==1`, `added==1`, `errors==0`.
4. Сохранить `id` и `integrationId` объекта A.

**Ожидаемый результат:** Объект A создан.

---

### ТК-2. Smoke: PUT /StorageArea/CreateOrUpdate — обновление одного объекта (A)

**Предусловия:** Выполнен ТК-1.

**Шаги:**
1. Обновить `name` в payload A.
2. Выполнить PUT /StorageArea/CreateOrUpdate по тому же `integrationId`.
3. Проверить 200 и `updated==1`.

**Ожидаемый результат:** A обновлён.

---

### ТК-3. Smoke: PUT /StorageArea/CreateOrUpdateMany — создание двух объектов (B1, B2)

**Предусловия:** Выполнен ТК-2.

**Шаги:**
1. Сформировать два payload B1/B2 с `warehouse: {id:63}`.
2. Выполнить PUT /StorageArea/CreateOrUpdateMany.
3. Проверить 200, `added==2`, `errors==0`.
4. Сохранить `integrationId` B1/B2.

**Ожидаемый результат:** B1/B2 созданы.

---

### ТК-4. Smoke: PUT /StorageArea/CreateOrUpdateMany — обновление двух объектов (B1, B2)

**Предусловия:** Выполнен ТК-3.

**Шаги:**
1. Обновить `name` для B1/B2.
2. Выполнить PUT /StorageArea/CreateOrUpdateMany по тем же `integrationId`.
3. Проверить 200, `updated==2`.

**Ожидаемый результат:** B1/B2 обновлены.

---

### ТК-5. Smoke: GET /StorageArea — в списке есть A, B1, B2

**Предусловия:** Сохранены integrationId A/B1/B2.

**Шаги:**
1. Выполнить GET /StorageArea.
2. Найти объекты A/B1/B2 по `integrationId`.
3. Сверить обновлённые `name`.

**Ожидаемый результат:** Все объекты найдены.

---

### ТК-6. Smoke: PATCH /StorageArea/Delete — удаление объекта A

**Предусловия:** Сохранён `integrationId` A.

**Шаги:**
1. Выполнить PATCH /StorageArea/Delete с `{ integrationId: integrationId_A }`.
2. Проверить 200/204; при 200 — `deleted==1`.

**Ожидаемый результат:** A удалён.

---

### ТК-7. Smoke: POST /StorageArea — фильтр по B1 и B2

**Предусловия:** Сохранены `integrationId` B1/B2.

**Шаги:**
1. Выполнить POST /StorageArea с `integrationIds: [B1, B2]`.
2. Проверить 200 и `items` длиной 2.

**Ожидаемый результат:** Вернулись B1 и B2.

---

### ТК-8. Smoke: PATCH /StorageArea/DeleteMany — удаление B1 и B2

**Предусловия:** Сохранены `integrationId` B1/B2.

**Шаги:**
1. Выполнить PATCH /StorageArea/DeleteMany с `[{integrationId:B1},{integrationId:B2}]`.
2. Проверить 200/204; при 200 — `deleted==2` (или `>=1`).

**Ожидаемый результат:** B1 и B2 удалены.

---

### ТК-9. Smoke: POST /StorageArea — финальная проверка чистоты

**Предусловия:** A, B1, B2 удалены.

**Шаги:**
1. Выполнить POST /StorageArea с `integrationIds: [A, B1, B2]`.
2. Проверить, что `items` пуст.

**Ожидаемый результат:** Удалённые объекты не возвращаются.


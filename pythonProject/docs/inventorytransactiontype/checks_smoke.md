# Таблица проверок Smoke: InventoryTransactionType (типы складских операций)

Последовательный сценарий smoke для API InventoryTransactionType: создание одного (A) → обновление одного (A, поле name) → создание двух (B1, B2) → обновление пачки (B1, B2, поле name) → GET с проверкой наличия и значений полей после обновления → удаление одного → проверка фильтра → удаление двух → финальная проверка чистоты через POST-фильтр. Для smoke фиксируются значения enum: `actionType=0` (ReceiptIntoInventory), `sourceType=0` (Inventory), `isDefault=false`, все `isFor*` = false.

| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | Smoke: PUT /InventoryTransactionType/CreateOrUpdate — создание одного объекта | PUT с минимально валидным payload (integrationId, code, name, isDefault, actionType, sourceType, isFor*) | 200, count==1, added==1, errors==0, results[0].entity.id; сохранение id, integrationId и payload объекта A |
| 2 | Smoke: PUT /InventoryTransactionType/CreateOrUpdate — обновление одного объекта | PUT того же объекта A (тот же integrationId), поле name изменено | 200, result \"Updated\", updated==1; сохранение ожидаемого значения name для проверки в GET |
| 3 | Smoke: PUT /InventoryTransactionType/CreateOrUpdateMany — создание двух объектов | PUT с массивом из двух RestInventoryTransactionType | 200, added==2, errors==0, в results два элемента с entity.id; сохранение id, integrationId и массив payloads объектов B1, B2 |
| 4 | Smoke: PUT /InventoryTransactionType/CreateOrUpdateMany — обновление двух объектов | PUT того же массива (те же integrationId), у каждого изменено поле name | 200, updated==2, errors==0; сохранение списка обновлённых name для B1, B2 |
| 5 | Smoke: GET /InventoryTransactionType — в списке есть A, B1, B2 и поля после обновления | GET /InventoryTransactionType; поиск по integrationId; проверка поля name | 200, items — массив; A, B1, B2 найдены; name у каждой записи совпадает с сохранённым при обновлении |
| 6 | Smoke: PATCH /InventoryTransactionType/Delete — удаление объекта A | PATCH /InventoryTransactionType/Delete с телом { integrationId: integrationId_A } | 200 или 204; при 200 — deleted==1 |
| 7 | Smoke: POST /InventoryTransactionType — фильтр по B1 и B2 | POST /InventoryTransactionType с телом { pageNum: 0, pageSize: 100, integrationIds: [B1, B2], noCount: false } | 200, в items ровно 2 элемента |
| 8 | Smoke: PATCH /InventoryTransactionType/DeleteMany — удаление B1 и B2 | PATCH /InventoryTransactionType/DeleteMany с телом [ { integrationId: integrationId_B1 }, { integrationId: integrationId_B2 } ] | 200 или 204; при 200 — deleted==2 (или >= 1) |
| 9 | Smoke: POST /InventoryTransactionType — финальная проверка чистоты | POST /InventoryTransactionType с фильтром по integrationIds A, B1, B2; items пуст | 200; items пуст, объекты A, B1, B2 не возвращаются |

---

## Подробные тест-кейсы

### ТК-1. Smoke: PUT /InventoryTransactionType/CreateOrUpdate — создание одного объекта (A)

**Предусловия:** API доступен, Basic Auth.

**Шаги:**
1. Сформировать payload RestInventoryTransactionType: integrationId, code, name (уникальные), isDefault=false, actionType=0, sourceType=0, isFor* = false.
2. Выполнить PUT /InventoryTransactionType/CreateOrUpdate.
3. Проверить 200, count==1, added==1, errors==0.
4. Проверить results[0].entity.id; сохранить id, integrationId и payload.

**Ожидаемый результат:** 200; объект A создан; состояние сохранено.

---

### ТК-2. Smoke: PUT /InventoryTransactionType/CreateOrUpdate — обновление одного объекта (A)

**Предусловия:** Выполнен ТК-1.

**Шаги:**
1. Взять payload A, изменить name (например, + \" (обновлено)\" в пределах 250 символов).
2. Выполнить PUT /InventoryTransactionType/CreateOrUpdate.
3. Проверить 200, result \"Updated\", updated==1.
4. Сохранить новое значение name для проверки в GET.

**Ожидаемый результат:** 200; объект обновлён.

---

### ТК-3. Smoke: PUT /InventoryTransactionType/CreateOrUpdateMany — создание двух объектов (B1, B2)

**Предусловия:** Выполнен ТК-2.

**Шаги:**
1. Сформировать массив из двух RestInventoryTransactionType с уникальными integrationId/code/name и теми же enum/флагами.
2. Выполнить PUT /InventoryTransactionType/CreateOrUpdateMany.
3. Проверить 200, added==2, errors==0, results содержит 2 элемента с entity.id.
4. Сохранить id/integrationId и payloads B1/B2.

**Ожидаемый результат:** 200; B1/B2 созданы.

---

### ТК-4. Smoke: PUT /InventoryTransactionType/CreateOrUpdateMany — обновление двух объектов (B1, B2)

**Предусловия:** Выполнен ТК-3.

**Шаги:**
1. Взять payloads B1/B2, изменить name у каждого.
2. Выполнить PUT /InventoryTransactionType/CreateOrUpdateMany.
3. Проверить 200, updated==2, errors==0.
4. Сохранить ожидаемые name для B1/B2.

**Ожидаемый результат:** 200; B1/B2 обновлены.

---

### ТК-5. Smoke: GET /InventoryTransactionType — в списке есть A, B1, B2 и поля после обновления

**Предусловия:** Сохранены integrationId и ожидаемые name.

**Шаги:**
1. Выполнить GET /InventoryTransactionType (pageSize достаточно большой, например 5000).
2. Проверить 200, items — массив.
3. Найти A/B1/B2 по integrationId.
4. Проверить name совпадает с ожидаемым.

**Ожидаемый результат:** 200; все объекты найдены; name корректный.

---

### ТК-6. Smoke: PATCH /InventoryTransactionType/Delete — удаление объекта A

**Предусловия:** Сохранён integrationId A.

**Шаги:**
1. Выполнить PATCH /InventoryTransactionType/Delete с телом { integrationId: integrationId_A }.
2. Проверить 200 или 204; при 200 и наличии тела — deleted==1.

**Ожидаемый результат:** A удалён.

---

### ТК-7. Smoke: POST /InventoryTransactionType — фильтр по B1 и B2

**Предусловия:** Сохранены integrationId B1/B2; A удалён.

**Шаги:**
1. Выполнить POST /InventoryTransactionType с телом { integrationIds: [B1, B2], pageNum:0, pageSize:100, noCount:false }.
2. Проверить 200; items содержит ровно 2 элемента.

**Ожидаемый результат:** В фильтре только B1/B2.

---

### ТК-8. Smoke: PATCH /InventoryTransactionType/DeleteMany — удаление B1 и B2

**Предусловия:** Сохранены integrationId B1/B2.

**Шаги:**
1. Выполнить PATCH /InventoryTransactionType/DeleteMany с телом [ { integrationId: integrationId_B1 }, { integrationId: integrationId_B2 } ].
2. Проверить 200 или 204; при 200 — deleted==2 (или >=1).

**Ожидаемый результат:** B1/B2 удалены.

---

### ТК-9. Smoke: POST /InventoryTransactionType — финальная проверка чистоты

**Предусловия:** A, B1, B2 удалены.

**Шаги:**
1. Выполнить POST /InventoryTransactionType с фильтром по integrationIds A, B1, B2.
2. Проверить 200; items пуст.

**Ожидаемый результат:** items пуст (удалённые объекты не возвращаются).


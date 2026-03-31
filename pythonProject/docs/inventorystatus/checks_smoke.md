# Таблица проверок Smoke: InventoryStatus (статусы запаса)

Последовательный сценарий smoke для API InventoryStatus: создание одного (A) → обновление одного (A, поле name) → создание двух (B1, B2) → обновление пачки (B1, B2, поле name) → GET с проверкой наличия и значений полей после обновления → удаление одного → проверка фильтра → удаление двух → финальная проверка чистоты через POST-фильтр.

| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | Smoke: PUT /InventoryStatus/CreateOrUpdate — создание одного объекта | PUT с минимально валидным payload (integrationId, code, name + boolean flags) | 200, count==1, added==1, errors==0, results[0].entity.id; сохранение id, integrationId и payload объекта A |
| 2 | Smoke: PUT /InventoryStatus/CreateOrUpdate — обновление одного объекта | PUT того же объекта A (тот же integrationId), поле name изменено | 200, result \"Updated\", updated==1; сохранение ожидаемого name для проверки в GET |
| 3 | Smoke: PUT /InventoryStatus/CreateOrUpdateMany — создание двух объектов | PUT с массивом из двух RestInventoryStatus | 200, added==2, errors==0, в results два элемента с entity.id; сохранение id, integrationId и payloads B1/B2 |
| 4 | Smoke: PUT /InventoryStatus/CreateOrUpdateMany — обновление двух объектов | PUT того же массива (те же integrationId), у каждого изменено поле name | 200, updated==2, errors==0; сохранение списка обновлённых name |
| 5 | Smoke: GET /InventoryStatus — в списке есть A, B1, B2 и поля после обновления | GET /InventoryStatus; поиск по integrationId; проверка name | 200; A, B1, B2 найдены; name совпадает с ожидаемым |
| 6 | Smoke: PATCH /InventoryStatus/Delete — удаление объекта A | PATCH /InventoryStatus/Delete с телом { integrationId: integrationId_A } | 200 или 204; при 200 — deleted==1 |
| 7 | Smoke: POST /InventoryStatus — фильтр по B1 и B2 | POST /InventoryStatus с телом { integrationIds: [B1, B2], pageNum:0, pageSize:100 } | 200; items ровно 2 элемента |
| 8 | Smoke: PATCH /InventoryStatus/DeleteMany — удаление B1 и B2 | PATCH /InventoryStatus/DeleteMany с телом [ {integrationId:integrationId_B1}, {integrationId:integrationId_B2} ] | 200 или 204; при 200 — deleted==2 (или >=1) |
| 9 | Smoke: POST /InventoryStatus — финальная проверка чистоты | POST /InventoryStatus с фильтром по integrationIds A, B1, B2; items пуст | 200; items пуст |

---

## Подробные тест-кейсы

### ТК-1. Smoke: PUT /InventoryStatus/CreateOrUpdate — создание одного объекта (A)

**Предусловия:** API доступен, Basic Auth.

**Шаги:**
1. Сформировать payload RestInventoryStatus: integrationId, code, name (уникальные) + обязательные boolean‑поля (isAllowPicking, isAvailableStock, isForWarehouse, isForWarehouseBin, isForLot, isForSerialNumber).
2. Выполнить PUT /InventoryStatus/CreateOrUpdate.
3. Проверить 200, count==1, added==1, errors==0.
4. Проверить results[0].entity.id; сохранить id, integrationId и payload.

**Ожидаемый результат:** 200; объект A создан.

---

### ТК-2. Smoke: PUT /InventoryStatus/CreateOrUpdate — обновление одного объекта (A)

**Предусловия:** Выполнен ТК-1.

**Шаги:**
1. Взять payload A, изменить name (например, + \" (обновлено)\").
2. Выполнить PUT /InventoryStatus/CreateOrUpdate.
3. Проверить 200, result \"Updated\", updated==1.
4. Сохранить новое name.

**Ожидаемый результат:** 200; объект обновлён.

---

### ТК-3…ТК-9

Тест‑кейсы 3–9 полностью аналогичны `docs/unit/checks_smoke.md` и `docs/item/checks_smoke.md`:\n\n- **ТК‑3**: CreateOrUpdateMany (создание B1/B2)\n- **ТК‑4**: CreateOrUpdateMany (обновление B1/B2)\n- **ТК‑5**: GET /InventoryStatus (проверка наличия и name)\n- **ТК‑6**: PATCH Delete (удаление A)\n- **ТК‑7**: POST filter (проверка B1/B2)\n- **ТК‑8**: PATCH DeleteMany (удаление B1/B2)\n- **ТК‑9**: финальный POST filter (items пуст)\n+

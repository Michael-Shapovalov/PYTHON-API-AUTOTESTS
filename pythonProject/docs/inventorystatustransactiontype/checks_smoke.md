# Таблица проверок Smoke: InventoryStatusTransactionType (тип складской операции для статуса запаса)

Последовательный сценарий smoke для API InventoryStatusTransactionType: создание одного (A) → обновление одного (A, переключение `isNotAllowed`) → создание двух (B1, B2) → обновление пачки (B1, B2) → GET с проверкой наличия → удаление одного → проверка фильтра → удаление двух → финальная проверка чистоты через POST-фильтр.\n\nДля связей используются фиксированные существующие id из БД:\n\n- `inventoryStatus: { id: <InventoryStatusId> }`\n- `inventoryTransactionType: { id: <InventoryTransactionTypeId> }`\n\nИх значения задаются в фикстурах smoke‑теста.\n+
| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdate — создание одного объекта | PUT с payload (integrationId, inventoryStatus{id}, inventoryTransactionType{id}, isNotAllowed=false) | 200, count==1, added==1, errors==0, results[0].entity.id; сохранение id, integrationId и payload объекта A |
| 2 | Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdate — обновление одного объекта | PUT того же объекта A (тот же integrationId), переключение isNotAllowed | 200, result \"Updated\", updated==1 |
| 3 | Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdateMany — создание двух объектов | PUT с массивом из двух RestInventoryStatusTransactionType | 200, added==2, errors==0, в results два элемента с entity.id; сохранение id, integrationId и payloads B1/B2 |
| 4 | Smoke: PUT /InventoryStatusTransactionType/CreateOrUpdateMany — обновление двух объектов | PUT того же массива (те же integrationId), переключение isNotAllowed | 200, updated==2, errors==0 |
| 5 | Smoke: GET /InventoryStatusTransactionType — в списке есть A, B1, B2 | GET; поиск по integrationId | 200; A, B1, B2 найдены |
| 6 | Smoke: PATCH /InventoryStatusTransactionType/Delete — удаление объекта A | PATCH Delete с телом { integrationId: integrationId_A } | 200 или 204; при 200 — deleted==1 |
| 7 | Smoke: POST /InventoryStatusTransactionType — фильтр по B1 и B2 | POST filter по integrationIds B1/B2 | 200; items ровно 2 элемента |
| 8 | Smoke: PATCH /InventoryStatusTransactionType/DeleteMany — удаление B1 и B2 | PATCH DeleteMany с телом [ { integrationId: integrationId_B1 }, { integrationId: integrationId_B2 } ] | 200 или 204; при 200 — deleted==2 (или >=1) |
| 9 | Smoke: POST /InventoryStatusTransactionType — финальная проверка чистоты | POST filter по integrationIds A, B1, B2; items пуст | 200; items пуст |
\n---\n\n## Подробные тест-кейсы\n\nТК‑1…ТК‑9 аналогичны структуре smoke‑документации `docs/personnel/checks_smoke.md`, но с отличием:\n\n- вместо проверки поля `name` в GET мы проверяем только **наличие объектов по integrationId**, потому что у связующей сущности поля `name/code` могут отсутствовать;\n- при обновлении вместо изменения `name` мы **переключаем `isNotAllowed`**.\n+

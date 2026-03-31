# Таблица проверок Smoke: ManufacturingBillTemplate (шаблоны спецификаций)

Последовательный сценарий smoke для API ManufacturingBillTemplate:
создание одного (A) → обновление одного (A, поле name) → создание двух (B1, B2) → обновление пачки (B1, B2, поле name) → GET с проверкой наличия и name → удаление по `integrationId` → POST-фильтр → удаление пачки по `integrationId` → финальная проверка чистоты.

| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdate — создание одного объекта | PUT минимально валидного payload (integrationId, code, name, presentation, isDefault, positionNumberingStep, status) | 200; added==1; сохранение id и integrationId объекта A |
| 2 | Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdate — обновление одного объекта | PUT того же объекта A (тот же integrationId), поле name изменено | 200; result "Updated"; updated==1 |
| 3 | Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdateMany — создание двух объектов | PUT массива из двух payload | 200; added==2; сохранение id и integrationId для B1/B2 |
| 4 | Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdateMany — обновление двух объектов | PUT массива B1/B2 (те же integrationId), поле name изменено | 200; updated==2 |
| 5 | Smoke: GET /ManufacturingBillTemplate — в списке есть A, B1, B2 | GET и поиск по integrationId; проверка name после обновления | 200; items содержит A/B1/B2; name совпадает |
| 6 | Smoke: PATCH /ManufacturingBillTemplate/Delete — удаление объекта A | PATCH Delete с телом { integrationId: integrationId_A } | 200 или 204; при 200 — deleted==1 |
| 7 | Smoke: POST /ManufacturingBillTemplate — фильтр по B1 и B2 | POST фильтр по integrationIds B1/B2 | 200; items ровно 2 элемента |
| 8 | Smoke: PATCH /ManufacturingBillTemplate/DeleteMany — удаление B1 и B2 | PATCH DeleteMany по integrationId | 200 или 204; при 200 — deleted==2 (или >=1) |
| 9 | Smoke: POST /ManufacturingBillTemplate — финальная проверка чистоты | POST фильтр по integrationIds A/B1/B2; items пуст | 200; items пуст |

---

## Подробные тест-кейсы

### ТК-1. Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdate — создание одного объекта (A)

**Предусловия:** API доступен, Basic Auth.

**Шаги:**
1. Сформировать payload RestManufacturingBillTemplate:
   - уникальные `integrationId`, `code`, `name`;
   - `presentation = <Code> <Name>`;
   - `isDefault=false`;
   - `positionNumberingStep=10`;
   - `status=0` (Draft).
2. Выполнить PUT /ManufacturingBillTemplate/CreateOrUpdate с Basic Auth.
3. Проверить код 200, `count==1`, `added==1`, `errors==0`.
4. Проверить наличие `results[0].entity.id`; сохранить `id` и `integrationId` объекта A.

**Ожидаемый результат:** 200; объект A создан; `id` и `integrationId` сохранены для следующих шагов.

---

### ТК-2. Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdate — обновление одного объекта (A)

**Предусловия:** Выполнен ТК-1 (есть payload A).

**Шаги:**
1. Взять сохранённый payload A, скопировать и изменить поле `name` (суффикс “ (обновлено)”).
2. Обновить `presentation` под формат `<Code> <Name>`.
3. Выполнить PUT /ManufacturingBillTemplate/CreateOrUpdate с Basic Auth.
4. Проверить `result=="Updated"` и `updated==1`.
5. Сохранить ожидаемое значение `name` для проверки в GET.

**Ожидаемый результат:** 200; объект A обновлён; ожидаемый `name` сохранён.

---

### ТК-3. Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdateMany — создание двух объектов (B1, B2)

**Предусловия:** Выполнен ТК-2.

**Шаги:**
1. Сформировать массив из двух payload B1/B2 с разными `integrationId`/`code`/`name`.
2. Выполнить PUT /ManufacturingBillTemplate/CreateOrUpdateMany с Basic Auth.
3. Проверить `added==2`, `errors==0`.
4. Сохранить `id` и `integrationId` объектов B1/B2, а также payloads для B1/B2.

**Ожидаемый результат:** 200; объекты B1 и B2 созданы.

---

### ТК-4. Smoke: PUT /ManufacturingBillTemplate/CreateOrUpdateMany — обновление двух объектов (B1, B2)

**Предусловия:** Выполнен ТК-3 (есть payloads B1/B2).

**Шаги:**
1. Для каждого payload B1/B2 изменить `name` (суффикс “ (обновлено)”).
2. Пересчитать `presentation` под `<Code> <Name>`.
3. Выполнить PUT /ManufacturingBillTemplate/CreateOrUpdateMany с Basic Auth.
4. Проверить `updated==2`, `errors==0`.
5. Сохранить ожидаемые значения `name` для B1 и B2 (в том же порядке).

**Ожидаемый результат:** 200; объекты B1 и B2 обновлены.

---

### ТК-5. Smoke: GET /ManufacturingBillTemplate — в списке есть A, B1, B2 и fields после обновления

**Предусловия:** Сохранены `integrationId` объектов и ожидаемые значения `name` после обновления.

**Шаги:**
1. Выполнить GET /ManufacturingBillTemplate с Basic Auth (pageSize достаточно большой, например 5000).
2. Проверить код 200 и наличие поля `items`.
3. Найти в `items` объекты по `integrationId` для A, B1, B2.
4. Проверить, что `name` совпадает с ожидаемыми значениями.

**Ожидаемый результат:** 200; `items` содержит A/B1/B2; `name` корректный.

---

### ТК-6. Smoke: PATCH /ManufacturingBillTemplate/Delete — удаление объекта A

**Предусловия:** Сохранён `integrationId` объекта A.

**Шаги:**
1. Выполнить PATCH /ManufacturingBillTemplate/Delete с Basic Auth и телом { integrationId: integrationId_A }.
2. Проверить код 200 или 204; при 200 и наличии тела — `deleted==1`.

**Ожидаемый результат:** 200 или 204; объект A удалён.

---

### ТК-7. Smoke: POST /ManufacturingBillTemplate — фильтр по B1 и B2

**Предусловия:** Объект A удалён; сохранены `integrationId` для B1 и B2.

**Шаги:**
1. Выполнить POST /ManufacturingBillTemplate с Basic Auth и телом { pageNum: 0, pageSize: 100, integrationIds: [integrationId_B1, integrationId_B2], noCount: false }.
2. Проверить код 200; в `items` ровно 2 элемента.

**Ожидаемый результат:** 200; в `items` только B1 и B2.

---

### ТК-8. Smoke: PATCH /ManufacturingBillTemplate/DeleteMany — удаление B1 и B2

**Предусловия:** Сохранены `integrationId` объектов B1 и B2.

**Шаги:**
1. Выполнить PATCH /ManufacturingBillTemplate/DeleteMany с Basic Auth и телом [ { integrationId: integrationId_B1 }, { integrationId: integrationId_B2 } ].
2. Проверить код 200 или 204; при 200 — `deleted==2` (или >=1).

**Ожидаемый результат:** 200 или 204; объекты B1 и B2 удалены.

---

### ТК-9. Smoke: POST /ManufacturingBillTemplate — финальная проверка чистоты

**Предусловия:** Все созданные в сценарии объекты (A, B1, B2) удалены.

**Шаги:**
1. Выполнить POST /ManufacturingBillTemplate с Basic Auth и телом { pageNum: 0, pageSize: 100, integrationIds: [integrationId_A, integrationId_B1, integrationId_B2], noCount: false }.
2. Проверить, что `items` пустой.

**Ожидаемый результат:** 200; `items` пуст (A/B1/B2 не возвращаются).


# Таблица проверок GET /UnitGroup (Получение всех объектов)

| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | GET /UnitGroup: успешный ответ 200 и структура ответа | Создать одну Unit и одну UnitGroup через PUT, затем GET /UnitGroup с auth (pageNum=0, pageSize=0) | 200, тело JSON с полями pageNum, totalPages, pageSize, total, hasPreviousPage, hasNextPage, items; items — массив; созданная группа в списке по integrationId |
| 2 | GET /UnitGroup: соответствие ответа схеме PaginatedListOfRestUnitGroup | После создания группы через PUT — GET с auth, валидация ответа по схеме из swagger | 200, jsonschema.validate не выбрасывает исключение |
| 3 | GET /UnitGroup: пагинация — pageSize ограничивает число записей | После PUT одной группы — GET с pageNum=0, pageSize=5 | 200, len(items) <= 5, в ответе pageSize=5 |
| 4 | GET /UnitGroup: запрос без авторизации — 401 | GET /UnitGroup без заголовка Authorization | 401 Unauthorized |

---

## Подробные тест-кейсы

### ТК-1. GET /UnitGroup: успешный ответ 200 и структура ответа

**Предусловия:** API доступен; в .env заданы BASE_SERVER_URL, ADMIN_USERNAME, ADMIN_PASSWORD.

**Шаги:**
1. Создать одну единицу измерения (Unit) через PUT /Unit/CreateOrUpdate с уникальными code, name, integrationId, acronym.
2. Создать одну группу ЕИ (UnitGroup) через PUT /UnitGroup/CreateOrUpdate с уникальными code, name, integrationId и baseUnit: { id: &lt;id созданной Unit&gt; }.
3. Выполнить GET /UnitGroup с Basic Auth, параметры: pageNum=0, pageSize=0 (или без пагинации по контракту).
4. Проверить код ответа и наличие в теле полей: pageNum, totalPages, pageSize, total, hasPreviousPage, hasNextPage, items.
5. Убедиться, что items — массив.
6. Найти в items элемент с integrationId, равным integrationId созданной группы.

**Ожидаемый результат:** HTTP 200; в ответе присутствуют все перечисленные поля; items — массив; созданная группа найдена в items по integrationId.

---

### ТК-2. GET /UnitGroup: соответствие ответа схеме PaginatedListOfRestUnitGroup

**Предусловия:** Выполнены шаги 1–2 из ТК-1 (созданы Unit и UnitGroup).

**Шаги:**
1. Выполнить GET /UnitGroup с Basic Auth.
2. Загрузить схему PaginatedListOfRestUnitGroup из swagger.json (с разрешением $ref и allOf).
3. Выполнить jsonschema.validate(instance=response.json(), schema=schema).

**Ожидаемый результат:** HTTP 200; валидация проходит без исключения (ответ соответствует схеме).

---

### ТК-3. GET /UnitGroup: пагинация — pageSize ограничивает число записей

**Предусловия:** В системе есть хотя бы одна группа (создана в фикстуре).

**Шаги:**
1. Выполнить GET /UnitGroup с Basic Auth, параметры: pageNum=0, pageSize=5.
2. Проверить код ответа и что длина массива items не превышает 5.
3. Проверить, что в ответе поле pageSize равно 5.

**Ожидаемый результат:** HTTP 200; len(items) <= 5; в ответе pageSize=5.

---

### ТК-4. GET /UnitGroup: запрос без авторизации — 401

**Предусловия:** API доступен.

**Шаги:**
1. Выполнить GET /UnitGroup без заголовка Authorization (без Basic Auth).

**Ожидаемый результат:** HTTP 401 Unauthorized.

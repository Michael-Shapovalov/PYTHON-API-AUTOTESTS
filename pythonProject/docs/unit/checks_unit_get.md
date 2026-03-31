# Таблица проверок GET /Unit (Получение всех объектов)

| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | GET /Unit: успешный ответ 200 и структура ответа | Создать одну единицу через PUT, затем GET /Unit с auth (pageNum=0, pageSize=0) | 200, тело JSON с полями pageNum, totalPages, pageSize, total, hasPreviousPage, hasNextPage, items; items — массив; созданная единица в списке по integrationId |
| 2 | GET /Unit: соответствие ответа схеме PaginatedListOfRestUnit | После создания единицы через PUT — GET с auth, валидация ответа по схеме из swagger | 200, jsonschema.validate не выбрасывает исключение |
| 3 | GET /Unit: пагинация — pageSize ограничивает число записей | После PUT одной единицы — GET с pageNum=0, pageSize=5 | 200, len(items) <= 5, в ответе pageSize=5 |
| 4 | GET /Unit: запрос без авторизации — 401 | GET /Unit без заголовка Authorization (создание данных не требуется) | 401 Unauthorized |

---

## Подробные тест-кейсы

### ТК-1. GET /Unit: успешный ответ 200 и структура ответа

**Предусловия:** API доступен; в .env заданы BASE_SERVER_URL, ADMIN_USERNAME, ADMIN_PASSWORD.

**Шаги:**
1. Создать одну единицу измерения через PUT /Unit/CreateOrUpdate с уникальными code, name, integrationId, acronym.
2. Выполнить GET /Unit с Basic Auth, параметры: pageNum=0, pageSize=0 (или без пагинации по контракту).
3. Проверить код ответа и наличие в теле полей: pageNum, totalPages, pageSize, total, hasPreviousPage, hasNextPage, items.
4. Убедиться, что items — массив.
5. Найти в items элемент с integrationId, равным integrationId созданной единицы.

**Ожидаемый результат:** HTTP 200; в ответе присутствуют все перечисленные поля; items — массив; созданная единица найдена в items по integrationId.

---

### ТК-2. GET /Unit: соответствие ответа схеме PaginatedListOfRestUnit

**Предусловия:** Создана одна единица через PUT (фикстура или предыдущий шаг).

**Шаги:**
1. Выполнить GET /Unit с Basic Auth.
2. Загрузить схему PaginatedListOfRestUnit из swagger.json (с разрешением $ref и allOf).
3. Выполнить jsonschema.validate(instance=response.json(), schema=schema).

**Ожидаемый результат:** HTTP 200; валидация проходит без исключения (ответ соответствует схеме).

---

### ТК-3. GET /Unit: пагинация — pageSize ограничивает число записей

**Предусловия:** В системе есть хотя бы одна единица (создана в фикстуре).

**Шаги:**
1. Выполнить GET /Unit с Basic Auth, параметры: pageNum=0, pageSize=5.
2. Проверить код ответа и что длина массива items не превышает 5.
3. Проверить, что в ответе поле pageSize равно 5.

**Ожидаемый результат:** HTTP 200; len(items) <= 5; в ответе pageSize=5.

---

### ТК-4. GET /Unit: запрос без авторизации — 401

**Предусловия:** API доступен.

**Шаги:**
1. Выполнить GET /Unit без заголовка Authorization (без Basic Auth).

**Ожидаемый результат:** HTTP 401 Unauthorized.

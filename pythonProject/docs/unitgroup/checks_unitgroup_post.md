# Проверки POST /UnitGroup (получение объектов по фильтру)

| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | POST /UnitGroup: успешный ответ 200 и структура ответа | После создания Unit и UnitGroup — POST /UnitGroup с фильтром (integrationIds, pageNum, pageSize) | 200, поля пагинации и items; созданная группа в items по integrationId |
| 2 | POST /UnitGroup: соответствие ответа схеме PaginatedListOfRestUnitGroup | Валидация ответа по jsonschema из swagger | Ответ проходит jsonschema.validate |
| 3 | POST /UnitGroup: запрос без авторизации — 401 | POST без auth | 401 |
| 4 | POST /UnitGroup: пустой body — 400 | POST с телом {} | 400 или 200 (по контракту) |
| 5 | POST /UnitGroup: невалидный JSON в теле — 400 | POST с обрезанным JSON | 400, 415 или 422 |
| 6 | POST /UnitGroup: ids не массив — 400 | ids передано строкой вместо массива | 400 или 200 с валидным ответом |

---

## Подробные тест-кейсы

### ТК-1. POST /UnitGroup: успешный ответ 200 и структура ответа

**Предусловия:** Созданы одна Unit и одна UnitGroup через PUT.

**Шаги:**
1. Сформировать тело запроса: pageNum=0, pageSize=100, integrationIds=[integrationId созданной группы], noCount=false.
2. Выполнить POST /UnitGroup с Basic Auth и этим телом.
3. Проверить код ответа 200.
4. Проверить наличие в ответе полей: pageNum, totalPages, pageSize, total, hasPreviousPage, hasNextPage, items.
5. Убедиться, что items — массив и в нём есть группа с указанным integrationId.

**Ожидаемый результат:** HTTP 200; структура ответа соответствует пагинации; созданная группа присутствует в items.

---

### ТК-2. POST /UnitGroup: соответствие ответа схеме PaginatedListOfRestUnitGroup

**Предусловия:** Есть созданная UnitGroup (фикстура).

**Шаги:**
1. Выполнить POST /UnitGroup с телом { pageNum: 0, pageSize: 0 } и Basic Auth.
2. Загрузить схему PaginatedListOfRestUnitGroup из swagger.
3. Выполнить jsonschema.validate(instance=response.json(), schema=schema).

**Ожидаемый результат:** HTTP 200; валидация схемы проходит без ошибки.

---

### ТК-3. POST /UnitGroup: запрос без авторизации — 401

**Шаги:**
1. Выполнить POST /UnitGroup с телом { pageNum: 0, pageSize: 0 } без заголовка Authorization.

**Ожидаемый результат:** HTTP 401 Unauthorized.

---

### ТК-4. POST /UnitGroup: пустой body — 400

**Шаги:**
1. Выполнить POST /UnitGroup с Basic Auth и телом {}.

**Ожидаемый результат:** HTTP 400 или HTTP 200 (если API допускает пустой body).

---

### ТК-5. POST /UnitGroup: невалидный JSON в теле — 400

**Шаги:**
1. Отправить POST /UnitGroup с Basic Auth и телом в виде невалидного JSON (например, обрезанная строка `{"pageNum": 0, "pageSize": `).

**Ожидаемый результат:** HTTP 400, 415 или 422.

---

### ТК-6. POST /UnitGroup: ids не массив — 400

**Шаги:**
1. Отправить POST /UnitGroup с телом { pageNum: 0, pageSize: 0, ids: "not-an-array" } и Basic Auth.

**Ожидаемый результат:** HTTP 400 или иная ошибка валидации; либо 200 с валидной структурой ответа, если API игнорирует поле.

# Таблица проверок Smoke: Personnel (сотрудники)

Последовательный сценарий smoke для API Personnel: создание одного (A) → обновление одного (A, поле name/fullName) → создание двух (B1, B2) → обновление пачки (B1, B2, поле name/fullName) → GET с проверкой наличия и значений полей после обновления → удаление одного → проверка фильтра → удаление двух → финальная проверка чистоты через POST-фильтр. Для сценария используются фиксированные ссылки на существующие объекты справочников: производственный участок (**ProductionUnit**) и профессия (**Profession**) — их id задаются в фикстурах и не запрашиваются отдельными GET. Это сокращает время прогона тестов.

| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | Smoke: PUT /Personnel/CreateOrUpdate — создание одного объекта | PUT с минимально валидным payload RestPersonnel (firstName, lastName, integrationId, code, name/fullName, вложенные personnelLocations и personnelQualifications) | 200, count==1, added==1, errors==0, results[0].entity.id; сохранение id, integrationId и payload объекта A |
| 2 | Smoke: PUT /Personnel/CreateOrUpdate — обновление одного объекта | PUT того же объекта A (тот же integrationId), поля name/fullName изменены | 200, result "Updated", updated==1; сохранение ожидаемого значения name/fullName для проверки в GET |
| 3 | Smoke: PUT /Personnel/CreateOrUpdateMany — создание двух объектов | PUT с массивом из двух RestPersonnel | 200, added==2, errors==0, в results два элемента с entity.id; сохранение id, integrationId и массива payloads объектов B1, B2 |
| 4 | Smoke: PUT /Personnel/CreateOrUpdateMany — обновление двух объектов | PUT того же массива (те же integrationId), у каждого изменены поля name/fullName | 200, updated==2, errors==0; сохранение списка обновлённых значений name/fullName для B1, B2 |
| 5 | Smoke: GET /Personnel — в списке есть A, B1, B2 и поля после обновления | GET /Personnel с пагинацией; поиск по integrationId; проверка поля name | 200, items — массив; A, B1, B2 найдены; name у каждой записи совпадает с сохранённым при обновлении |
| 6 | Smoke: PATCH /Personnel/Delete — удаление объекта A | PATCH /Personnel/Delete с телом { integrationId: integrationId_A } | 200 или 204; при 200 — deleted==1 |
| 7 | Smoke: POST /Personnel — фильтр по B1 и B2 | POST /Personnel с телом { pageNum: 0, pageSize: 100, integrationIds: [integrationId_B1, integrationId_B2], noCount: false } | 200, в items ровно 2 элемента (B1 и B2) |
| 8 | Smoke: PATCH /Personnel/DeleteMany — удаление B1 и B2 | PATCH /Personnel/DeleteMany с телом [ { integrationId: integrationId_B1 }, { integrationId: integrationId_B2 } ] | 200 или 204; при 200 — deleted==2 (или >= 1) |
| 9 | Smoke: POST /Personnel — финальная проверка чистоты | POST /Personnel с фильтром по integrationIds A, B1, B2; проверка, что items пустой | 200; items пуст, объекты A, B1, B2 не возвращаются |

---

## Подробные тест-кейсы

### ТК-1. Smoke: PUT /Personnel/CreateOrUpdate — создание одного объекта (A)

**Предусловия:** В системе существуют валидные значения для ProductionUnit и Profession (их id заданы в фикстурах). API доступен, Basic Auth.

**Шаги:**
1. Сформировать payload RestPersonnel:
   - обязательные поля firstName, lastName;
   - уникальные integrationId и code;
   - name/fullName, сформированные на основе ФИО;
   - массив personnelLocations из одного элемента: базовая локация с `personnel: { id: 0 }`, `productionUnit: { id: <id_подразделения> }`, признаками isBasic=true, isPermanent=true и диапазоном дат;
   - массив personnelQualifications из одного элемента: базовая квалификация с `personnel: { id: 0 }`, `profession: { id: <id_профессии> }`, grade=1, status=0.
2. Выполнить PUT /Personnel/CreateOrUpdate с Basic Auth.
3. Проверить код 200, count==1, added==1, errors==0.
4. Проверить наличие results[0].entity.id; сохранить id, integrationId и payload для следующих шагов.

**Ожидаемый результат:** 200; объект A создан; id, integrationId и payload сохранены в состоянии сценария.

---

### ТК-2. Smoke: PUT /Personnel/CreateOrUpdate — обновление одного объекта (A)

**Предусловия:** Выполнен ТК-1 (есть payload объекта A).

**Шаги:**
1. Взять сохранённый payload A, скопировать, изменить поля name и fullName (например, добавить суффикс " (обновлено)" в пределах лимита длины).
2. Выполнить PUT /Personnel/CreateOrUpdate с Basic Auth.
3. Проверить код 200, result "Updated", updated==1.
4. Сохранить новое значение name/fullName для проверки в GET.

**Ожидаемый результат:** 200; объект A обновлён; ожидаемое значение name/fullName сохранено.

---

### ТК-3. Smoke: PUT /Personnel/CreateOrUpdateMany — создание двух объектов (B1, B2)

**Предусловия:** Выполнен ТК-2 (объект A обновлён).

**Шаги:**
1. Сформировать массив из двух RestPersonnel с разными integrationId, code, name/fullName и теми же ссылками на ProductionUnit и Profession.
2. Выполнить PUT /Personnel/CreateOrUpdateMany с Basic Auth.
3. Проверить 200, added==2, errors==0, в results два элемента с entity.id.
4. Сохранить id, integrationId и массив payloads обоих объектов (B1, B2).

**Ожидаемый результат:** 200; объекты B1 и B2 созданы; их id, integrationId и payloads сохранены.

---

### ТК-4. Smoke: PUT /Personnel/CreateOrUpdateMany — обновление двух объектов (B1, B2)

**Предусловия:** Выполнен ТК-3 (есть массив payloads для B1, B2).

**Шаги:**
1. Взять сохранённые payloads B1 и B2, для каждого скопировать и изменить поля name/fullName (например, добавить суффикс " (обновлено)" в пределах 250 символов).
2. Выполнить PUT /Personnel/CreateOrUpdateMany с Basic Auth.
3. Проверить 200, updated==2, errors==0.
4. Сохранить список обновлённых значений name/fullName для B1 и B2 (в том же порядке).

**Ожидаемый результат:** 200; объекты B1 и B2 обновлены; список ожидаемых name/fullName сохранён.

---

### ТК-5. Smoke: GET /Personnel — в списке есть A, B1, B2 и поля после обновления

**Предусловия:** В состоянии сценария есть integrationId и ожидаемые значения name/fullName для A, B1, B2.

**Шаги:**
1. Выполнить GET /Personnel с Basic Auth (pageNum=0, pageSize достаточный для получения всех созданных, например 5000).
2. Проверить код 200, наличие поля items, items — массив.
3. Найти в items элементы по integrationId для A, B1, B2.
4. Проверить, что у найденных записей поле name совпадает с сохранёнными при обновлении значениями.

**Ожидаемый результат:** 200; items содержит A, B1, B2; у каждой записи name совпадает с ожидаемым после обновления.

---

### ТК-6. Smoke: PATCH /Personnel/Delete — удаление объекта A

**Предусловия:** Сохранён integrationId объекта A (после ТК-5).

**Шаги:**
1. Выполнить PATCH /Personnel/Delete с Basic Auth и телом { integrationId: integrationId_A }.
2. Проверить код 200 или 204; при 200 и наличии тела ответа — deleted==1.

**Ожидаемый результат:** 200 или 204; объект A удалён.

---

### ТК-7. Smoke: POST /Personnel — фильтр по B1 и B2

**Предусловия:** Сохранены integrationId для B1 и B2; объект A удалён.

**Шаги:**
1. Выполнить POST /Personnel с Basic Auth и телом { pageNum: 0, pageSize: 100, integrationIds: [integrationId_B1, integrationId_B2], noCount: false }.
2. Проверить код 200; в items ровно 2 элемента.

**Ожидаемый результат:** 200; в items только B1 и B2.

---

### ТК-8. Smoke: PATCH /Personnel/DeleteMany — удаление B1 и B2

**Предусловия:** Сохранены integrationId объектов B1 и B2.

**Шаги:**
1. Выполнить PATCH /Personnel/DeleteMany с Basic Auth и телом [ { integrationId: integrationId_B1 }, { integrationId: integrationId_B2 } ].
2. Проверить код 200 или 204; при 200 — deleted==2 (или >= 1).

**Ожидаемый результат:** 200 или 204; объекты B1 и B2 удалены.

---

### ТК-9. Smoke: POST /Personnel — финальная проверка чистоты

**Предусловия:** Все созданные в сценарии объекты (A, B1, B2) удалены.

**Шаги:**
1. Выполнить POST /Personnel с Basic Auth и телом { pageNum: 0, pageSize: 100, integrationIds: [integrationId_A, integrationId_B1, integrationId_B2], noCount: false }.
2. В items убедиться, что массив пуст (нет элементов с сохранёнными integrationId для A, B1, B2).

**Ожидаемый результат:** 200; items пуст (A, B1, B2 не возвращаются в ответе).


# Таблица проверок PUT /UnitGroup/CreateOrUpdate

| № | Название проверки | Что проверяется | Ожидаемый результат |
|---|-------------------|-----------------|---------------------|
| 1 | Создание группы с полным набором полей (PUT + GET + сравнение) | Создание UnitGroup с code, name, integrationId, baseUnit | 200, added=1 или updated=1, схема ответа, группа в GET, поля совпадают |
| 2 | Создание с минимальным набором (code, name, baseUnit) | Создание только с обязательными полями | 200, added=1 или updated=1, группа в GET |
| 3 | Обязательность: отсутствие name — ошибка | PUT без поля name | 400 или ошибка в results |
| 4 | Обязательность: отсутствие code — ошибка | PUT без поля code | 400 или ошибка в results |
| 5 | Уникальность: повтор по integrationId — обновление (updated=1) | Два PUT с одним integrationId, разный name | Первый: added=1; второй: updated=1 |
| 6 | Уникальность: повтор по code+name — обновление (updated=1) | Два PUT с одной парой code+name | Второй: updated=1 |
| 7 | Границы: code длина 30, name длина 250 — успех | Поля на границе maxLength | 200, создание |
| 8 | Правило: создание по IntegrationId (без id) | PUT без id, с уникальным integrationId | 200, added=1 |
| 9 | Правило: создание по Code+Name (без id и integrationId) | PUT без id и integrationId, с уникальной парой code+name | 200, added=1 |
| 10 | Правило: обновление по Id | PUT с id существующей группы и новыми полями | 200, updated=1, в GET — обновлённые данные |
| 11 | Идемпотентность: один и тот же запрос дважды | Два одинаковых PUT подряд | Первый: added=1; второй: updated=1 |
| 12 | Запрос без тела (пустой body) — 400 | PUT с телом {} | 400 или ошибка в results |
| 13 | Запрос без авторизации — 401 | PUT без Basic Auth | 401 Unauthorized |
| 14 | Невалидный JSON в теле — 400 | PUT с невалидным JSON | 400, 415 или 422 |

---

## Подробные тест-кейсы

### ТК-1. Создание группы с полным набором полей

**Предусловия:** Создана одна Unit через PUT /Unit/CreateOrUpdate.

**Шаги:**
1. Сформировать payload: code, name, integrationId (уникальные), baseUnit: { id: &lt;id Unit&gt; }.
2. Выполнить PUT /UnitGroup/CreateOrUpdate с Basic Auth.
3. Проверить код 200, наличие results, added=1 или updated=1.
4. Проверить ответ по схеме RestResponseDtoOfRestUnitGroup.
5. Выполнить GET /UnitGroup, найти группу по integrationId.
6. Сравнить поля созданной группы с отправленным payload.

**Ожидаемый результат:** 200, добавление или обновление, схема соблюдена, группа есть в GET и данные совпадают.

---

### ТК-2. Создание с минимальным набором (code, name, baseUnit)

**Шаги:**
1. Создать Unit, получить baseUnit ref.
2. Отправить PUT /UnitGroup/CreateOrUpdate с полями: code, name, baseUnit (без integrationId).
3. Проверить 200, added=1 или updated=1, наличие группы в GET.

**Ожидаемый результат:** Успешное создание без ошибок.

---

### ТК-3. Обязательность: отсутствие name — ошибка

**Шаги:**
1. Payload без name (есть code, baseUnit).
2. PUT /UnitGroup/CreateOrUpdate.

**Ожидаемый результат:** HTTP 400 или 200 с ошибкой в results (не added=1).

---

### ТК-4. Обязательность: отсутствие code — ошибка

**Шаги:**
1. Payload без code (есть name, baseUnit).
2. PUT /UnitGroup/CreateOrUpdate.

**Ожидаемый результат:** HTTP 400 или ошибка в results.

---

### ТК-5. Уникальность: повтор по integrationId — обновление

**Шаги:**
1. Создать группу с уникальным integrationId (первый PUT → added=1).
2. Второй PUT с тем же integrationId и другим name.
3. Проверить updated=1 и что в GET у группы новое name.

**Ожидаемый результат:** Второй ответ: 200, updated=1; в GET — обновлённое имя.

---

### ТК-6. Уникальность: повтор по code+name — обновление

**Шаги:**
1. Создать группу по code+name (без integrationId) → added=1.
2. Второй PUT с теми же code и name, добавить integrationId или изменить другие поля.
3. Проверить updated=1.

**Ожидаемый результат:** 200, updated=1.

---

### ТК-7. Границы: code длина 30, name длина 250

**Шаги:**
1. Payload с code длиной 30 символов, name длиной 250 символов, валидный baseUnit.
2. PUT /UnitGroup/CreateOrUpdate.

**Ожидаемый результат:** 200, успешное создание.

---

### ТК-8. Правило: создание по IntegrationId (без id)

**Шаги:**
1. Payload без поля id, с уникальным integrationId и baseUnit.
2. PUT /UnitGroup/CreateOrUpdate.
3. Проверить added=1 и наличие группы в GET по integrationId.

**Ожидаемый результат:** 200, added=1.

---

### ТК-9. Правило: создание по Code+Name (без id и integrationId)

**Шаги:**
1. Payload только code, name, baseUnit (без id и integrationId).
2. PUT /UnitGroup/CreateOrUpdate.
3. Проверить added=1.

**Ожидаемый результат:** 200, added=1.

---

### ТК-10. Правило: обновление по Id

**Шаги:**
1. Создать группу, получить её id из GET.
2. PUT с id, новым name и теми же code, baseUnit.
3. Проверить updated=1 и что в GET у записи с этим id — новое name.

**Ожидаемый результат:** 200, updated=1; в GET — обновлённые данные.

---

### ТК-11. Идемпотентность: один и тот же запрос дважды

**Шаги:**
1. Отправить один и тот же payload дважды подряд.
2. Первый ответ: added=1.
3. Второй ответ: updated=1.
4. В GET одна запись с данными из payload.

**Ожидаемый результат:** Первый PUT — added=1, второй — updated=1; в списке одна группа.

---

### ТК-12. Запрос без тела (пустой body) — 400

**Шаги:**
1. PUT /UnitGroup/CreateOrUpdate с телом {} и Basic Auth.

**Ожидаемый результат:** 400 или ошибка в results.

---

### ТК-13. Запрос без авторизации — 401

**Шаги:**
1. Создать Unit с auth. Сформировать payload UnitGroup с baseUnit.
2. PUT /UnitGroup/CreateOrUpdate без заголовка Authorization.

**Ожидаемый результат:** HTTP 401 Unauthorized.

---

### ТК-14. Невалидный JSON в теле — 400

**Шаги:**
1. Отправить PUT с телом в виде невалидного JSON (обрыв строки).

**Ожидаемый результат:** HTTP 400, 415 или 422.

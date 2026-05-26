# Анализ Frontend проекта Network Monitor

## Общий обзор

**Тип приложения**: Server-Side Rendered (SSR) HTML — не SPA.  
**Архитектура**: FastAPI (Python) → Jinja2 шаблоны → HTMX + TailwindCSS + Vanilla JS.  
**Состояние**: Ранняя-средняя стадия разработки (3 коммита в git).

### Текущий стек

| Технология | Назначение |
|---|---|
| Jinja2 | Шаблонизатор (включение partials, наследование) |
| HTMX 1.9.6 | Динамические обновления HTML (polling, фильтры, пагинация) |
| TailwindCSS v4 | Утилитарные CSS-классы |
| Custom CSS | Тема оформления "Cyber Terminal" (232 строки) |
| Vanilla JS (app.js) | Вся клиентская логика (357 строк) |
| FontAwesome 6.5.1 | Иконки |

## Критические проблемы

### 1. Race condition в фильтрации статусов

**Файлы**: `_statuses.html` + `app.js` `initFilters()`

Фильтры ALL/ONLINE/OFFLINE имеют **два параллельных механизма** обработки кликов:

- Встроенные HTMX-атрибуты (`hx-get`, `hx-vals`) на каждой кнопке
- JavaScript-обработчик `initFilters()`, который перезаписывает `hx-vals` на `#terminal-list`

При клике срабатывают оба механизма, создавая состояние гонки. Фактически HTMX отправляет запрос с `hx-vals` кнопки, а JS в то же время обновляет атрибут для следующего запроса. Это приводит к недетерминированному поведению.

**Решение**: Удалить JS-обработчик `initFilters()`, оставить только HTMX-атрибуты на кнопках.

### 2. `setPollingInterval()` не останавливает текущий таймер HTMX

**Файл**: `app.js:330-336`

```javascript
setPollingInterval(seconds) {
    list.setAttribute('hx-trigger', `load, every ${seconds}s`);
}
```

Простое изменение атрибута `hx-trigger` **не влияет** на уже запущенный HTMX polling timer. Новое значение применяется только при следующей полной загрузке/свапе элемента. Пользователь выбирает "30 секунд", а таймер продолжает тикать каждые 10 секунд.

**Решение**: Использовать `htmx.trigger('#terminal-list', 'htmx:load')` для перезапуска, либо заменить polling на `setInterval()` + `htmx.ajax()`.

### 3. Состояние сортировки сбрасывается после фильтрации/поиска

**Файл**: `app.js:96-116`

При фильтрации HTMX заменяет `innerHTML` таблицы. Хотя есть обработчик `htmx:afterSettle`, который восстанавливает сортировку, он не сохраняет состояние сортировки при замене контента, если данные изменились.

### 4. Нет CSRF-защиты

Форма команд и все HTMX-запросы не имеют CSRF-токенов. Для локального инструмента это допустимо, но при публикации в сеть — уязвимость.

## Проблемы средней важности

### 5. Дублирование логики форматирования на бэкенде

**Файл**: `app/api/v1/routes/dashboard.py`

Два роута (`/htmx/terminals` и `/htmx/host_card/{hostname}`) содержат идентичный код форматирования полей (uptime, traffic). Добавление нового поля требует правки в двух местах.

### 6. Модальные окна открываются через fetch + innerHTML вместо HTMX

**Файл**: `app.js:174-184`

Модальное окно хоста использует ручной `fetch()` + `innerHTML`. Это дублирует функциональность HTMX и теряет преимущества:
- Встроенная обработка ошибок
- HTMX-индикаторы загрузки
- История браузера

**Решение**: Использовать `hx-get="/htmx/host_card/{hostname}"` + `hx-target="#host-modal-content"`.

### 7. Селектор `td:nth-child(4)` в updateCounters хрупкий

**Файл**: `app.js:147`

```javascript
const statusSpan = tr.querySelector('td:nth-child(4) span');
```

Если порядок колонок изменится, счётчики сломаются.

**Решение**: Добавить `data-status` атрибут на строку и читать его.

### 8. `sendCommand()` не отправляет запрос на сервер

**Файл**: `app.js:203-215`

Метод только показывает toast и блок результата, но реального HTTP-запроса не делает. Соответствующего бэкенд-эндпоинта нет.

## Улучшения качества кода

### 9. Смешивание inline-стилей и Tailwind-классов

Почти каждый шаблон содержит `style="..."` атрибуты рядом с Tailwind классами. Пример из `_row_table.html`:

```html
<tr style="border-bottom: 1px solid var(--border-color); cursor: pointer;"
    class="hover:bg-[rgba(0,255,157,0.05)] transition-colors">
```

Это затрудняет поддержку темы и переопределение стилей.

**Решение**: Перенести все inline-стили в CSS-классы в `styles_cyberterminal.css`.

### 10. Монолитный JS-файл (357 строк)

Весь клиентский код в одном файле, одно глобальное состояние `App`. Добавление новой функциональности увеличивает файл.

### 11. Нет обработки ошибок для fetch

**Файл**: `app.js:180-183`

`fetch()` в `openHostModal()` имеет catch, но в `sendCommand()` вообще нет HTTP-запроса.

### 12. Логика представления в шаблонах

Jinja2-шаблоны содержат условные операторы для цветовых порогов (`{% if pc.cpu_percent > 80 %}`). Это нарушает разделение логики и представления.

### 13. Жёстко закодированные названия полей

Имена полей Computer Model дублируются в 7+ местах:
- `computer.py` (модель)
- `agent_metrics.py` (схема)
- `metrics.py` (обновление)
- `dashboard.py` (дважды)
- `_row_table.html` (data-атрибуты)
- `_card.html` (отображение)
- `_head_table.html` (заголовки)

## Производительность

### 14. Полный polling каждые N секунд

Каждый запрос к `/htmx/terminals` возвращает полный HTML всей таблицы (с пагинацией по 18 записей). Для 500+ машин это создаёт избыточную нагрузку.

### 15. Клиентская сортировка после каждого HTMX-ответа

`sortTable()` вызывается каждый раз в обработчике `htmx:afterSettle`, даже если пользователь не сортировал данные.

### 16. TailwindCSS не оптимизирован

`output.css` содержит все классы Tailwind, а не только используемые (хотя v4 с `@source` должен это делать, нужно проверить финальный размер).

## Безопасность

### 17. Отсутствует аутентификация

Любой, имеющий доступ к порту сервера, может просматривать все метрики и потенциально отправлять команды.

### 18. Hardcoded SECRET_KEY

В `app/config.py` прописано `SECRET_KEY: str = "your-secret-key-here"`. В `.env` также не указано безопасное значение.

---

# Предложения по рефакторингу

По степени приоритетности:

## Приоритет 1 (High) — Критические баги

### 1.1. Исправить race condition в фильтрах

**Действие**: Удалить `initFilters()` из `app.js`. Оставить только HTMX-атрибуты на кнопках. Добавить обработчик `htmx:afterSettle` для подсветки активной кнопки.

```html
<!-- _statuses.html (после рефакторинга) -->
<div id="filters">
    <div class="flex border rounded" style="border-color: var(--border-color)">
        <button class="px-3 py-2 text-xs font-bold status-filter active" data-filter="ALL"
                hx-get="/htmx/terminals" hx-target="#terminal-list" hx-indicator="#loading-spinner"
                hx-vals='{"page": "1", "status": "ALL", "q": ""}'>ALL</button>
        <button class="px-3 py-2 text-xs font-bold status-filter" data-filter="ONLINE"
                hx-get="/htmx/terminals" hx-target="#terminal-list" hx-indicator="#loading-spinner"
                hx-vals='{"page": "1", "status": "ONLINE", "q": ""}'>ONLINE</button>
        <button class="px-3 py-2 text-xs font-bold status-filter" data-filter="OFFLINE"
                hx-get="/htmx/terminals" hx-target="#terminal-list" hx-indicator="#loading-spinner"
                hx-vals='{"page": "1", "status": "OFFLINE", "q": ""}'>OFFLINE</button>
    </div>
</div>
```

### 1.2. Исправить `setPollingInterval()`

**Действие**: Использовать `htmx.ajax()` с периодическим вызовом через `setInterval()`.

```javascript
// app.js
setPollingInterval(seconds) {
    const list = document.getElementById('terminal-list');
    if (this._pollingTimer) clearInterval(this._pollingTimer);
    if (list) {
        list.removeAttribute('hx-trigger');
        this._pollingTimer = setInterval(() => {
            htmx.ajax('GET', '/htmx/terminals', {
                target: '#terminal-list',
                swap: 'innerHTML',
                values: { /* текущие фильтры */ }
            });
        }, seconds * 1000);
    }
    localStorage.setItem('cybermonitor-polling', seconds);
}
```

### 1.3. Исправить `updateCounters()`

**Действие**: Использовать `data-status` атрибут вместо `td:nth-child(4)`.

```javascript
// app.js updateCounters
updateCounters() {
    let online = 0, offline = 0;
    document.querySelectorAll('#cli-table tbody tr[data-status]').forEach(tr => {
        if (tr.dataset.status === 'ONLINE') online++;
        else offline++;
    });
    // ... обновление UI
}
```

```html
<!-- _row_table.html — добавить атрибут -->
<tr data-status="{{ pc.status }}" ...>
```

## Приоритет 2 (Medium) — Архитектурные улучшения

### 2.1. Выделить общий слой форматирования на бэкенде

Создать функцию/хелпер `format_computer(computer)`, возвращающую словарь с форматированными полями:

```python
# app/helpers/computer.py
def format_computer(computer: Computer) -> dict:
    return {
        "hostname": computer.hostname,
        "status": computer.status,
        "cpu_percent": computer.cpu_percent,
        "uptime_formatted": format_uptime(computer.uptime_seconds),
        "net_down_formatted": format_traffic(computer.bytes_recv_mb),
        "net_up_formatted": format_traffic(computer.bytes_sent_mb),
        # ... все поля
    }
```

### 2.2. Заменить `fetch()` на HTMX для модального окна

```html
<!-- base.html — модальное окно хоста -->
<div id="host-modal" ...>
    <div id="host-modal-content"></div>
</div>

<!-- _row_table.html — вызов -->
<button hx-get="/htmx/host_card/{{ pc.hostname|lower|e }}"
        hx-target="#host-modal-content"
        hx-trigger="click"
        onclick="htmx.takeClass('#host-modal', 'hidden'); htmx.takeClass('#host-modal', 'flex');">
    {{ pc.hostname }}
</button>
```

### 2.3. Заменить all-inline-стили на CSS-классы

Создать Tailwind-подобные CSS-переменные и классы для частых комбинаций:

```css
/* styles_cyberterminal.css — добавить */
.text-muted { color: var(--text-muted); }
.text-main { color: var(--text-main); }
.border-color { border-color: var(--border-color); }
.bg-panel { background-color: var(--bg-panel); }
```

## Приоритет 3 (Low) — Качество кода

### 3.1. Разделить app.js на модули

Структура файлов:

```
app/static/js/
├── app.js              # Только точка входа, инициализация
├── state.js            # Управление состоянием (сортировка, тема, polling)
├── modals.js           # Модальные окна (host, command, settings)
├── table.js            # Сортировка таблицы, фильтры
└── utils.js            # Утилиты (toast, copy, animation)
```

### 3.2. Вынести цветовые пороги в конфиг

Создать константы для пороговых значений:

```javascript
// app.js
const THRESHOLDS = {
    cpu: { danger: 80 },
    ram: { danger: 80 },
    disk: { danger: 90 }
};
```

### 3.3. Добавить `<noscript>` fallback

```html
<!-- base.html -->
<noscript>
    <div style="padding: 2rem; text-align: center; color: #f85149;">
        ⚠ Для работы панели управления требуется JavaScript
    </div>
</noscript>
```

### 3.4. Добавить CSRF-защиту для POST-запросов

```python
# dependencies.py — middleware для CSRF
```

```javascript
// app.js — глобальная настройка HTMX с CSRF-токеном
document.body.addEventListener('htmx:configRequest', (e) => {
    e.detail.headers['X-CSRF-Token'] = getCookie('csrf_token');
});
```

## Приоритет 4 (Future) — Долгосрочные улучшения

### 4.1. WebSocket вместо polling

Заменить HTTP-polling на WebSocket через `htmx.org` + `ws` на бэкенде. Это снизит нагрузку и ускорит обновления.

### 4.2. Виртуализация таблицы

Для больших сетей (1000+ узлов) внедрить виртуальный скролл или сохранить пагинацию с серверной сортировкой.

### 4.3. E2E-тесты

Добавить Playwright/Cypress тесты для критических сценариев:
- Загрузка дашборда
- Фильтрация по статусу
- Сортировка колонок
- Поиск по hostname
- Открытие карточки хоста

### 4.4. Автоматизация сборки

Заменить ручную компиляцию Tailwind на автоматическую через `make css-watch` в dev-режиме.

---

## Резюме

Проект функционален и имеет стильный cyber-terminal дизайн. Основные проблемы — в дублировании механизмов (HTMX + JS для одних и тех же действий), хрупких селекторах, и смешанном подходе к стилизации. Критических багов два (race condition в фильтрах и неработающий polling interval), остальное — вопросы поддерживаемости и производительности.

**Рекомендуемый порядок действий**:
1. Исправить race condition в фильтрах
2. Починить `setPollingInterval()`
3. Укрепить `updateCounters()` через `data-*` атрибуты
4. Выделить общий хелпер форматирования на бэкенде
5. Перевести модалки на HTMX
6. Заменить inline-стили на CSS-классы
7. Разделить app.js на модули

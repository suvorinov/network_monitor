# Frontend: анализ и предложения по рефакторингу

> Текущее состояние после выполненных улучшений (удаление `_cli_table.html`, HTMX-индикатор/ошибки, локальный TailwindCSS).

---

## 1. 🧹 Кодовая база

### 1.1 JS размазан по 4+ местам

Проблема: JavaScript находится в `app.js`, `dashboard.html` (inline), `terminals.html` (inline, 2 блока), `base.html` (inline). Логика дублируется, трудно поддерживать.

**Решение:**
- Перенести всю логику в `app.js`
- Сделать инициализацию через единую функцию `initDashboard()` / `initFilters()` / `initSorting()`
- В шаблонах оставить только вызовы функций и data-атрибуты

### 1.2 Undefined функции

В `base.html` используются `closeCommandModal()` и `setCommand()`, но они нигде не определены. При клике — ошибка в консоли.

**Решение:** Определить функции-заглушки или удалить, если функционал не реализован.

### 1.3 Мёртвый код

- `dashboard.html:39-47` и `:67-83` — закомментированные блоки
- `app.js:1` — `let modalHostname = '';` (нигде не используется)
- `app.js:3` — `let resultCheckInterval;` (нигде не используется)
- `dashboard.html:62` — `console.log(currentVals)` — отладочный вывод

**Решение:** Удалить.

### 1.4 Глобальные переменные

`onlineCount`, `offlineCount`, `currentSortState`, `toastTimeout` — висят в `window`.

**Решение:** Завернуть в модуль (IIFE) или использовать объект-неймспейс:

```js
const App = {
    state: { onlineCount: 0, offlineCount: 0, sort: { key: null, type: 'string', asc: true } },
    toastTimeout: null,
    // methods...
};
```

---

## 2. ⚡ Производительность

### 2.1 HTMX polling при скрытой вкладке

`hx-trigger="every 10s"` продолжает опрашивать сервер даже когда вкладка неактивна.

**Решение:** Добавить условие `[!document.hidden]`:

```html
hx-trigger="every 10s[!document.hidden]"
```

Или через IntersectionObserver — останавливать polling, если таблица не видна.

### 2.2 Inline-стили вместо CSS-классов

`style="color: var(--text-muted)"` повторяется ~40 раз в шаблонах. Это раздувает HTML и усложняет поддержку.

**Решение:** Вынести в CSS-классы:

```css
.text-muted { color: var(--text-muted); }
.text-main { color: var(--text-main); }
.border-cyber { border-color: var(--border-color); }
```

Заменить во всех шаблонах `style="color: var(--text-muted)"` на `class="text-muted"`.

### 2.3 Прогресс-бары с дублированием логики

Шаблоны CPU/RAM/DISK в `_row_table.html` и `_card.html` — практически идентичный код с дублированием условий для цвета.

**Решение:** Создать Jinja2-макрос (или фильтр) для прогресс-бара:

```jinja
{% macro progress_bar(value, threshold, color_normal, color_danger) %}
<div class="inline-flex items-center justify-end space-x-1.5">
    <div class="w-10 h-1.5 rounded-full flex-shrink-0 bg-terminal">
        <div class="h-1.5 rounded-full" style="width: {{ value }}%; background-color: {{ '#f85149' if value > threshold else color_normal }};"></div>
    </div>
    <span class="w-9 text-right flex-shrink-0 {{ 'glow-red' if value > threshold else '' }}">{{ value }}%</span>
</div>
{% endmacro %}
```

---

## 3. 🐛 Баги

### 3.1 Пагинация теряет поиск и фильтр

При переходе на следующую страницу `hx-vals='{"page": "...", "view": "..."}'` не передаёт `q` и `status`. Пользователь переходит на страницу 2 и теряет текущий поисковый запрос/фильтр.

**Решение:** Передавать все текущие параметры:

```html
hx-vals='{"page": "{{ page + 1 }}", "view": "{{ view_type }}", "q": "...", "status": "..."}'
```

Или читать их из `hx-vals` контейнера `#terminal-list` в JS перед отправкой.

### 3.2 XSS в hostname

`openHostModal('{{ pc.hostname|lower }}')` и `fetch(/htmx/host_card/${hostname})` — hostname может содержать спецсимволы.

**Решение:** Использовать `encodeURIComponent`:

```js
fetch(`/htmx/host_card/${encodeURIComponent(hostname)}`)
```

На серверной стороне в `_row_table.html`:

```
data-sort-hostname="{{ pc.hostname|lower|e }}"
```

### 3.3 `filterOffline()` имитирует клик по DOM

Функция ищет DOM-элемент и вызывает `.click()`. Хрупкий подход — если структура фильтров изменится, сломается.

**Решение:** Вызывать HTMX напрямую:

```js
function filterOffline() {
    htmx.ajax('GET', '/htmx/terminals', {
        target: '#terminal-list',
        swap: 'innerHTML',
        values: { status: 'OFFLINE', view: 'cli', page: 1, q: '' }
    });
}
```

---

## 4. 💅 UI/UX

### 4.1 Переключение вида (cli/table)

В дашборде захардкожено `"view": "cli"`. Второй режим `table` не реализован. Кнопка "Узлы сети" в сайдбаре удалена.

**Решение:**
- Либо удалить `view_type` из всех шаблонов и роута `/htmx/terminals`
- Либо реализовать полноценное переключение с кнопкой в шапке дашборда

### 4.2 Кнопка "Настройки" — заглушка

В сайдбаре ссылка ведёт на `#`.

**Решение:** Либо удалить, либо сделать модалку с базовыми настройками (интервал обновления, смена темы).

### 4.3 Нет debounce для `hx-indicator` при поиске

Поиск срабатывает через 300ms debounce. Если пользователь стирает и быстро печатает заново, спиннер мигает 2 раза.

**Решение:** Добавить минимальную задержку для `hx-indicator` через CSS:

```css
#loading-spinner {
    opacity: 0;
    transition: opacity 0.3s ease, display 0.3s allow-discrete;
}
```

Или добавить `hx-indicator` отдельно с задержкой через JS.

---

## 5. 🏗 Архитектура шаблонов

### 5.1 Избыточное количество partials

Текущая структура:

```
templates/
├── base.html
├── dashboard.html
└── partials/
    ├── _card.html
    ├── _head_table.html
    ├── _row_table.html
    ├── _search_hostname.html
    ├── _sidebar.html
    ├── _statuses.html
    └── terminals.html
```

`_search_hostname.html` (8 строк), `_statuses.html` (10 строк), `_head_table.html` (30 строк) — можно объединить:

| Сейчас | Предложение |
|--------|------------|
| `_search_hostname.html` | Включить в `dashboard.html` |
| `_statuses.html` | Включить в `dashboard.html` |
| `_head_table.html` | Включить в `terminals.html` |
| `_row_table.html` | Оставить (DRY — используется в цикле) |
| `_sidebar.html` | Оставить |
| `_card.html` | Оставить |

### 5.2 Жёсткие ширины колонок в `_head_table.html` и `_row_table.html`

Значения `w-[15%]`, `w-[10%]` и т.д. дублируются в 2 файлах. При изменении нужно править оба.

**Решение:** Вынести в CSS-классы или задавать ширину только в `_head_table.html` (таблица использует `table-layout: fixed`).

---

## 6. 📋 Приоритет выполнения

| # | Задача | Приоритет | Влияние | Сложность |
|---|--------|-----------|---------|-----------|
| 1 | undefined функции (closeCommandModal, setCommand) | 🔴 High | Ломает JS при клике | Низкая |
| 2 | Пагинация теряет поиск/фильтр | 🔴 High | Функциональный баг | Средняя |
| 3 | XSS в hostname | 🔴 High | Безопасность | Низкая |
| 4 | Удалить мёртвый код (console.log, комментарии) | 🟡 Medium | Чистота кода | Низкая |
| 5 | Inline-стили → CSS-классы | 🟡 Medium | Производительность/поддержка | Средняя |
| 6 | JS размазан → собрать в app.js | 🟡 Medium | Поддержка | Высокая |
| 7 | `filterOffline` — убрать имитацию клика | 🟡 Medium | Надёжность | Низкая |
| 8 | HTMX polling при скрытой вкладке | 🟡 Medium | Производительность | Низкая |
| 9 | Глобальные переменные → модуль | 🟢 Low | Архитектура | Средняя |
| 10 | Уменьшить количество partials | 🟢 Low | Архитектура | Средняя |
| 11 | Прогресс-бары через макрос | 🟢 Low | DRY | Средняя |
| 12 | Переключение вида (cli/table) | 🟢 Low | Функциональность | Высокая |

---

## 7. 🔄 CI/CD

Добавить `make css` в CI/CD pipeline, чтобы `output.css` всегда был актуален:

```yaml
# .gitlab-ci.yml / GitHub Actions
- run: make css
- run: uvicorn app.main:app --host 0.0.0.0 --port 8900
```

Альтернатива — добавить `make css` в pre-commit хук.

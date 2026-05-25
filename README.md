# network_monitor

Система мониторинга компьютерной сети. Сервер на FastAPI собирает метрики с агентов (CPU, RAM, disk, network) и отображает их в веб-дашборде.

## Архитектура

```
network_monitor/
├── app/                  # FastAPI-сервер
│   ├── api/v1/routes/   # Эндпоинты (дашборд, приём метрик)
│   ├── models/          # SQLAlchemy модель Computer
│   ├── schemas/         # Pydantic схема AgentMetrics
│   ├── templates/       # Jinja2 + HTMX шаблоны
│   └── static/          # CSS, JS, шрифты
├── agent/               # Агент для целевых машин (psutil + requests)
└── docker-compose.yml   # Запуск сервера в Docker
```

## Быстрый старт

```bash
# 1. Установка зависимостей сервера
pip install -r requirements.txt

# 2. Сборка TailwindCSS (требуется ./tailwindcss)
make css

# 3. Запуск сервера
uvicorn app.main:app --reload --host 0.0.0.0 --port 8900
```

## Запуск агента

```bash
# На целевой машине (требуется Python + psutil)
python agent/agent.py
```

Настройки агента — в `agent/config.ini` (URL сервера, интервал опроса).

## Docker

```bash
make up       # Запуск в фоне
make down     # Остановка
make logs     # Просмотр логов
make build    # Пересборка образа
```

## Makefile

| Команда        | Назначение                              |
|----------------|----------------------------------------|
| `css`          | Собрать TailwindCSS                     |
| `css-watch`    | Собрать TailwindCSS и следить           |
| `build`        | Собрать Docker-образы (включает css)    |
| `up` / `down`  | Запустить / остановить контейнеры       |
| `logs`         | Показать логи контейнеров               |
| `shell`        | Зайти в контейнер                       |

## Технологии

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Jinja2 + HTMX + TailwindCSS + FontAwesome
- **Агент**: psutil + requests + PyInstaller
- **Инфраструктура**: Docker, docker-compose

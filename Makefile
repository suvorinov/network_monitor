.PHONY: help build up up-attach down down-volumes restart logs ps shell shell-root clean build-force exec logs-follow

.DEFAULT_GOAL := help

help:
	@echo "Доступные команды:"
	@echo "  help          - Показать это сообщение"
	@echo "  build         - Собрать образы"
	@echo "  build-force   - Принудительно пересобрать образы"
	@echo "  up            - Запустить сервисы в фоне"
	@echo "  up-attach     - Запустить и остаться в терминале"
	@echo "  down          - Остановить и удалить контейнеры"
	@echo "  down-volumes  - Остановить и удалить контейнеры и тома"
	@echo "  restart       - Перезапустить сервисы"
	@echo "  logs          - Показать логи"
	@echo "  logs-follow   - Показать логи и следить за ними"
	@echo "  ps            - Показать состояние контейнеров"
	@echo "  exec          - Выполнить команду в запущенном контейнере (usage: make exec SERVICE=web CMD='ls')"
	@echo "  shell         - Зайти в контейнер как пользователь"
	@echo "  shell-root    - Зайти в контейнер как root"
	@echo "  clean         - Удалить все неиспользуемые образы, сети, тома и т.д."

build:
	docker-compose build

build-force:
	docker-compose build --no-cache

up:
	docker-compose up -d

up-attach:
	docker-compose up

down:
	docker-compose down

down-volumes:
	docker-compose down -v

restart:
	docker-compose restart

logs:
	docker-compose logs

logs-follow:
	docker-compose logs -f

ps:
	docker-compose ps

exec:
	docker-compose exec $(SERVICE) $(CMD)

shell:
	docker-compose exec web /bin/sh

shell-root:
	docker-compose exec --user=root web /bin/sh

clean:
	docker system prune -af && docker volume prune -f

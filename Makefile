.PHONY: help up down api ai mobile worker test fmt

help:
	@echo "make up        - postgres + redis 기동"
	@echo "make api       - 백엔드 API (apps/api) 로컬 실행"
	@echo "make ai        - 로컬 AI 서버 (apps/ai-server) 실행"
	@echo "make mobile    - Expo dev server 실행"
	@echo "make worker    - 헬스 폴링 워커 실행"
	@echo "make test      - 전체 테스트"

up:
	docker compose up -d postgres redis

down:
	docker compose down

api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

ai:
	cd apps/ai-server && uvicorn app.main:app --port 8800

mobile:
	cd apps/mobile && pnpm start

worker:
	cd apps/api && rq worker -u $${REDIS_URL:-redis://localhost:6379/0} default health

test:
	cd apps/api && pytest -q
	cd apps/ai-server && pytest -q

fmt:
	cd apps/api && ruff check --fix . && ruff format .
	cd apps/ai-server && ruff check --fix . && ruff format .

.PHONY: dev
dev:
	uv run uvicorn app.main:app --port 8001 --reload


.PHONY: sync
sync:
	uv sync


.PHONY: add
add:
	@if [ -z "$(package)" ]; then \
		echo "Error: at least one package required."; \
		echo "  make add package=\"fastapi httpx\""; \
		exit 1; \
	fi
	uv add $(package)


.PHONY: prod
prod:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
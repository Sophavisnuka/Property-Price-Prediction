PYTHON = C:/Users/User/AppData/Local/Programs/Python/Python313/python.exe

.PHONY: dev
dev:
	$(PYTHON) -m uvicorn app.main:app --port 8001 --reload


.PHONY: sync
sync:
	$(PYTHON) -m pip install --prefer-binary -r requirements.txt


.PHONY: add
add:
	@if [ -z "$(package)" ]; then \
		echo "Error: at least one package required."; \
		echo "  make add package=\"fastapi httpx\""; \
		exit 1; \
	fi
	$(PYTHON) -m pip install $(package)


.PHONY: prod
prod:
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000

.PHONY: run-prod
run-prod:
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000
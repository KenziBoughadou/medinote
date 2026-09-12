.PHONY: install check test dev demo contracts corpus benchmark report
install:
	uv sync --frozen --group dev --group eval
	npm --prefix frontend ci
check:
	uv run ruff check backend scripts
	uv run pytest backend/tests
	npm --prefix frontend run lint
	npm --prefix frontend run typecheck
	npm --prefix frontend run test -- --run
	npm --prefix frontend run build
	$(MAKE) corpus contracts
contracts:
	uv run python scripts/export_openapi.py
	npm --prefix frontend run generate:api
	test -z "$$(git diff -- contracts/openapi.json frontend/src/api/schema.d.ts)"
test:
	uv run pytest backend/tests
	npm --prefix frontend run test:e2e
dev:
	uv run uvicorn medinote.main:create_app --factory --host 127.0.0.1
demo:
	npm --prefix frontend run dev -- --open '/?mode=offline'
corpus:
	uv run medinote corpus validate --root .
benchmark:
	@echo 'Exécuter la CLI dans la release active ; voir docs/DEPLOYMENT.md.'
report:
	uv run medinote plan-status --root .
record-demo:
	npm --prefix frontend run record:demo

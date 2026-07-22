.PHONY: setup test evaluate dashboard serve check-rocm acceptance-local

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -e '.[test]'
	npm --prefix dashboard ci

test:
	.venv/bin/python -m pytest
	npm --prefix dashboard run build

evaluate:
	.venv/bin/roborecover evaluate --backend analytic

dashboard:
	npm --prefix dashboard run build

serve: dashboard
	.venv/bin/roborecover serve --backend analytic

check-rocm:
	.venv/bin/roborecover check-rocm

acceptance-local:
	bash scripts/acceptance_local.sh


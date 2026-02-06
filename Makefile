run_linters:
	pre-commit install
	git add .
	pre-commit run

run_tests:
	pytest -vv tests

run_unittests:
	pytest -vv tests/unit

run_integration_tests:
	pytest -vv tests/integration

.PHONY: run run-fake test screenshot clean

run:
	python3 -m web.backend.server

run-fake:
	XIANGQI_FAKE_ENGINE=1 python3 -m web.backend.server

test:
	python3 -m unittest discover -s tests -v

screenshot:
	npx playwright screenshot --viewport-size=1440,960 http://127.0.0.1:8080/ assets/ui-preview.png

clean:
	rm -rf tests/__pycache__ web/__pycache__ web/backend/__pycache__ .pytest_cache test-results playwright-report

.PHONY: run run-lan run-fake run-fake-lan test test-frontend screenshot screenshot-mobile clean

run:
	python3 -m web.backend.server

run-lan:
	XIANGQI_HOST=0.0.0.0 python3 -m web.backend.server

run-fake:
	XIANGQI_FAKE_ENGINE=1 python3 -m web.backend.server

run-fake-lan:
	XIANGQI_FAKE_ENGINE=1 XIANGQI_HOST=0.0.0.0 python3 -m web.backend.server

test:
	python3 -m unittest discover -s tests -v

test-frontend:
	npm run test:frontend

screenshot:
	npx playwright screenshot --viewport-size=1440,960 http://127.0.0.1:8080/ assets/ui-preview.png

screenshot-mobile:
	npm run screenshot:mobile

clean:
	rm -rf tests/__pycache__ web/__pycache__ web/backend/__pycache__ .pytest_cache test-results playwright-report logs node_modules

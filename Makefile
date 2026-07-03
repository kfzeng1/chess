GRADLE ?= /home/zkf/.gradle/wrapper/dists/gradle-8.14.3-all/10utluxaxniiv4wxiphsi49nj/gradle-8.14.3/bin/gradle

.PHONY: run run-lan run-fake run-fake-lan test test-frontend test-android-engine apk-debug screenshot screenshot-mobile clean

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

test-android-engine:
	rm -rf /tmp/xiangqi-android-engine-test
	mkdir -p /tmp/xiangqi-android-engine-test
	javac -d /tmp/xiangqi-android-engine-test \
		android/app/src/main/java/com/kfzeng/xiangqi/core/*.java \
		android/app/src/main/java/com/kfzeng/xiangqi/engine/*.java \
		tools/android-engine-test/EngineSmokeTest.java
	java -cp /tmp/xiangqi-android-engine-test EngineSmokeTest

apk-debug:
	$(GRADLE) -p android assembleDebug

screenshot:
	npx playwright screenshot --viewport-size=1440,960 http://127.0.0.1:8080/ assets/ui-preview.png

screenshot-mobile:
	npm run screenshot:mobile

clean:
	rm -rf tests/__pycache__ web/__pycache__ web/backend/__pycache__ .pytest_cache test-results playwright-report logs android/.gradle android/build android/app/build

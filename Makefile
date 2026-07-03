GRADLE ?= /home/zkf/.gradle/wrapper/dists/gradle-8.14.3-all/10utluxaxniiv4wxiphsi49nj/gradle-8.14.3/bin/gradle

.PHONY: apk-debug test-android-engine assets clean

apk-debug:
	$(GRADLE) -p android assembleDebug

test-android-engine:
	rm -rf /tmp/xiangqi-android-engine-test
	mkdir -p /tmp/xiangqi-android-engine-test
	javac -d /tmp/xiangqi-android-engine-test \
		android/app/src/main/java/com/kfzeng/xiangqi/core/*.java \
		android/app/src/main/java/com/kfzeng/xiangqi/engine/*.java \
		tools/android-engine-test/EngineSmokeTest.java
	java -cp /tmp/xiangqi-android-engine-test EngineSmokeTest

assets:
	python3 tools/asset-generation/render_xiangqi_board.py
	python3 tools/asset-generation/render_xiangqi_pieces.py

clean:
	rm -rf android/.gradle android/build android/app/build

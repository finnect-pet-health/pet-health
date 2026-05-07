// Gradle 의 toolchain 자동 다운로드 활성화 — JDK 21 이 호스트에 없으면 foojay 에서 받음.
plugins {
	id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
}

rootProject.name = "api"

import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "io.github.dovecoteescapee.byedpi"
    compileSdk = 34
    ndkVersion = "27.2.12479018"

    defaultConfig {
        applicationId = "com.companycall.dpibypass"
        minSdk = 24
        targetSdk = 34
        versionCode = 9
        versionName = "1.3.6"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        ndk {
            abiFilters.add("armeabi-v7a")
            abiFilters.add("arm64-v8a")
        }
    }

    buildFeatures {
        buildConfig = true
        viewBinding = true
    }

    val releaseKeystore = rootProject.file("release.keystore")
    val signingPropsFile = rootProject.file("release-signing.properties")
    val signingProps = Properties().apply {
        if (signingPropsFile.exists()) {
            signingPropsFile.inputStream().use { load(it) }
        }
    }

    signingConfigs {
        if (releaseKeystore.exists()) {
            val storePassword = signingProps.getProperty("storePassword")
                ?: error("Missing storePassword in release-signing.properties")
            val keyPassword = signingProps.getProperty("keyPassword")
                ?: error("Missing keyPassword in release-signing.properties")
            val keyAlias = signingProps.getProperty("keyAlias")
                ?: error("Missing keyAlias in release-signing.properties")

            create("release") {
                storeFile = releaseKeystore
                this.storePassword = storePassword
                this.keyAlias = keyAlias
                this.keyPassword = keyPassword
            }
        }
    }

    buildTypes {
        release {
            buildConfigField("String", "VERSION_NAME",  "\"${defaultConfig.versionName}\"")

            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            if (releaseKeystore.exists()) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
        debug {
            buildConfigField("String", "VERSION_NAME",  "\"${defaultConfig.versionName}-debug\"")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
    kotlinOptions {
        jvmTarget = "1.8"
    }
    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }

    // https://android.izzysoft.de/articles/named/iod-scan-apkchecks?lang=en#blobs
    dependenciesInfo {
        // Disables dependency metadata when building APKs.
        includeInApk = false
        // Disables dependency metadata when building Android App Bundles.
        includeInBundle = false
    }
}

dependencies {
    implementation("androidx.coordinatorlayout:coordinatorlayout:1.2.0")
    implementation("net.java.dev.jna:jna:5.15.0@aar")
    implementation("androidx.fragment:fragment-ktx:1.8.2")
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.preference:preference-ktx:1.2.1")
    implementation("com.takisoft.preferencex:preferencex:1.1.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.4")
    implementation("androidx.lifecycle:lifecycle-service:2.8.4")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
}

tasks.register<Exec>("runNdkBuild") {
    group = "build"
    onlyIf { file("src/main/jni/Android.mk").exists() }

    val ndkDir = android.ndkDirectory
    executable = if (System.getProperty("os.name").startsWith("Windows", ignoreCase = true)) {
        "$ndkDir\\ndk-build.cmd"
    } else {
        "$ndkDir/ndk-build"
    }
    setArgs(listOf(
        "NDK_PROJECT_PATH=build/intermediates/ndkBuild",
        "NDK_LIBS_OUT=src/main/jniLibs",
        "APP_BUILD_SCRIPT=src/main/jni/Android.mk",
        "NDK_APPLICATION_MK=src/main/jni/Application.mk"
    ))

    println("Command: $commandLine")
}

tasks.register<Copy>("copyTgWsProxyLibs") {
    group = "build"
    dependsOn("runNdkBuild")
    from("third_party/tgwsproxy") {
        include("**/*.so")
    }
    into("src/main/jniLibs")

    onlyIf {
        val tgwsDir = file("third_party/tgwsproxy")
        if (!tgwsDir.isDirectory) {
            logger.warn("Skipping copyTgWsProxyLibs: ${tgwsDir.path} not found")
            false
        } else {
            true
        }
    }
}

val androidMk = file("src/main/jni/Android.mk")
val tgwsProxyDir = file("third_party/tgwsproxy")
if (androidMk.exists() && tgwsProxyDir.isDirectory) {
    tasks.preBuild {
        dependsOn("copyTgWsProxyLibs")
    }
} else {
    logger.warn(
        "preBuild will not depend on copyTgWsProxyLibs " +
            "(Android.mk exists=${androidMk.exists()}, tgwsproxy exists=${tgwsProxyDir.isDirectory})",
    )
}
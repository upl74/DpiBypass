package io.github.dovecoteescapee.byedpi.core

import android.content.Context
import android.util.Log
import com.sun.jna.Pointer
import java.net.InetSocketAddress
import java.net.Socket
import java.security.SecureRandom
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference

/**
 * Local MTProto proxy with WebSocket tunneling (tg-ws-proxy / Rust core).
 * Telegram connects to 127.0.0.1 — traffic exits via WSS, not raw MTProto.
 */
object TgWsProxy {
    private const val TAG = "TgWsProxy"
    private const val PREFS = "tgws_proxy"
    private const val KEY_SECRET = "secret_key"
    private const val STARTUP_TIMEOUT_MS = 10_000L
    private const val PORT_CHECK_TIMEOUT_MS = 5_000L

    const val BIND_IP = "127.0.0.1"
    const val DEFAULT_PORT = 1443

    @Volatile
    private var running = false

    @Volatile
    private var nativeAvailable: Boolean? = null

    fun isNativeAvailable(): Boolean {
        nativeAvailable?.let { return it }
        return try {
            TgWsProxyLibrary.load()
            nativeAvailable = true
            true
        } catch (t: Throwable) {
            Log.e(TAG, "libtgwsproxy unavailable", t)
            nativeAvailable = false
            false
        }
    }

    fun start(context: Context, port: Int = DEFAULT_PORT): String {
        if (!isNativeAvailable()) {
            throw UnsatisfiedLinkError("libtgwsproxy.so not found in APK")
        }

        if (running) {
            return proxyUrl(BIND_IP, port, ensureSecret(context))
        }

        val secret = ensureSecret(context)
        val cacheDir = context.cacheDir.absolutePath
        val startCode = AtomicInteger(-1)
        val startError = AtomicReference<Throwable?>(null)
        val latch = CountDownLatch(1)

        Thread({
            try {
                TgWsProxyLibrary.INSTANCE.apply {
                    SetPoolSize(4)
                    SetCfProxyCacheDir(cacheDir)
                    SetCfProxyConfig(1, 1, "")
                    startCode.set(StartProxy(BIND_IP, port, "", secret, 1))
                }
            } catch (t: Throwable) {
                startError.set(t)
            } finally {
                latch.countDown()
            }
        }, "TgWsProxyStart").apply {
            isDaemon = true
            start()
        }

        if (!latch.await(STARTUP_TIMEOUT_MS, TimeUnit.MILLISECONDS)) {
            throw IllegalStateException("TgWsProxy start timed out")
        }

        startError.get()?.let { throw it }
        if (startCode.get() != 0) {
            throw IllegalStateException("TgWsProxy StartProxy failed: ${startCode.get()}")
        }

        if (!waitForPort(BIND_IP, port, PORT_CHECK_TIMEOUT_MS)) {
            stop()
            throw IllegalStateException("TgWsProxy port $port not listening")
        }

        running = true
        val fullSecret = readCString { TgWsProxyLibrary.INSTANCE.GetSecretWithPrefix() }
            ?: "dd$secret"
        Log.i(TAG, "Started on $BIND_IP:$port")
        return proxyUrl(BIND_IP, port, fullSecret)
    }

    fun stop() {
        if (!running && nativeAvailable != true) return
        try {
            if (isNativeAvailable()) {
                TgWsProxyLibrary.INSTANCE.StopProxy()
            }
        } catch (e: Throwable) {
            Log.w(TAG, "StopProxy failed", e)
        } finally {
            running = false
        }
    }

    val isRunning: Boolean
        get() = running

    fun proxyUrl(host: String, port: Int, secretWithPrefix: String): String =
        "https://t.me/proxy?server=$host&port=$port&secret=$secretWithPrefix"

    private fun waitForPort(host: String, port: Int, timeoutMs: Long): Boolean {
        val deadline = System.currentTimeMillis() + timeoutMs
        while (System.currentTimeMillis() < deadline) {
            if (isPortOpen(host, port, 500)) return true
            Thread.sleep(100)
        }
        return false
    }

    private fun isPortOpen(host: String, port: Int, timeoutMs: Int): Boolean =
        try {
            Socket().use { socket ->
                socket.connect(InetSocketAddress(host, port), timeoutMs)
                true
            }
        } catch (_: Exception) {
            false
        }

    private fun ensureSecret(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val current = prefs.getString(KEY_SECRET, "")?.trim().orEmpty()
        if (isValidSecret(current)) return current

        val generated = generateSecret()
        prefs.edit().putString(KEY_SECRET, generated).apply()
        return generated
    }

    private fun generateSecret(): String {
        val bytes = ByteArray(16)
        SecureRandom().nextBytes(bytes)
        return bytes.joinToString("") { "%02x".format(it) }
    }

    private fun isValidSecret(value: String): Boolean =
        value.length == 32 && value.all { it.isDigit() || it.lowercaseChar() in 'a'..'f' }

    private inline fun readCString(getter: () -> Pointer?): String? {
        val ptr = getter() ?: return null
        return try {
            ptr.getString(0)
        } finally {
            TgWsProxyLibrary.INSTANCE.FreeString(ptr)
        }
    }
}

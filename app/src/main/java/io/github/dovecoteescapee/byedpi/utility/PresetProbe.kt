package io.github.dovecoteescapee.byedpi.utility

import android.util.Log
import java.net.HttpURLConnection
import java.net.InetSocketAddress
import java.net.Proxy
import java.net.URL
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException
import javax.net.ssl.HttpsURLConnection
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withTimeout

/** HTTPS check through local ByeDPI SOCKS — YouTube + Instagram. */
object PresetProbe {
    private val TAG = PresetProbe::class.java.simpleName

    private const val PER_URL_TIMEOUT_MS = 4_000
    private const val PRESET_DEADLINE_MS = 10_000L

    private val YOUTUBE_URLS = arrayOf(
        "https://www.youtube.com/generate_204",
        "https://youtubei.googleapis.com/",
        "https://www.gstatic.com/generate_204",
    )

    private val INSTAGRAM_URLS = arrayOf(
        "https://www.instagram.com/",
        "https://i.instagram.com/",
    )

    /** Preset must bypass DPI for YouTube (2+ URLs) and Instagram (1+ URL). */
    suspend fun testBypass(socksPort: Int): Boolean = withTimeout(PRESET_DEADLINE_MS) {
        coroutineScope {
            val proxy = Proxy(Proxy.Type.SOCKS, InetSocketAddress("127.0.0.1", socksPort))

            val ytJobs = YOUTUBE_URLS.map { url ->
                async(Dispatchers.IO) { testUrlBounded(proxy, url) }
            }
            val igJobs = INSTAGRAM_URLS.map { url ->
                async(Dispatchers.IO) { testUrlBounded(proxy, url) }
            }

            val ytOk = ytJobs.awaitAll().count { it } >= 2
            val igOk = igJobs.awaitAll().any { it }
            Log.i(TAG, "Probe youtube=$ytOk instagram=$igOk (port=$socksPort)")
            ytOk && igOk
        }
    }

    /** Force wall-clock timeout — HttpURLConnection can ignore connectTimeout on SOCKS. */
    private fun testUrlBounded(proxy: Proxy, urlString: String): Boolean {
        val pool = Executors.newSingleThreadExecutor()
        return try {
            val future = pool.submit<Boolean> {
                testUrl(proxy, urlString, PER_URL_TIMEOUT_MS)
            }
            future.get(PER_URL_TIMEOUT_MS.toLong() + 500L, TimeUnit.MILLISECONDS)
        } catch (_: TimeoutException) {
            Log.d(TAG, "Probe timeout: $urlString")
            false
        } catch (e: Exception) {
            Log.d(TAG, "Probe $urlString: ${e.javaClass.simpleName}")
            false
        } finally {
            pool.shutdownNow()
        }
    }

    private fun testUrl(proxy: Proxy, urlString: String, timeoutMs: Int): Boolean {
        var conn: HttpURLConnection? = null
        return try {
            conn = (URL(urlString).openConnection(proxy) as HttpsURLConnection).apply {
                connectTimeout = timeoutMs
                readTimeout = timeoutMs
                instanceFollowRedirects = false
                requestMethod = "GET"
            }
            conn.responseCode in 200..499
        } catch (e: Exception) {
            Log.d(TAG, "Probe $urlString: ${e.javaClass.simpleName}")
            false
        } finally {
            conn?.disconnect()
        }
    }
}

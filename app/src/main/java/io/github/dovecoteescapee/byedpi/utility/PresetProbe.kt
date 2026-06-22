package io.github.dovecoteescapee.byedpi.utility

import android.util.Log
import java.net.HttpURLConnection
import java.net.InetSocketAddress
import java.net.Proxy
import java.net.URL
import javax.net.ssl.HttpsURLConnection

/** HTTPS check through local ByeDPI SOCKS — socket open ≠ bypass works. */
object PresetProbe {
    private val TAG = PresetProbe::class.java.simpleName

    private val TEST_URLS = arrayOf(
        "https://www.youtube.com/generate_204",
        "https://youtubei.googleapis.com/",
        "https://www.gstatic.com/generate_204",
        "https://i.ytimg.com/generate_204",
    )

    /** At least two endpoints must respond — one success is not enough on strict DPI. */
    fun testBypass(socksPort: Int, timeoutMs: Int = 12_000): Boolean {
        val proxy = Proxy(Proxy.Type.SOCKS, InetSocketAddress("127.0.0.1", socksPort))
        var ok = 0
        for (url in TEST_URLS) {
            if (testUrl(proxy, url, timeoutMs)) {
                ok++
                Log.i(TAG, "Probe OK ($ok): $url")
                if (ok >= 2) return true
            }
        }
        Log.w(TAG, "Probe failed: $ok/${TEST_URLS.size} URLs (port=$socksPort)")
        return false
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

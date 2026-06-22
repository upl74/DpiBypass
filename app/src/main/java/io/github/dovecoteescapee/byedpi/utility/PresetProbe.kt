package io.github.dovecoteescapee.byedpi.utility

import android.util.Log
import java.net.HttpURLConnection
import java.net.InetSocketAddress
import java.net.Proxy
import java.net.URL
import javax.net.ssl.HttpsURLConnection

/** Quick HTTPS check through local ByeDPI SOCKS — socket open ≠ bypass works. */
object PresetProbe {
    private val TAG = PresetProbe::class.java.simpleName

    private val TEST_URLS = arrayOf(
        "https://www.youtube.com/generate_204",
        "https://youtubei.googleapis.com/",
        "https://gstatic.com/generate_204",
    )

    fun testBypass(socksPort: Int, timeoutMs: Int = 10_000): Boolean {
        val proxy = Proxy(Proxy.Type.SOCKS, InetSocketAddress("127.0.0.1", socksPort))
        for (url in TEST_URLS) {
            if (testUrl(proxy, url, timeoutMs)) {
                Log.i(TAG, "Probe OK via $url")
                return true
            }
        }
        Log.w(TAG, "Probe failed on all URLs (port=$socksPort)")
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
            val code = conn.responseCode
            code in 200..499
        } catch (e: Exception) {
            Log.d(TAG, "Probe $urlString: ${e.javaClass.simpleName}")
            false
        } finally {
            conn?.disconnect()
        }
    }
}

package io.github.dovecoteescapee.byedpi.utility

import android.util.Log
import java.net.HttpURLConnection
import java.net.InetSocketAddress
import java.net.Proxy
import java.net.URL
import javax.net.ssl.HttpsURLConnection

/** HTTPS check through local ByeDPI SOCKS — must work for YouTube and Instagram. */
object PresetProbe {
    private val TAG = PresetProbe::class.java.simpleName

    private val YOUTUBE_URLS = arrayOf(
        "https://www.youtube.com/generate_204",
        "https://youtubei.googleapis.com/",
        "https://www.gstatic.com/generate_204",
    )

    private val INSTAGRAM_URLS = arrayOf(
        "https://www.instagram.com/",
        "https://i.instagram.com/",
        "https://graph.instagram.com/",
    )

    /** Preset must bypass DPI for both YouTube (2+ URLs) and Instagram (1+ URL). */
    fun testBypass(socksPort: Int, timeoutMs: Int = 10_000): Boolean {
        val proxy = Proxy(Proxy.Type.SOCKS, InetSocketAddress("127.0.0.1", socksPort))
        val ytOk = countOk(proxy, YOUTUBE_URLS, timeoutMs) >= 2
        val igOk = countOk(proxy, INSTAGRAM_URLS, timeoutMs) >= 1
        Log.i(TAG, "Probe youtube=$ytOk instagram=$igOk (port=$socksPort)")
        return ytOk && igOk
    }

    private fun countOk(proxy: Proxy, urls: Array<String>, timeoutMs: Int): Int {
        var ok = 0
        for (url in urls) {
            if (testUrl(proxy, url, timeoutMs)) {
                ok++
                Log.i(TAG, "Probe OK: $url")
            }
        }
        return ok
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

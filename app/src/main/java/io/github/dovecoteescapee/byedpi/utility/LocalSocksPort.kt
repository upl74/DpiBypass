package io.github.dovecoteescapee.byedpi.utility

import android.util.Log
import java.net.ServerSocket

/**
 * Ephemeral local SOCKS port per service session so other apps cannot rely on a fixed :1080.
 */
object LocalSocksPort {
    private val portPattern = Regex("""-p\s+\d+""")

    fun allocate(): Int {
        repeat(8) { attempt ->
            val port = ServerSocket(0).use { it.localPort }
            try {
                ServerSocket(port).use { return port }
            } catch (_: Exception) {
                Log.w("LocalSocksPort", "Port $port busy, retry ${attempt + 1}/8")
            }
        }
        return 1080
    }

    fun patchCmdPort(cmd: String, port: Int): String =
        if (portPattern.containsMatchIn(cmd)) {
            portPattern.replace(cmd, "-p $port")
        } else {
            "$cmd -p $port"
        }
}

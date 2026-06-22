package io.github.dovecoteescapee.byedpi.utility

import io.github.dovecoteescapee.byedpi.core.ByeDpiProxyCmdPreferences
import io.github.dovecoteescapee.byedpi.core.ByeDpiProxyPreferences
import io.github.dovecoteescapee.byedpi.core.ByeDpiProxyUIPreferences

object PresetLabel {
    fun fromPreferences(preferences: ByeDpiProxyPreferences): String = when (preferences) {
        is ByeDpiProxyCmdPreferences -> fromCmd(preferences.args.joinToString(" "))
        is ByeDpiProxyUIPreferences -> "UI preset"
    }

    fun fromCmd(cmd: String): String {
        val c = cmd.replace(Regex("\\s+"), " ").trim()
        return when {
            c.contains("-H:\"") -> "Google whitelist"
            c.contains("-n yandex.ru") -> "MTS Fake"
            c.contains("-o1 -s1+s") && c.contains("-d35+s") -> "MTS Universal"
            c.contains("-o1 -s1+s") && c.contains("-Ku -a3") -> "MTS #405 QUIC"
            c.contains("-o1 -s1+s") -> "MTS #405"
            c.contains("-Ku -a8") -> "MTS alt"
            c.contains("-Ku -a3") && c.contains("-S") -> "Mobile YouTube"
            c.contains("-Kt,h -d1 -d3+s -s6+s -d9+s -r1+s -S") -> "Hybrid TG+YT"
            c.contains("-r1+s -S") -> "YouTube TLS"
            c.contains("-d1 -f-1 -t 8 -Ku") -> "Minimal UDP"
            c.contains("-Ku") -> "Mobile / QUIC"
            else -> "Custom"
        }
    }
}

package io.github.dovecoteescapee.byedpi.utility



import android.content.Context

import androidx.preference.PreferenceManager

import io.github.dovecoteescapee.byedpi.core.ByeDpiProxyUIPreferences



object DpiDefaults {

    private const val PREFS_VERSION_KEY = "dpi_defaults_version"

    const val CURRENT_VERSION = 13



    private const val BIND = "-i 127.0.0.1 -p 1080"



    /** Full GoodbyeDPI TLS ladder (user-tuned for YouTube). */
    private const val LADDER_FULL =

        "-d1 -d3+s -s6+s -d9+s -s12+s -d15+s -s20+s -d25+s -s30+s -d35+s"

    /** GoodbyeDPI ladder for TLS/HTTP only (SNI-relative offsets). */

    private const val LADDER_TLS = LADDER_FULL



    /** Raw TCP/UDP tricks for MTProto (no +s — not TLS). */

    private const val MTProto_RAW = "-d1 -f-1 -t 8 -r1 -Ku -As -d3 -f-1 -t 8 -Ku"



    /**

     * Hybrid: YouTube/Instagram via TLS ladder; Telegram MTProto via raw fake/disorder.

     * Old GoodbyeDPI preset applied SNI splits to all TCP and broke MTProto.

     */

    const val PRESET_HYBRID =

        "$BIND -Kt,h $LADDER_TLS -r1+s -S -a1 -As -Kt,h $LADDER_TLS -S -a1 $MTProto_RAW"



    const val PRESET_GOODBYEDPI = PRESET_HYBRID



    const val PRESET_GOODBYEDPI_LITE =

        "$BIND -Kt,h -d1 -d3+s -s6+s -d9+s -r1+s -S -a1 -d1 -f-1 -t 8 -Ku"



    const val PRESET_TELEGRAM = "$BIND $MTProto_RAW"



    const val PRESET_UNIVERSAL = PRESET_HYBRID



    /** YouTube / Instagram — пользовательский пресет (двойная TLS-лестница + auto ssl_err). */
    const val PRESET_YOUTUBE =

        "$BIND $LADDER_FULL -r1+s -S -a1 -As $LADDER_FULL -S -a1"

    /** @deprecated use [PRESET_YOUTUBE] */
    const val PRESET_MEDIA_TCP =

        "$BIND -Kt,h -d1 -d3+s -s6+s -d9+s -s20+s -r1+s -S"



    const val PRESET_LIGHT = "$BIND -s0 -o1 -d1 -r1+s"



    const val PRESET_MINIMAL = "$BIND -d1 -f-1 -t 8 -Ku"



    fun presetArgs(preset: String): String? = when (preset) {

        "hybrid", "goodbyedpi" -> PRESET_HYBRID

        "telegram" -> PRESET_TELEGRAM

        "universal" -> PRESET_UNIVERSAL

        "youtube" -> PRESET_YOUTUBE

        "youtube_video" -> PRESET_YOUTUBE

        "media_tcp" -> PRESET_MEDIA_TCP

        "youtube_classic" -> PRESET_MEDIA_TCP

        "light" -> PRESET_LIGHT

        else -> null

    }



    fun uiPreferences(port: Int = 1080): ByeDpiProxyUIPreferences =
        ByeDpiProxyUIPreferences(
            ip = "127.0.0.1",
            port = port,

            desyncHttp = true,

            desyncHttps = true,

            desyncUdp = true,

            desyncMethod = ByeDpiProxyUIPreferences.DesyncMethod.Disorder,

            splitPosition = 1,

            splitAtHost = true,

            fakeTtl = 8,

            tlsRecordSplit = true,

            tlsRecordSplitPosition = 1,

            tlsRecordSplitAtSni = true,

            udpFakeCount = 1,

        )



    fun applyIfNeeded(context: Context) {

        val prefs = PreferenceManager.getDefaultSharedPreferences(context)

        if (prefs.getInt(PREFS_VERSION_KEY, 0) >= CURRENT_VERSION) return



        prefs.edit()

            .putInt(PREFS_VERSION_KEY, CURRENT_VERSION)

            .putString("byedpi_mode", "vpn")

            .putBoolean("only_target_apps", true)

            .putBoolean("byedpi_enable_cmd_settings", true)

            .putBoolean("ipv6_enable", true)

            .putBoolean("tg_ws_telegram", true)
            .putBoolean("tg_ws_auto_apply", true)

            .putString("byedpi_cmd_preset", "youtube")

            .putString("byedpi_cmd_args", PRESET_YOUTUBE)

            .putString("byedpi_proxy_ip", "127.0.0.1")

            .putString("byedpi_proxy_port", "1080")

            .putString("dns_ip", "8.8.8.8")

            .apply()

    }

}


package io.github.dovecoteescapee.byedpi.utility



import android.content.Context

import androidx.preference.PreferenceManager

import io.github.dovecoteescapee.byedpi.core.ByeDpiProxyUIPreferences



object DpiDefaults {

    private const val PREFS_VERSION_KEY = "dpi_defaults_version"

    const val CURRENT_VERSION = 20



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



    /** YouTube / Instagram — проверенная TLS-лестница (без -H: whitelist ломает GMS/gstatic). */
    const val PRESET_YOUTUBE_BASE =
        "$BIND $LADDER_FULL -r1+s -S -a1 -As $LADDER_FULL -S -a1"

    /** LTE/5G: дополнительно QUIC/UDP fake. */
    const val PRESET_YOUTUBE_MOBILE =
        "$BIND -Ku -a3 -Kt,h $LADDER_FULL -r1+s -S -a1 -As -Kt,h $LADDER_FULL -S -a1"

    /**
     * МТС #405 Android (lav89): -Qr заменён на -f-1 -r2+s.
     * @see <a href="https://github.com/hufrea/byedpi/issues/405">byedpi #405</a>
     */
    const val PRESET_MTS_405 =
        "$BIND -Kt,h -o1 -s1+s -s3+s -s6+s -s9+s -s12+s -s15+s -s20+s -s30+s " +
        "-a1 -At,r,s -d1 -f-1 -r2+s -An"

    /** МТС #405 + QUIC fake (googlevideo). */
    const val PRESET_MTS_405_QUIC =
        "$BIND -Ku -a3 -Kt,h -o1 -s1+s -s3+s -s6+s -s9+s -s12+s -s15+s -s20+s -s30+s " +
        "-a1 -At,r,s -d1 -f-1 -r2+s -An"

    /** МТС — Fake + split (ByeDPIAndroid #41). */
    const val PRESET_MTS_FAKE =
        "$BIND -Kt,h -d1 -d3+s -s6+s -d9+s -r1+s -a1 -Mh,d,r -d1 -f-1 -t 7 -n yandex.ru -e a -Ku -a3"

    /** @deprecated -H whitelist отбрасывает домены вне списка — не использовать в auto-probe. */
    fun mtsHostsPreset(context: Context): String {
        val h = HostsAssets.googleHostsSwitch(context)
        return "$BIND $h -Kt,h -o1 -s1+s -s3+s -s6+s -s9+s -s12+s -s15+s -s20+s -s30+s " +
            "-a1 -An -Kt,h -At,r,s -d1 -f-1 -r2+s -An -Ku -a3"
    }

    /** @deprecated use [PRESET_MTS_405] */
    const val PRESET_MTS_YOUTUBE = PRESET_MTS_405_QUIC

    /** Запасной для МТС — disorder + fake + UDP. */
    const val PRESET_MTS_ALT =
        "$BIND -Ku -a8 -Kt,h -o1 -d1 -d3+s -s6+s -d9+s -s12+s -r1+s -a1 " +
        "-At,r,s -d1 -f-1 -t 8 -r2+s -An"

    const val PRESET_YOUTUBE = PRESET_YOUTUBE_BASE

    fun youtubePreset(_context: Context): String = PRESET_YOUTUBE_BASE

    fun youtubeMobilePreset(_context: Context): String = PRESET_YOUTUBE_MOBILE

    fun mtsYoutubePreset(_context: Context): String = PRESET_MTS_405_QUIC

    fun litePreset(_context: Context): String = PRESET_GOODBYEDPI_LITE

    fun defaultYoutubePreset(context: Context): String = when {
        NetworkHelper.isMts(context) -> PRESET_MTS_405_QUIC
        NetworkHelper.isCellular(context) -> PRESET_YOUTUBE_MOBILE
        else -> PRESET_YOUTUBE_BASE
    }

    /** МТС OOB + общая TLS-лестница — YouTube и Instagram без -H whitelist. */
    const val PRESET_MTS_UNIVERSAL =
        "$BIND -Ku -a3 -Kt,h -o1 -s1+s -s3+s -s6+s -s9+s -s12+s -a1 -At,r,s -d1 -f-1 -r2+s -An " +
        "-Kt,h $LADDER_FULL -r1+s -a1 -As -Kt,h $LADDER_FULL -r1+s -a1"

    /** Порядок кандидатов для runtime-probe на сотовой сети (без -H: whitelist рвёт YT). */
    fun cellularProbePresets(context: Context, savedCmd: String?): List<String> {
        val candidates = mutableListOf<String>()
        if (NetworkHelper.isMts(context)) {
            candidates += PRESET_MTS_UNIVERSAL
            candidates += PRESET_MTS_405_QUIC
            candidates += PRESET_MTS_405
            candidates += PRESET_MTS_FAKE
            candidates += PRESET_MTS_ALT
        }
        candidates += PRESET_HYBRID
        candidates += PRESET_YOUTUBE_MOBILE
        if (!NetworkHelper.isMts(context)) {
            candidates += PRESET_MTS_UNIVERSAL
            candidates += PRESET_MTS_405_QUIC
        }
        savedCmd?.trim()?.takeIf { it.isNotEmpty() }?.let { candidates += it }
        candidates += PRESET_YOUTUBE_BASE
        candidates += PRESET_GOODBYEDPI_LITE
        candidates += PRESET_MINIMAL
        return candidates.distinct()
    }

    fun cellularFallbackPreset(context: Context): String = when {
        NetworkHelper.isMts(context) -> PRESET_MTS_UNIVERSAL
        NetworkHelper.isCellular(context) -> PRESET_HYBRID
        else -> PRESET_YOUTUBE_BASE
    }

    /** @deprecated use [PRESET_YOUTUBE] */
    const val PRESET_MEDIA_TCP =

        "$BIND -Kt,h -d1 -d3+s -s6+s -d9+s -s20+s -r1+s -S"



    const val PRESET_LIGHT = "$BIND -s0 -o1 -d1 -r1+s"



    const val PRESET_MINIMAL = "$BIND -d1 -f-1 -t 8 -Ku"



    fun presetArgs(context: Context, preset: String): String? = when (preset) {

        "hybrid", "goodbyedpi" -> PRESET_HYBRID

        "telegram" -> PRESET_TELEGRAM

        "universal" -> PRESET_UNIVERSAL

        "youtube", "youtube_video" -> defaultYoutubePreset(context)

        "mts" -> mtsYoutubePreset(context)

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
        val version = prefs.getInt(PREFS_VERSION_KEY, 0)
        if (version >= CURRENT_VERSION) return

        val editor = prefs.edit().putInt(PREFS_VERSION_KEY, CURRENT_VERSION)
        when {
            version == 0 -> applyFreshInstall(editor, context)
            version < 19 -> applyMtsTunnelFix(editor, context, prefs)
            version < 20 -> applyDualServiceProbeFix(editor, context, prefs)
        }
        editor.apply()
    }

    private fun applyFreshInstall(
        editor: android.content.SharedPreferences.Editor,
        context: Context,
    ) {
        editor
            .putString("byedpi_mode", "vpn")
            .putBoolean("only_target_apps", true)
            .putBoolean("byedpi_enable_cmd_settings", true)
            .putBoolean("ipv6_enable", false)
            .putBoolean("tg_ws_telegram", true)
            .putBoolean("tg_ws_auto_apply", true)
            .putString("byedpi_cmd_preset", "youtube")
            .putString("byedpi_cmd_args", defaultYoutubePreset(context))
            .putString("byedpi_proxy_ip", "127.0.0.1")
            .putString("byedpi_proxy_port", "1080")
            .putString("dns_ip", "")
    }

    /** v20: probe YouTube+Instagram; сброс YT-only кэша пресета. */
    private fun applyDualServiceProbeFix(
        editor: android.content.SharedPreferences.Editor,
        context: Context,
        prefs: android.content.SharedPreferences,
    ) {
        editor.remove("byedpi_cellular_working_cmd")
        val preset = prefs.getString("byedpi_cmd_preset", "youtube") ?: "youtube"
        if (preset in YOUTUBE_PRESETS) {
            editor.putString("byedpi_cmd_args", cellularFallbackPreset(context))
        }
    }

    /** v19: полный туннель на LTE, публичный DNS, сброс кэша пресета. */
    private fun applyMtsTunnelFix(
        editor: android.content.SharedPreferences.Editor,
        context: Context,
        prefs: android.content.SharedPreferences,
    ) {
        val preset = prefs.getString("byedpi_cmd_preset", "youtube") ?: "youtube"
        if (preset in YOUTUBE_PRESETS) {
            editor.putString("byedpi_cmd_args", defaultYoutubePreset(context))
        }
        editor.remove("byedpi_cellular_working_cmd")
        editor.putBoolean("ipv6_enable", false)
        if (NetworkHelper.isCellular(context) || NetworkHelper.isMts(context)) {
            editor.putString("dns_ip", "9.9.9.9")
        }
    }

    private val YOUTUBE_PRESETS = setOf(
        "youtube",
        "youtube_video",
        "universal",
        "hybrid",
        "goodbyedpi",
        "media_tcp",
        "youtube_classic",
    )

}


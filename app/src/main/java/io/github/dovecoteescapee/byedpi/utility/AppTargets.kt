package io.github.dovecoteescapee.byedpi.utility

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build

object AppTargets {
    val knownPackages: List<String> = listOf(
        // Telegram
        "org.telegram.messenger",
        "org.telegram.messenger.web",
        "org.telegram.messenger.beta",
        "org.thunderdog.challegram",
        "nekox.messenger",
        "org.telegram.plus",
        "com.exteragram.messenger",
        // YouTube / ReVanced / Music
        "com.google.android.youtube",
        "app.revanced.android.youtube",
        "com.vanced.android.youtube",
        "com.google.android.apps.youtube.vanced",
        "com.google.android.apps.youtube.music",
        "com.google.android.apps.youtube.kids",
        // Browser / WebView (YouTube links, login)
        "com.android.chrome",
        "com.google.android.webview",
        // Instagram
        "com.instagram.android",
        "com.instagram.lite",
        // Google Play Services (stock YouTube / часть Instagram)
        "com.google.android.gms",
        "com.google.android.gsf",
        // Meta / Instagram
        "com.facebook.services",
        "com.facebook.system",
        "com.facebook.appmanager",
        // microG (ReVanced)
        "com.mgoogle.android.gms",
        "app.revanced.android.gms",
    )

    private val packageHints = listOf(
        "telegram",
        "youtube",
        "youtub",
        "revanced",
        "instagram",
        "google.android.apps.youtube",
    )

    private val telegramExact = setOf(
        "org.telegram.messenger",
        "org.telegram.messenger.web",
        "org.telegram.messenger.beta",
        "org.thunderdog.challegram",
        "nekox.messenger",
        "org.telegram.plus",
        "com.exteragram.messenger",
        "com.radolyn.ayugram",
        "tw.nekomimi.nekogram",
        "app.nicegram",
    )

    fun isTelegramPackage(packageName: String): Boolean =
        telegramExact.contains(packageName) ||
            packageName.contains("telegram", ignoreCase = true) ||
            packageName.contains("nekogram", ignoreCase = true) ||
            packageName.contains("ayugram", ignoreCase = true)

    fun isMediaPackage(packageName: String): Boolean =
        packageName.contains("youtube", ignoreCase = true) ||
            packageName.contains("youtub", ignoreCase = true) ||
            packageName.contains("instagram", ignoreCase = true) ||
            packageName.contains("revanced", ignoreCase = true) ||
            packageName.contains("vanced", ignoreCase = true) ||
            packageName.contains("mgoogle", ignoreCase = true) ||
            packageName.contains("facebook", ignoreCase = true) ||
            packageName == "com.android.chrome" ||
            packageName == "com.google.android.webview" ||
            packageName == "com.google.android.gms" ||
            packageName == "com.google.android.gsf"

    /** Packages that must share the VPN tunnel with YouTube/Instagram. */
    private val vpnCompanionPackages: List<String> = listOf(
        "com.google.android.gms",
        "com.google.android.gsf",
        "com.android.chrome",
        "com.google.android.webview",
        "com.facebook.services",
        "com.facebook.system",
        "com.facebook.appmanager",
        "com.mgoogle.android.gms",
        "app.revanced.android.gms",
    )

    /**
     * Apps to capture in per-app VPN mode.
     * When [excludeTelegram] is true, TG uses WS proxy and must not use the tunnel.
     */
    fun vpnCapturePackages(context: Context, excludeTelegram: Boolean): List<String> {
        val pm = context.packageManager
        val base = installedOnDevice(context)
        val primary = if (excludeTelegram) {
            base.filterNot { isTelegramPackage(it) }
        } else {
            base
        }
        val needsCompanions = primary.any { isMediaPackage(it) }
        val companions = if (needsCompanions) {
            vpnCompanionPackages.filter { isInstalled(pm, it) }
        } else {
            emptyList()
        }
        return (primary + companions).distinct()
    }

    fun installedOnDevice(context: Context): List<String> {
        val pm = context.packageManager
        val fromKnown = knownPackages.filter { pkg -> isInstalled(pm, pkg) }
        val fromDiscovery = discoverByLauncher(pm)
        return (fromKnown + fromDiscovery).distinct()
    }

    private fun isInstalled(pm: PackageManager, packageName: String): Boolean =
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                pm.getPackageInfo(packageName, PackageManager.PackageInfoFlags.of(0))
            } else {
                @Suppress("DEPRECATION")
                pm.getPackageInfo(packageName, 0)
            }
            true
        } catch (_: PackageManager.NameNotFoundException) {
            false
        }

    private fun discoverByLauncher(pm: PackageManager): List<String> {
        val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        val flags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            PackageManager.MATCH_ALL
        } else {
            0
        }

        @Suppress("DEPRECATION")
        return pm.queryIntentActivities(intent, flags)
            .map { it.activityInfo.packageName }
            .distinct()
            .filter { pkg -> packageHints.any { hint -> pkg.contains(hint, ignoreCase = true) } }
    }
}

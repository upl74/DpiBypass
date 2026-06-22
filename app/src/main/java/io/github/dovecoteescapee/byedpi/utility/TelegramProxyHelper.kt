package io.github.dovecoteescapee.byedpi.utility

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.widget.Toast
import io.github.dovecoteescapee.byedpi.R

object TelegramProxyHelper {
    private val telegramPackages = listOf(
        "org.telegram.messenger",
        "org.telegram.messenger.web",
        "org.telegram.messenger.beta",
        "org.thunderdog.challegram",
        "org.telegram.plus",
        "com.exteragram.messenger",
        "nekox.messenger",
        "com.radolyn.ayugram",
        "tw.nekomimi.nekogram",
        "xyz.nextalone.nagram",
        "app.nicegram",
    )

    private val allowedHosts = setOf("127.0.0.1", "localhost", "::1")

    fun isLocalWsProxyUrl(proxyUrl: String?): Boolean {
        if (proxyUrl.isNullOrBlank()) return false
        return try {
            val uri = Uri.parse(proxyUrl)
            if (uri.scheme != "https" || uri.host != "t.me" || uri.path != "/proxy") {
                return false
            }
            val server = uri.getQueryParameter("server")?.trim()?.lowercase() ?: return false
            server in allowedHosts
        } catch (_: Exception) {
            false
        }
    }

    fun applyLocalWsProxy(context: Context, proxyUrl: String) {
        if (!isLocalWsProxyUrl(proxyUrl)) {
            return
        }

        val pm = context.packageManager
        val installed = telegramPackages.filter { pkg ->
            try {
                pm.getPackageInfo(pkg, 0)
                true
            } catch (_: PackageManager.NameNotFoundException) {
                false
            }
        }

        if (installed.isEmpty()) {
            Toast.makeText(context, R.string.telegram_open_failed, Toast.LENGTH_SHORT).show()
            return
        }

        val intents = installed.map { pkg ->
            Intent(Intent.ACTION_VIEW, Uri.parse(proxyUrl)).apply {
                setPackage(pkg)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
        }

        try {
            if (intents.size == 1) {
                context.startActivity(intents.first())
            } else {
                val chooser = Intent.createChooser(intents.first(), null)
                chooser.putExtra(Intent.EXTRA_INITIAL_INTENTS, intents.drop(1).toTypedArray())
                chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                context.startActivity(chooser)
            }
            Toast.makeText(context, R.string.telegram_ws_applied, Toast.LENGTH_SHORT).show()
        } catch (_: Exception) {
            Toast.makeText(context, R.string.telegram_open_failed, Toast.LENGTH_SHORT).show()
        }
    }

    fun openMtprotoLink(context: Context, link: String) {
        try {
            context.startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse(link)).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                },
            )
        } catch (_: Exception) {
            Toast.makeText(context, R.string.telegram_open_failed, Toast.LENGTH_SHORT).show()
        }
    }
}

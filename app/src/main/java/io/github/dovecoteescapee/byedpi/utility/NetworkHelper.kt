package io.github.dovecoteescapee.byedpi.utility

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.telephony.TelephonyManager

object NetworkHelper {
    /** MTS / MGTS (Россия) — MCC 250. */
    private val MTS_OPERATOR_CODES = setOf(
        "25001",
        "25011",
        "25039",
    )

    fun isCellular(context: Context): Boolean {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            ?: return false
        val network = cm.activeNetwork ?: return false
        val caps = cm.getNetworkCapabilities(network) ?: return false
        return caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)
    }

    fun isMts(context: Context): Boolean {
        val tm = context.getSystemService(Context.TELEPHONY_SERVICE) as? TelephonyManager
            ?: return false
        val code = tm.networkOperator?.takeIf { it.length >= 5 }
            ?: tm.simOperator?.takeIf { it.length >= 5 }
        if (code != null && code in MTS_OPERATOR_CODES) {
            return true
        }
        val label = listOf(tm.networkOperatorName, tm.simOperatorName)
            .filterNotNull()
            .joinToString(" ")
            .lowercase()
        return label.contains("mts") ||
            label.contains("мтс") ||
            label.contains("mgts") ||
            label.contains("мгтс")
    }

    fun carrierLabel(context: Context): String {
        val tm = context.getSystemService(Context.TELEPHONY_SERVICE) as? TelephonyManager
            ?: return "?"
        return tm.networkOperatorName?.takeIf { it.isNotBlank() }
            ?: tm.simOperatorName?.takeIf { it.isNotBlank() }
            ?: tm.networkOperator?.takeIf { it.isNotBlank() }
            ?: "?"
    }
}

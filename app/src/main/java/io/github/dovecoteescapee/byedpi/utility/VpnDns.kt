package io.github.dovecoteescapee.byedpi.utility

import android.content.Context
import android.net.ConnectivityManager
import android.net.LinkProperties

object VpnDns {
    /** User DNS first, then ISP/system DNS — avoids relying only on blocked 8.8.8.8. */
    fun resolveServers(context: Context, userDns: String?): List<String> {
        val servers = mutableListOf<String>()
        val user = userDns?.trim().orEmpty()
        if (user.isNotEmpty()) {
            servers.add(user)
        }
        for (dns in readSystemDns(context)) {
            if (dns !in servers) {
                servers.add(dns)
            }
        }
        if (servers.isEmpty()) {
            servers.add("8.8.8.8")
        }
        return servers
    }

    private fun readSystemDns(context: Context): List<String> {
        return try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
                ?: return emptyList()
            val network = cm.activeNetwork ?: return emptyList()
            val props: LinkProperties = cm.getLinkProperties(network) ?: return emptyList()
            props.dnsServers.mapNotNull { it.hostAddress?.trim() }.filter { it.isNotEmpty() }
        } catch (e: SecurityException) {
            emptyList()
        }
    }
}

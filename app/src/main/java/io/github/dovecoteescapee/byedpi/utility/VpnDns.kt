package io.github.dovecoteescapee.byedpi.utility

import android.content.Context
import android.net.ConnectivityManager
import android.net.LinkProperties

object VpnDns {
    /** System DNS first, then user override — Google DNS alone often breaks YT in RU. */
    fun resolveServers(context: Context, userDns: String?): List<String> {
        val servers = mutableListOf<String>()
        for (dns in readSystemDns(context)) {
            if (dns !in servers) {
                servers.add(dns)
            }
        }
        val user = userDns?.trim().orEmpty()
        if (user.isNotEmpty() && user !in servers) {
            servers.add(user)
        }
        if (servers.isEmpty()) {
            servers.add("77.88.8.8")
            servers.add("1.1.1.1")
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

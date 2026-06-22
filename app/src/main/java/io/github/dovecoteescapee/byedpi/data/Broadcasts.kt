package io.github.dovecoteescapee.byedpi.data

const val STARTED_BROADCAST = "io.github.dovecoteescapee.byedpi.STARTED"
const val STOPPED_BROADCAST = "io.github.dovecoteescapee.byedpi.STOPPED"
const val FAILED_BROADCAST = "io.github.dovecoteescapee.byedpi.FAILED"
const val TG_WS_READY_BROADCAST = "io.github.dovecoteescapee.byedpi.TG_WS_READY"

const val SENDER = "sender"
const val ERROR_DETAIL = "error_detail"
const val TG_WS_PROXY_URL = "tg_ws_proxy_url"

enum class Sender(val senderName: String) {
    Proxy("Proxy"),
    VPN("VPN")
}

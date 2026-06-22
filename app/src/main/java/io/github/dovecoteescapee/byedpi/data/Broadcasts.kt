package io.github.dovecoteescapee.byedpi.data

const val STARTED_BROADCAST = "io.github.dovecoteescapee.byedpi.STARTED"
const val STOPPED_BROADCAST = "io.github.dovecoteescapee.byedpi.STOPPED"
const val FAILED_BROADCAST = "io.github.dovecoteescapee.byedpi.FAILED"
const val TG_WS_READY_BROADCAST = "io.github.dovecoteescapee.byedpi.TG_WS_READY"
const val PROBE_PROGRESS_BROADCAST = "io.github.dovecoteescapee.byedpi.PROBE_PROGRESS"

const val SENDER = "sender"
const val ERROR_DETAIL = "error_detail"
const val TG_WS_PROXY_URL = "tg_ws_proxy_url"

const val PROBE_INDEX = "probe_index"
const val PROBE_TOTAL = "probe_total"
const val PROBE_PRESET_LABEL = "probe_preset_label"
const val PROBE_PHASE = "probe_phase"

/** [PROBE_PHASE] values for preset auto-selection UI. */
object ProbePhase {
    const val STARTED = "started"
    const val TRYING = "trying"
    const val FAILED = "failed"
    const val SUCCESS = "success"
    const val FINISHED = "finished"
    const val SKIPPED = "skipped"
}

enum class Sender(val senderName: String) {
    Proxy("Proxy"),
    VPN("VPN")
}

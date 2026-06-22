package io.github.dovecoteescapee.byedpi.services

import android.app.Notification
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.ParcelFileDescriptor
import android.util.Log
import androidx.lifecycle.lifecycleScope
import io.github.dovecoteescapee.byedpi.R
import io.github.dovecoteescapee.byedpi.activities.MainActivity
import io.github.dovecoteescapee.byedpi.core.ByeDpiProxy
import io.github.dovecoteescapee.byedpi.core.ByeDpiProxyCmdPreferences
import io.github.dovecoteescapee.byedpi.core.ByeDpiProxyPreferences
import io.github.dovecoteescapee.byedpi.core.ByeDpiProxyUIPreferences
import io.github.dovecoteescapee.byedpi.core.TProxyService
import io.github.dovecoteescapee.byedpi.core.TgWsProxy
import io.github.dovecoteescapee.byedpi.data.*
import io.github.dovecoteescapee.byedpi.utility.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.io.File

class ByeDpiVpnService : LifecycleVpnService() {
    private val byeDpiProxy = ByeDpiProxy()
    private var proxyJob: Job? = null
    private var tunFd: ParcelFileDescriptor? = null
    private var tunConfigFile: File? = null
    private var useTgWsForTelegram: Boolean = false
    private val mutex = Mutex()
    private var stopping: Boolean = false

    companion object {
        private val TAG: String = ByeDpiVpnService::class.java.simpleName
        private const val FOREGROUND_SERVICE_ID: Int = 1
        private const val NOTIFICATION_CHANNEL_ID: String = "ByeDPIVpn"

        private var status: ServiceStatus = ServiceStatus.Disconnected
        var lastError: String? = null
            private set
        var tgWsProxyUrl: String? = null
            private set
        var sessionSocksPort: Int = 1080
            private set
    }

    override fun onCreate() {
        super.onCreate()
        registerNotificationChannel(
            this,
            NOTIFICATION_CHANNEL_ID,
            R.string.vpn_channel_name,
        )
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)
        return when (val action = intent?.action) {
            START_ACTION -> {
                lifecycleScope.launch { start() }
                START_STICKY
            }

            STOP_ACTION -> {
                lifecycleScope.launch { stop() }
                START_NOT_STICKY
            }

            else -> {
                Log.w(TAG, "Unknown action: $action")
                START_NOT_STICKY
            }
        }
    }

    override fun onRevoke() {
        Log.i(TAG, "VPN revoked")
        lifecycleScope.launch { stop() }
    }

    private suspend fun start() {
        Log.i(TAG, "Starting")

        if (status == ServiceStatus.Connected) {
            Log.w(TAG, "VPN already connected")
            return
        }

        startForeground()

        // Fixed loopback port: tun2socks and ByeDPI must share a stable port (ephemeral broke YT).
        val prefs = getPreferences()
        sessionSocksPort = prefs.getString("byedpi_proxy_port", null)?.toIntOrNull() ?: 1080

        try {
            mutex.withLock {
                startProxy()
                startTun2Socks()
            }
            updateStatus(ServiceStatus.Connected)
            lifecycleScope.launch(Dispatchers.IO) {
                mutex.withLock {
                    if (!stopping) {
                        startTgWsProxyAsync()
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start VPN", e)
            lastError = e.message ?: e.javaClass.simpleName
            cleanupAfterFailure()
            updateStatus(ServiceStatus.Failed)
            stopSelf()
        }
    }

    private fun startForeground() {
        val notification: Notification = createNotification()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(
                FOREGROUND_SERVICE_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE,
            )
        } else {
            startForeground(FOREGROUND_SERVICE_ID, notification)
        }
    }

    private suspend fun cleanupAfterFailure() {
        mutex.withLock {
            stopping = true
            try {
                if (tunFd != null) {
                    stopTun2Socks()
                }
            } catch (e: Exception) {
                Log.w(TAG, "Cleanup tun2socks failed", e)
            }
            try {
                TgWsProxy.stop()
            } catch (e: Exception) {
                Log.w(TAG, "Cleanup tg-ws failed", e)
            }
            try {
                if (proxyJob != null) {
                    byeDpiProxy.stopProxy()
                    proxyJob?.join()
                } else {
                    byeDpiProxy.reset()
                }
            } catch (e: Exception) {
                Log.w(TAG, "Cleanup proxy failed", e)
            } finally {
                proxyJob = null
                stopping = false
            }
        }
    }

    private suspend fun stop() {
        Log.i(TAG, "Stopping")

        mutex.withLock {
            stopping = true
            try {
                stopTun2Socks()
                TgWsProxy.stop()
                stopProxy()
            } catch (e: Exception) {
                Log.e(TAG, "Failed to stop VPN", e)
            } finally {
                stopping = false
            }
        }

        updateStatus(ServiceStatus.Disconnected)
        stopSelf()
    }

    private suspend fun startProxy() {
        Log.i(TAG, "Starting proxy")

        if (proxyJob != null) {
            throw IllegalStateException("Proxy fields not null")
        }

        val listenFd = openProxySocket()
        if (listenFd < 0) {
            throw IllegalStateException("ByeDPI failed to start")
        }

        proxyJob = lifecycleScope.launch(Dispatchers.IO) {
            val code = byeDpiProxy.runLoop()

            withContext(Dispatchers.Main) {
                if (code != 0) {
                    Log.e(TAG, "Proxy stopped with code $code")
                    updateStatus(ServiceStatus.Failed)
                } else if (!stopping) {
                    stop()
                    updateStatus(ServiceStatus.Disconnected)
                }
            }
        }

        Log.i(TAG, "Proxy listening on fd $listenFd")
    }

    private suspend fun openProxySocket(): Int {
        val shared = getPreferences()
        val tgWs = shared.getBoolean("tg_ws_telegram", true)
        val port = sessionSocksPort
        val cellular = NetworkHelper.isCellular(this)
        val isMts = NetworkHelper.isMts(this)
        if (cellular) {
            Log.i(TAG, "Cellular operator: ${NetworkHelper.carrierLabel(this)} (mts=$isMts)")
        }
        val ytPreset = LocalSocksPort.patchCmdPort(DpiDefaults.youtubePreset(this), port)
        val ytMobilePreset = LocalSocksPort.patchCmdPort(DpiDefaults.youtubeMobilePreset(this), port)
        val mtsPreset = LocalSocksPort.patchCmdPort(DpiDefaults.mtsYoutubePreset(this), port)
        val mtsAltPreset = LocalSocksPort.patchCmdPort(DpiDefaults.PRESET_MTS_ALT, port)
        val litePreset = LocalSocksPort.patchCmdPort(DpiDefaults.litePreset(this), port)

        val attempts = buildList {
            if (isMts && cellular) {
                add(ByeDpiProxyCmdPreferences(mtsPreset))
                add(ByeDpiProxyCmdPreferences(mtsAltPreset))
            }
            if (shared.getBoolean("byedpi_enable_cmd_settings", false)) {
                val cmd = shared.getString("byedpi_cmd_args", null)?.trim().orEmpty()
                if (cmd.isNotEmpty()) {
                    add(ByeDpiProxyCmdPreferences(LocalSocksPort.patchCmdPort(cmd, port)))
                }
            }
            if (cellular && !isMts) {
                add(ByeDpiProxyCmdPreferences(ytMobilePreset))
            }
            if (tgWs) {
                add(ByeDpiProxyCmdPreferences(ytPreset))
                add(
                    ByeDpiProxyCmdPreferences(
                        LocalSocksPort.patchCmdPort(DpiDefaults.PRESET_MEDIA_TCP, port),
                    ),
                )
            } else {
                add(ByeDpiProxyPreferences.fromSharedPreferences(shared, port))
            }
            add(ByeDpiProxyCmdPreferences(litePreset))
            add(ByeDpiProxyCmdPreferences(LocalSocksPort.patchCmdPort(DpiDefaults.PRESET_HYBRID, port)))
            add(ByeDpiProxyCmdPreferences(LocalSocksPort.patchCmdPort(DpiDefaults.PRESET_MINIMAL, port)))
            add(DpiDefaults.uiPreferences(port))
        }

        for (preferences in attempts) {
            byeDpiProxy.reset()
            when (preferences) {
                is ByeDpiProxyCmdPreferences ->
                    Log.i(TAG, "Trying cmd: ${preferences.args.joinToString(" ")}")
                is ByeDpiProxyUIPreferences ->
                    Log.i(TAG, "Trying UI preferences")
            }
            val fd = byeDpiProxy.openSocket(preferences)
            if (fd >= 0) return fd
        }
        return -1
    }

    private suspend fun stopProxy() {
        Log.i(TAG, "Stopping proxy")

        if (proxyJob == null) {
            byeDpiProxy.reset()
            return
        }

        byeDpiProxy.stopProxy()
        proxyJob?.join()
        proxyJob = null

        Log.i(TAG, "Proxy stopped")
    }

    private fun startTgWsProxyAsync() {
        if (stopping) {
            Log.i(TAG, "TG WS proxy skipped — service stopping")
            return
        }

        val prefs = getPreferences()
        useTgWsForTelegram = prefs.getBoolean("tg_ws_telegram", true)
        tgWsProxyUrl = null

        if (!useTgWsForTelegram) {
            Log.i(TAG, "TG WS proxy disabled")
            return
        }

        if (!TgWsProxy.isNativeAvailable()) {
            Log.e(TAG, "libtgwsproxy.so missing — Telegram WS proxy skipped")
            useTgWsForTelegram = false
            return
        }

        try {
            val url = TgWsProxy.start(this@ByeDpiVpnService)
            if (stopping) {
                Log.i(TAG, "TG WS proxy stopped immediately after start")
                TgWsProxy.stop()
                return
            }
            if (!TelegramProxyHelper.isLocalWsProxyUrl(url)) {
                Log.e(TAG, "TG WS proxy returned unexpected URL")
                TgWsProxy.stop()
                return
            }
            tgWsProxyUrl = url
            prefs.edit().putString("tg_ws_last_proxy_url", url).apply()
            Log.i(TAG, "TG WS proxy started on ${TgWsProxy.BIND_IP}:${TgWsProxy.DEFAULT_PORT}")

            if (prefs.getBoolean("tg_ws_auto_apply", true)) {
                sendBroadcast(
                    Intent(TG_WS_READY_BROADCAST).apply {
                        setPackage(packageName)
                        putExtra(TG_WS_PROXY_URL, url)
                    },
                )
            }
        } catch (t: Throwable) {
            Log.e(TAG, "TG WS proxy failed, YouTube/Instagram still via VPN", t)
            useTgWsForTelegram = false
            TgWsProxy.stop()
        }
    }

    private fun startTun2Socks() {
        Log.i(TAG, "Starting tun2socks")

        if (tunFd != null) {
            throw IllegalStateException("VPN field not null")
        }

        val sharedPreferences = getPreferences()
        val port = sessionSocksPort
        val userDns = sharedPreferences.getString("dns_ip", null)
        val ipv6 = sharedPreferences.getBoolean("ipv6_enable", false)

        val tun2socksConfig = """
        | misc:
        |   task-stack-size: 81920
        | socks5:
        |   mtu: 8500
        |   address: 127.0.0.1
        |   port: $port
        |   udp: udp
        """.trimMargin("| ")

        val configPath = try {
            File.createTempFile("config", "tmp", cacheDir).also { file ->
                file.writeText(tun2socksConfig)
                tunConfigFile = file
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create config file", e)
            throw e
        }

        val fd = createBuilder(userDns, ipv6).establish()
            ?: throw IllegalStateException("VPN connection failed")

        this.tunFd = fd

        TProxyService.TProxyStartService(configPath.absolutePath, fd.fd)

        Log.i(TAG, "Tun2Socks started")
    }

    private fun stopTun2Socks() {
        Log.i(TAG, "Stopping tun2socks")

        TProxyService.TProxyStopService()

        try {
            tunConfigFile?.delete()
            tunConfigFile = null
        } catch (e: SecurityException) {
            Log.e(TAG, "Failed to delete config file", e)
        }

        tunFd?.close() ?: Log.w(TAG, "VPN not running")
        tunFd = null

        Log.i(TAG, "Tun2socks stopped")
    }

    private fun updateStatus(newStatus: ServiceStatus) {
        Log.d(TAG, "VPN status changed from $status to $newStatus")

        status = newStatus

        setStatus(
            when (newStatus) {
                ServiceStatus.Connected -> AppStatus.Running

                ServiceStatus.Disconnected,
                ServiceStatus.Failed -> {
                    proxyJob = null
                    AppStatus.Halted
                }
            },
            Mode.VPN
        )

        val intent = Intent(
            when (newStatus) {
                ServiceStatus.Connected -> STARTED_BROADCAST
                ServiceStatus.Disconnected -> STOPPED_BROADCAST
                ServiceStatus.Failed -> FAILED_BROADCAST
            }
        )
        intent.putExtra(SENDER, Sender.VPN.ordinal)
        lastError?.let { intent.putExtra(ERROR_DETAIL, it) }
        intent.setPackage(packageName)
        sendBroadcast(intent)
    }

    private fun createNotification(): Notification =
        createConnectionNotification(
            this,
            NOTIFICATION_CHANNEL_ID,
            R.string.notification_title,
            R.string.vpn_notification_content,
            ByeDpiVpnService::class.java,
        )

    private fun createBuilder(userDns: String?, ipv6: Boolean): Builder {
        val dnsServers = VpnDns.resolveServers(this, userDns)
        Log.d(TAG, "DNS servers: ${dnsServers.joinToString()}")
        val builder = Builder()
        builder.setSession("DpiBypass")
        builder.setConfigureIntent(
            PendingIntent.getActivity(
                this,
                0,
                Intent(this, MainActivity::class.java),
                PendingIntent.FLAG_IMMUTABLE,
            )
        )

        builder.addAddress("10.10.10.10", 32)
            .addRoute("0.0.0.0", 0)

        if (ipv6) {
            builder.addAddress("fd00::1", 128)
                .addRoute("::", 0)
        }

        for (server in dnsServers) {
            builder.addDnsServer(server)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            builder.setMetered(false)
        }

        val prefs = getPreferences()
        val onlyTargets = prefs.getBoolean("only_target_apps", true)
        val tgWs = prefs.getBoolean("tg_ws_telegram", true)
        val installed = if (onlyTargets) {
            AppTargets.vpnCapturePackages(this, excludeTelegram = tgWs)
        } else {
            emptyList()
        }

        if (onlyTargets && installed.isNotEmpty()) {
            installed.forEach { pkg ->
                try {
                    builder.addAllowedApplication(pkg)
                    Log.i(TAG, "Per-app capture: $pkg")
                } catch (e: PackageManager.NameNotFoundException) {
                    Log.w(TAG, "Package not found: $pkg")
                }
            }
        } else if (onlyTargets && tgWs) {
            Log.w(TAG, "No YouTube/Instagram in package list — capturing all apps except DpiBypass")
            builder.addDisallowedApplication(applicationContext.packageName)
        } else if (!onlyTargets) {
            builder.addDisallowedApplication(applicationContext.packageName)
        } else {
            Log.w(TAG, "No target apps — falling back to full tunnel except DpiBypass")
            builder.addDisallowedApplication(applicationContext.packageName)
        }

        return builder
    }
}

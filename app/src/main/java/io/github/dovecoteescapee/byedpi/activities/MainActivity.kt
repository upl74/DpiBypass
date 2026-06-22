package io.github.dovecoteescapee.byedpi.activities

import android.Manifest
import android.annotation.SuppressLint
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.res.ColorStateList
import android.content.pm.PackageManager
import android.net.VpnService
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import androidx.lifecycle.lifecycleScope
import io.github.dovecoteescapee.byedpi.R
import io.github.dovecoteescapee.byedpi.data.*
import io.github.dovecoteescapee.byedpi.fragments.MainSettingsFragment
import io.github.dovecoteescapee.byedpi.databinding.ActivityMainBinding
import io.github.dovecoteescapee.byedpi.services.ByeDpiProxyService
import io.github.dovecoteescapee.byedpi.services.ByeDpiVpnService
import io.github.dovecoteescapee.byedpi.services.ServiceManager
import io.github.dovecoteescapee.byedpi.services.appStatus
import io.github.dovecoteescapee.byedpi.services.setStatus
import io.github.dovecoteescapee.byedpi.utility.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.IOException

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private val probeLogLines = ArrayDeque<String>(6)

    companion object {
        private val TAG: String = MainActivity::class.java.simpleName

        private val SENSITIVE_LOG_PATTERNS = listOf(
            Regex("""secret[=:]\S+""", RegexOption.IGNORE_CASE),
            Regex("""t\.me/proxy\?[^\s"]+""", RegexOption.IGNORE_CASE),
            Regex("""TG WS proxy:\s*\S+""", RegexOption.IGNORE_CASE),
            Regex("""tg_ws_last_proxy_url""", RegexOption.IGNORE_CASE),
        )

        private fun redactSensitiveLogs(raw: String): String =
            raw.lineSequence()
                .map { line ->
                    var redacted = line
                    for (pattern in SENSITIVE_LOG_PATTERNS) {
                        redacted = redacted.replace(pattern, "[REDACTED]")
                    }
                    redacted
                }
                .joinToString("\n")

        private fun collectLogs(): String? =
            try {
                Runtime.getRuntime()
                    .exec("logcat *:D -d")
                    .inputStream.bufferedReader()
                    .use { redactSensitiveLogs(it.readText()) }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to collect logs", e)
                null
            }
    }

    private val vpnRegister =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            if (it.resultCode == RESULT_OK) {
                ServiceManager.start(this, Mode.VPN)
            } else {
                setStatus(AppStatus.Halted, Mode.VPN)
                Toast.makeText(this, R.string.vpn_permission_denied, Toast.LENGTH_SHORT).show()
                updateStatus()
            }
        }

    private val logsRegister =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            lifecycleScope.launch(Dispatchers.IO) {
                val logs = collectLogs()

                if (logs == null) {
                    Toast.makeText(
                        this@MainActivity,
                        R.string.logs_failed,
                        Toast.LENGTH_SHORT
                    ).show()
                } else {
                    val uri = it.data?.data ?: run {
                        Log.e(TAG, "No data in result")
                        return@launch
                    }
                    contentResolver.openOutputStream(uri)?.use {
                        try {
                            it.write(logs.toByteArray())
                        } catch (e: IOException) {
                            Log.e(TAG, "Failed to save logs", e)
                        }
                    } ?: run {
                        Log.e(TAG, "Failed to open output stream")
                    }
                }
            }
        }

    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            Log.d(TAG, "Received intent: ${intent?.action}")

            if (intent == null) {
                Log.w(TAG, "Received null intent")
                return
            }

            val senderOrd = intent.getIntExtra(SENDER, -1)
            val sender = Sender.entries.getOrNull(senderOrd)
            if (sender == null) {
                Log.w(TAG, "Received intent with unknown sender: $senderOrd")
                return
            }

            when (val action = intent.action) {
                PROBE_PROGRESS_BROADCAST -> handleProbeProgress(intent)

                STARTED_BROADCAST,
                STOPPED_BROADCAST -> {
                    if (action == STOPPED_BROADCAST) {
                        hideProbePanel()
                    }
                    updateStatus()
                }

                FAILED_BROADCAST -> {
                    hideProbePanel()
                    val detail = intent.getStringExtra(ERROR_DETAIL)
                    Toast.makeText(
                        context,
                        detail ?: getString(R.string.failed_to_start, sender.name),
                        Toast.LENGTH_LONG,
                    ).show()
                    updateStatus()
                }

                TG_WS_READY_BROADCAST -> {
                    if (getPreferences().getBoolean("tg_ws_auto_apply", true)) {
                        val url = intent.getStringExtra(TG_WS_PROXY_URL)
                        if (TelegramProxyHelper.isLocalWsProxyUrl(url)) {
                            TelegramProxyHelper.applyLocalWsProxy(this@MainActivity, url!!)
                        } else {
                            Log.w(TAG, "Ignored non-local TG WS proxy URL")
                        }
                    }
                    updateStatus()
                }

                else -> Log.w(TAG, "Unknown action: $action")
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        DpiDefaults.applyIfNeeded(this)

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        WindowCompat.setDecorFitsSystemWindows(window, true)
        setSupportActionBar(binding.toolbar)

        val intentFilter = IntentFilter().apply {
            addAction(PROBE_PROGRESS_BROADCAST)
            addAction(STARTED_BROADCAST)
            addAction(STOPPED_BROADCAST)
            addAction(FAILED_BROADCAST)
            addAction(TG_WS_READY_BROADCAST)
        }

        @SuppressLint("UnspecifiedRegisterReceiverFlag")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(receiver, intentFilter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(receiver, intentFilter)
        }

        binding.statusButton.setOnClickListener {
            val (status, _) = appStatus
            when (status) {
                AppStatus.Halted -> start()
                AppStatus.Connecting -> stop()
                AppStatus.Running -> stop()
            }
        }

        binding.telegramMtprotoButton.setOnClickListener {
            val url = ByeDpiVpnService.tgWsProxyUrl
                ?: getPreferences().getString("tg_ws_last_proxy_url", null)
            if (!TelegramProxyHelper.isLocalWsProxyUrl(url)) {
                Toast.makeText(this, R.string.telegram_ws_not_running, Toast.LENGTH_SHORT).show()
            } else {
                TelegramProxyHelper.applyLocalWsProxy(this, url!!)
            }
        }

        val theme = getPreferences()
            .getString("app_theme", null)
        MainSettingsFragment.setTheme(theme ?: "system")

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.POST_NOTIFICATIONS
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }
    }

    override fun onResume() {
        super.onResume()
        updateStatus()
    }

    override fun onDestroy() {
        super.onDestroy()
        unregisterReceiver(receiver)
    }

    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean =
        when (item.itemId) {
            R.id.action_settings -> {
                startActivity(Intent(this, SettingsActivity::class.java))
                true
            }

            R.id.action_save_logs -> {
                val intent =
                    Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                        addCategory(Intent.CATEGORY_OPENABLE)
                        type = "text/plain"
                        putExtra(Intent.EXTRA_TITLE, "byedpi.log")
                    }

                logsRegister.launch(intent)
                true
            }

            else -> super.onOptionsItemSelected(item)
        }

    private fun start() {
        val preferences = getPreferences()
        if (preferences.getBoolean("only_target_apps", true)) {
            val targets = AppTargets.installedOnDevice(this)
            if (targets.isEmpty()) {
                Toast.makeText(this, R.string.no_target_apps_warn, Toast.LENGTH_LONG).show()
            }
        }

        when (preferences.mode()) {
            Mode.VPN -> {
                setStatus(AppStatus.Connecting, Mode.VPN)
                updateStatus()
                val intentPrepare = VpnService.prepare(this)
                if (intentPrepare != null) {
                    vpnRegister.launch(intentPrepare)
                } else {
                    ServiceManager.start(this, Mode.VPN)
                }
            }

            Mode.Proxy -> {
                setStatus(AppStatus.Connecting, Mode.Proxy)
                updateStatus()
                ServiceManager.start(this, Mode.Proxy)
            }
        }
    }

    private fun stop() {
        ServiceManager.stop(this)
    }

    private fun updateStatus() {
        val (status, mode) = appStatus

        Log.i(TAG, "Updating status: $status, $mode")

        val preferences = getPreferences()
        val proxyIp = preferences.getStringNotNull("byedpi_proxy_ip", "127.0.0.1")
        val proxyPort = when (status) {
            AppStatus.Running, AppStatus.Connecting -> when (mode) {
                Mode.VPN -> ByeDpiVpnService.sessionSocksPort.toString()
                Mode.Proxy -> ByeDpiProxyService.sessionSocksPort.toString()
            }
            AppStatus.Halted -> preferences.getStringNotNull("byedpi_proxy_port", "1080")
        }
        binding.proxyAddress.text = getString(R.string.proxy_address, proxyIp, proxyPort)

        val isRunning = status == AppStatus.Running
        val isConnecting = status == AppStatus.Connecting
        binding.statusIndicator.setBackgroundResource(
            when {
                isRunning -> R.drawable.bg_status_dot_connected
                isConnecting -> R.drawable.bg_status_dot_connecting
                else -> R.drawable.bg_status_dot_disconnected
            },
        )

        when (status) {
            AppStatus.Halted -> {
                hideProbePanel()
                binding.statusButton.backgroundTintList =
                    ColorStateList.valueOf(ContextCompat.getColor(this, R.color.primary))
                when (preferences.mode()) {
                    Mode.VPN -> {
                        binding.statusText.setText(R.string.vpn_disconnected)
                        binding.statusButton.setText(R.string.vpn_connect)
                    }

                    Mode.Proxy -> {
                        binding.statusText.setText(R.string.proxy_down)
                        binding.statusButton.setText(R.string.proxy_start)
                    }
                }
                binding.statusButton.isEnabled = true
            }

            AppStatus.Connecting -> {
                binding.statusButton.backgroundTintList =
                    ColorStateList.valueOf(ContextCompat.getColor(this, R.color.status_connecting))
                when (mode) {
                    Mode.VPN -> {
                        binding.statusText.setText(R.string.vpn_connecting)
                        binding.statusButton.setText(R.string.vpn_disconnect)
                    }

                    Mode.Proxy -> {
                        binding.statusText.setText(R.string.vpn_connecting)
                        binding.statusButton.setText(R.string.proxy_stop)
                    }
                }
                binding.statusButton.isEnabled = true
            }

            AppStatus.Running -> {
                binding.statusButton.backgroundTintList =
                    ColorStateList.valueOf(ContextCompat.getColor(this, R.color.disconnect))
                when (mode) {
                    Mode.VPN -> {
                        binding.statusText.setText(R.string.vpn_connected)
                        binding.statusButton.setText(R.string.vpn_disconnect)
                    }

                    Mode.Proxy -> {
                        binding.statusText.setText(R.string.proxy_up)
                        binding.statusButton.setText(R.string.proxy_stop)
                    }
                }
                binding.statusButton.isEnabled = true
            }
        }
    }

    private fun handleProbeProgress(intent: Intent) {
        val phase = intent.getStringExtra(PROBE_PHASE) ?: return
        val index = intent.getIntExtra(PROBE_INDEX, 0)
        val total = intent.getIntExtra(PROBE_TOTAL, 0)
        val label = intent.getStringExtra(PROBE_PRESET_LABEL).orEmpty()

        when (phase) {
            ProbePhase.STARTED -> {
                probeLogLines.clear()
                showProbePanel()
                binding.probeStatusLine.setText(R.string.probe_started)
                binding.probePresetName.text = ""
                binding.probeLog.text = ""
                binding.probeProgress.isIndeterminate = true
                binding.probeCounter.text = ""
            }

            ProbePhase.SKIPPED -> {
                binding.probePanel.visibility = View.VISIBLE
                binding.probeStatusLine.setText(R.string.probe_skipped)
                binding.probePresetName.text = ""
                binding.probeProgress.isIndeterminate = true
                binding.probeCounter.text = ""
            }

            ProbePhase.TRYING -> {
                showProbePanel()
                binding.probeProgress.isIndeterminate = false
                binding.probeProgress.max = total.coerceAtLeast(1)
                binding.probeProgress.setProgressCompat(index.coerceAtMost(total), true)
                binding.probeCounter.text = getString(R.string.probe_counter, index, total)
                binding.probePresetName.text = label
                binding.probeStatusLine.setText(R.string.probe_trying)
            }

            ProbePhase.FAILED -> {
                probeLogLines.addLast(getString(R.string.probe_failed_line, label))
                trimProbeLog()
                binding.probeLog.text = probeLogLines.joinToString("\n")
                binding.probeStatusLine.setTextColor(
                    ContextCompat.getColor(this, R.color.probe_failed),
                )
                binding.probeStatusLine.text = getString(R.string.probe_failed_line, label)
            }

            ProbePhase.SUCCESS -> {
                probeLogLines.addLast(getString(R.string.probe_success_line, label))
                trimProbeLog()
                binding.probeLog.text = probeLogLines.joinToString("\n")
                binding.probeStatusLine.setTextColor(
                    ContextCompat.getColor(this, R.color.status_connected),
                )
                binding.probeStatusLine.text = getString(R.string.probe_success_line, label)
            }

            ProbePhase.FINISHED -> {
                binding.probeProgress.isIndeterminate = false
                binding.probeProgress.max = total.coerceAtLeast(1)
                binding.probeProgress.setProgressCompat(total.coerceAtLeast(1), true)
                if (label.isNotEmpty()) {
                    binding.probePresetName.text = label
                    binding.probeStatusLine.setTextColor(
                        ContextCompat.getColor(this, R.color.status_connected),
                    )
                    binding.probeStatusLine.text = getString(R.string.probe_success_final, label)
                }
            }
        }
    }

    private fun trimProbeLog() {
        while (probeLogLines.size > 5) {
            probeLogLines.removeFirst()
        }
    }

    private fun showProbePanel() {
        binding.probePanel.visibility = View.VISIBLE
        binding.probeStatusLine.setTextColor(
            ContextCompat.getColor(this, R.color.on_surface_variant),
        )
    }

    private fun hideProbePanel() {
        binding.probePanel.visibility = View.GONE
        probeLogLines.clear()
    }
}
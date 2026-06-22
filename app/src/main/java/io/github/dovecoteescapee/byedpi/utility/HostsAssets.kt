package io.github.dovecoteescapee.byedpi.utility

import android.content.Context
import java.io.File

object HostsAssets {
    private const val GOOGLE_HOSTS_ASSET = "list-google.txt"
    private const val HOSTS_DIR = "hosts"

    /** Optional manual -H file; не подставлять автоматически — whitelist рвёт прочий Google-трафик. */
    fun googleHostsFile(context: Context): String {
        val dir = File(context.filesDir, HOSTS_DIR)
        val out = File(dir, GOOGLE_HOSTS_ASSET)
        if (!out.isFile) {
            dir.mkdirs()
            context.assets.open(GOOGLE_HOSTS_ASSET).use { input ->
                out.outputStream().use { output -> input.copyTo(output) }
            }
        }
        return out.absolutePath
    }

    /** Inline `-H:"…"` from asset — только с полным list-google.txt (все домены YT). */
    fun googleHostsSwitch(context: Context): String {
        val hosts = context.assets.open(GOOGLE_HOSTS_ASSET).bufferedReader().use { reader ->
            reader.lineSequence()
                .map { it.trim() }
                .filter { it.isNotEmpty() && !it.startsWith("#") }
                .joinToString(" ")
        }
        return "-H:\"$hosts\""
    }
}

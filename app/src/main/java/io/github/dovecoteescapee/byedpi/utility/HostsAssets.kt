package io.github.dovecoteescapee.byedpi.utility

import android.content.Context
import java.io.File

object HostsAssets {
    private const val GOOGLE_HOSTS_ASSET = "list-google.txt"
    private const val HOSTS_DIR = "hosts"

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

    /** Add Google/YouTube host whitelist if the preset has no -H yet. */
    fun withGoogleHosts(cmd: String, context: Context): String {
        if (cmd.contains("-H")) return cmd
        val path = googleHostsFile(context)
        val bind = Regex("""(-i\s+127\.0\.0\.1\s+-p\s+\d+)""")
        return if (bind.containsMatchIn(cmd)) {
            cmd.replaceFirst(bind, "$1 -H$path")
        } else {
            "-H$path $cmd"
        }
    }
}

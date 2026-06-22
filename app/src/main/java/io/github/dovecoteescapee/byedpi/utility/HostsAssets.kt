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

    /** @deprecated Авто-inject -H ломает YouTube (gstatic и др. вне списка). */
    @Deprecated("Do not auto-inject; breaks non-listed Google hosts")
    fun withGoogleHosts(cmd: String, context: Context): String = cmd
}

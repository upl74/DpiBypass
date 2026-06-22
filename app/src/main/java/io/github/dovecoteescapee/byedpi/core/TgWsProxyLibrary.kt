package io.github.dovecoteescapee.byedpi.core

import com.sun.jna.Library
import com.sun.jna.Native
import com.sun.jna.Pointer

internal interface TgWsProxyLibrary : Library {
    fun StartProxy(host: String, port: Int, dcIps: String, secret: String, verbose: Int): Int
    fun StopProxy(): Int
    fun SetPoolSize(size: Int)
    fun SetCfProxyCacheDir(cacheDir: String)
    fun SetCfProxyConfig(enabled: Int, priority: Int, userDomain: String)
    fun GetSecretWithPrefix(): Pointer?
    fun GetStats(): Pointer?
    fun FreeString(p: Pointer)

    companion object {
        @Volatile
        private var instance: TgWsProxyLibrary? = null

        fun load(): TgWsProxyLibrary {
            instance?.let { return it }
            synchronized(this) {
                instance?.let { return it }
                instance = Native.load("tgwsproxy", TgWsProxyLibrary::class.java)
                return instance!!
            }
        }

        val INSTANCE: TgWsProxyLibrary
            get() = load()
    }
}

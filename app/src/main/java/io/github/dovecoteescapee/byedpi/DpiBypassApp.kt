package io.github.dovecoteescapee.byedpi

import android.app.Application

class DpiBypassApp : Application() {
    override fun onCreate() {
        super.onCreate()
        System.setProperty("jna.nosys", "true")
        System.setProperty("jna.noclasspath", "true")
    }
}

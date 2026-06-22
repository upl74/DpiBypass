package io.github.dovecoteescapee.byedpi.fragments

import android.os.Bundle
import androidx.preference.EditTextPreference
import androidx.preference.ListPreference
import androidx.preference.PreferenceFragmentCompat
import io.github.dovecoteescapee.byedpi.R
import io.github.dovecoteescapee.byedpi.utility.DpiDefaults
import io.github.dovecoteescapee.byedpi.utility.findPreferenceNotNull

class ByeDpiCommandLineSettingsFragment : PreferenceFragmentCompat() {
    override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
        setPreferencesFromResource(R.xml.byedpi_cmd_settings, rootKey)

        val preset = findPreferenceNotNull<ListPreference>("byedpi_cmd_preset")
        val cmdArgs = findPreferenceNotNull<EditTextPreference>("byedpi_cmd_args")

        preset.setOnPreferenceChangeListener { _, newValue ->
            DpiDefaults.presetArgs(newValue as String)?.let { cmdArgs.text = it }
            true
        }
    }
}

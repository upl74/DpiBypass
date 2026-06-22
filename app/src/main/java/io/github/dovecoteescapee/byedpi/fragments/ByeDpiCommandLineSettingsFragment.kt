package io.github.dovecoteescapee.byedpi.fragments

import android.os.Bundle
import androidx.preference.DropDownPreference
import androidx.preference.PreferenceFragmentCompat
import com.takisoft.preferencex.EditTextPreference
import io.github.dovecoteescapee.byedpi.R
import io.github.dovecoteescapee.byedpi.utility.DpiDefaults
import io.github.dovecoteescapee.byedpi.utility.findPreferenceNotNull

class ByeDpiCommandLineSettingsFragment : PreferenceFragmentCompat() {
    override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
        setPreferencesFromResource(R.xml.byedpi_cmd_settings, rootKey)

        val preset = findPreferenceNotNull<DropDownPreference>("byedpi_cmd_preset")
        val cmdArgs = findPreferenceNotNull<EditTextPreference>("byedpi_cmd_args")

        if (cmdArgs.text.isNullOrBlank()) {
            cmdArgs.text = DpiDefaults.youtubePreset(requireContext())
        }

        preset.setOnPreferenceChangeListener { _, newValue ->
            val key = newValue as String
            if (key != "custom") {
                DpiDefaults.presetArgs(requireContext(), key)?.let { cmdArgs.text = it }
            }
            true
        }
    }
}

\
# options_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from aqt import mw
import os

# Assuming config.py and this file are in the same directory (addon root)
# and config.py defines addon_path
try:
    from .config import addon_path
    ADDON_NAME = os.path.basename(addon_path)
except ImportError:
    # Fallback if addon_path is not available, though it should be.
    # This might happen if structure is different or during isolated testing.
    # __name__ here would be 'options_dialog'. We need the package name.
    # A more robust way might be to pass addon_name to show_config_dialog.
    # For now, relying on addon_path from config.py.
    print("Extended HTML Editor: Could not determine ADDON_NAME for config dialog.")
    ADDON_NAME = "1043915942" # Fallback to known ID, less ideal.


class ConfigDialog(QDialog):
    def __init__(self, parent=None, current_addon_name=None):
        super().__init__(parent)
        self.setWindowTitle("Extended HTML Editor Options")

        self.addon_name = current_addon_name or ADDON_NAME
        self.config = mw.addonManager.getConfig(self.addon_name)

        layout = QVBoxLayout(self)

        self.copy_html_shortcut_checkbox = QCheckBox("Copy selection as HTML source on Ctrl+C/⌘C")
        # Use gc (from .config) to ensure DEFAULTS are respected if key is missing
        # However, getConfig should already provide this based on schema or defaults.
        # For simplicity, directly get from loaded config, assuming gc populates it initially.
        self.copy_html_shortcut_checkbox.setChecked(self.config.get("copyHtmlOnShortcut", False))
        layout.addWidget(self.copy_html_shortcut_checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        self.config["copyHtmlOnShortcut"] = self.copy_html_shortcut_checkbox.isChecked()
        mw.addonManager.writeConfig(self.addon_name, self.config)
        super().accept()

def show_config_dialog(current_addon_name_for_config):
    # Pass the add-on name from __init__.py's __name__
    dialog = ConfigDialog(mw, current_addon_name=current_addon_name_for_config)
    dialog.exec()

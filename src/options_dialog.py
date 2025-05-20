# options_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QLabel, QKeySequenceEdit
)
from PyQt6.QtCore import Qt
from aqt import mw
from aqt.qt import QKeySequence
import os

from .config import gc

# Helper function to convert key sequence to string (similar to editor.py)
def keystr(k):
    key = QKeySequence(k)
    return key.toString(QKeySequence.SequenceFormat.NativeText)

# Assuming config.py and this file are in the same directory (addon root)
# and config.py defines addon_path
try:
    from .config import addon_path
    ADDON_NAME = os.path.basename(addon_path)
except ImportError:
    print("Extended HTML Editor: Could not determine ADDON_NAME for config dialog.")
    ADDON_NAME = "1900436383" # Fallback to known ID, less ideal.


class ConfigDialog(QDialog):
    def __init__(self, parent=None, current_addon_name=None):
        super().__init__(parent)
        self.setWindowTitle("Extended HTML Editor Options")

        self.addon_name = current_addon_name or ADDON_NAME
        self.config = mw.addonManager.getConfig(self.addon_name)

        layout = QVBoxLayout(self)

        # Shortcut editor
        layout.addWidget(QLabel("Shortcut for Copy HTML/Plain Text:"))
        self.shortcut_edit = QKeySequenceEdit()
        self.shortcut_edit.setKeySequence(QKeySequence(gc("copyShortcut", False) or "Ctrl+Shift+H"))
        layout.addWidget(self.shortcut_edit)

        # Get the configured shortcut for checkbox labels
        current_shortcut_str = self.shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
        if not current_shortcut_str:
            current_shortcut_str = "Ctrl+Shift+H"

        self.copy_html_shortcut_checkbox = QCheckBox(f"Copy selection as HTML source on {keystr(current_shortcut_str)}")
        self.copy_html_shortcut_checkbox.setChecked(self.config.get("copyHtmlOnShortcut", False))
        layout.addWidget(self.copy_html_shortcut_checkbox)

        self.copy_plain_checkbox = QCheckBox(f"Copy cleaned plain-text/LaTeX on {keystr(current_shortcut_str)}")
        self.copy_plain_checkbox.setChecked(self.config.get("copyPlainOnShortcut", False))
        layout.addWidget(self.copy_plain_checkbox)

        # Update checkbox labels when shortcut_edit changes
        def update_checkbox_labels(key_sequence):
            ks = keystr(key_sequence.toString(QKeySequence.SequenceFormat.PortableText))
            if not ks:
                ks = keystr("Ctrl+Shift+H")
            self.copy_html_shortcut_checkbox.setText(f"Copy selection as HTML source on {ks}")
            self.copy_plain_checkbox.setText(f"Copy cleaned plain-text/LaTeX on {ks}")

        self.shortcut_edit.keySequenceChanged.connect(update_checkbox_labels)

        def sync_boxes(src, other):
            if src.isChecked():
                other.setChecked(False)

        self.copy_html_shortcut_checkbox.stateChanged.connect(
            lambda _ : sync_boxes(self.copy_html_shortcut_checkbox,
                                  self.copy_plain_checkbox))
        self.copy_plain_checkbox.stateChanged.connect(
            lambda _ : sync_boxes(self.copy_plain_checkbox,
                                  self.copy_html_shortcut_checkbox))

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        self.config["copyHtmlOnShortcut"] = self.copy_html_shortcut_checkbox.isChecked()
        self.config["copyPlainOnShortcut"] = self.copy_plain_checkbox.isChecked()
        self.config["copyShortcut"] = self.shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
        mw.addonManager.writeConfig(self.addon_name, self.config)
        super().accept()

def show_config_dialog(current_addon_name_for_config):
    dialog = ConfigDialog(mw, current_addon_name=current_addon_name_for_config)
    dialog.exec()

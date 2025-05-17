# for license info see lixense.txt in this folder

from aqt import gui_hooks
from aqt import mw
from aqt.qt import *

from . import editor
from . import clayout_adjust

# Import for new features
from .options_dialog import show_config_dialog
from .config import gc # To read the "copyHtmlOnShortcut" preference
from .editor import copy_selected_html_from_webview # The generic copy function

from PyQt6.QtCore import QObject, QEvent, Qt as Qt_core # Renamed to avoid conflict with wildcard import
from PyQt6.QtGui import QKeySequence
from aqt.webview import AnkiWebView


# this should avoid error after importing backup
# __init__.py", line 11, in run_after_profile_did_open
#    mw.col.cmhelper_field_content = None
# AttributeError: 'NoneType' object has no attribute 'cmhelper_field_content'
def try_workaround():
    if mw.col:
        mw.col.cmhelper_field_content = None


def run_after_profile_did_open():
    try:
        mw.col.cmhelper_field_content = None
    except:
        t = QTimer(mw)
        t.timeout.connect(try_workaround)
        t.setSingleShot(True)
        t.start(500)
gui_hooks.profile_did_open.append(run_after_profile_did_open)


# --- Configuration UI Setup ---
def on_addon_config_requested():
    # Pass __name__ (which is the add-on's package name like "1043915942")
    # to the dialog so it can correctly interact with addonManager for this addon.
    show_config_dialog(__name__)

mw.addonManager.setConfigAction(__name__, on_addon_config_requested)


# --- Global HTML Copy Event Filter ---
class GlobalHtmlCopyFilter(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not gc("copyHtmlOnShortcut", False):
            return False # Feature not enabled, pass event through

        if event.type() == QEvent.Type.KeyPress:
            # Use keyCombination() for Qt5/Qt6 compatibility if QKeySequence.StandardKey is problematic
            # For Qt6, event.keyCombination() is good.
            if QKeySequence(event.keyCombination()) == QKeySequence(QKeySequence.StandardKey.Copy):
                focused_widget = mw.app.focusWidget()
                target_webview = None

                # Traverse up the parent hierarchy to find an AnkiWebView
                current_widget = focused_widget
                while current_widget:
                    if isinstance(current_widget, AnkiWebView):
                        target_webview = current_widget
                        break
                    current_widget = current_widget.parent()

                if target_webview:
                    # Determine a suitable parent for dialogs (showWarning)
                    # The webview itself or mw (main window) are candidates
                    parent_for_dialogs = target_webview # AnkiWebView is a QWidget
                    copy_selected_html_from_webview(target_webview, parent_for_dialogs)
                    return True # Event handled, stop further processing

        return False # Event not handled by this filter


# Install the event filter instance on application load
# Ensure it's only installed once
if not hasattr(mw, "_global_html_copy_filter_instance_1043915942"): # Unique attribute name
    # Parent the filter to mw to manage its lifetime with Anki's main window
    filter_instance = GlobalHtmlCopyFilter(mw)
    mw.app.installEventFilter(filter_instance)
    setattr(mw, "_global_html_copy_filter_instance_1043915942", filter_instance)

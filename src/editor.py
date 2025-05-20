import os
import warnings
import json  # Added for parsing JS output

from bs4 import BeautifulSoup

from anki.hooks import addHook, wrap
# Added gui_hooks for modern Anki versions
from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.qt import (
    QKeySequence,
    QShortcut,
    Qt,
    QApplication,  # Added for clipboard access
    QClipboard,    # Added for clipboard access
)
from aqt.utils import (
    tooltip,
    showWarning,   # Added for user feedback
)


from .anki_version_detection import anki_point_version
from .config import addon_path, gc, unique_string
from .dialog_cm import CmDialogField
from .helpers import now, read_file
from .html_process import maybe_minify, maybe_format__prettify
from .web_utils import call_get_selection  # Added import



# from Sync Cursor Between Fields and HTML Editor by Glutanimate
# https://ankiweb.net/shared/info/138856093
# based on SO posts by Tim Down / B T (http://stackoverflow.com/q/16095155)
js_move_cursor = read_file("move_cursor.js")


def on_CMdialog_finished(self, status):
    if status:
        html = mw.col.cmhelper_field_content
        # from editor.py/_onHtmlEdit to "fix" invalid html

        if anki_point_version >= 36:
            image_func = self.mw.col.media.escape_media_filenames
        else:
            image_func = self.mw.col.media.escapeImages

        if html.find(">") > -1:
            # filter html through beautifulsoup so we can strip out things like a
            # leading </div>
            html_escaped = image_func(html)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                html_escaped = str(BeautifulSoup(html_escaped, "html.parser"))
                html = image_func(
                    html_escaped, unescape=True
                )
        content = maybe_minify(html)
    else:  # restore old
        content = self.original_cm_text

    try:
        note = mw.col.getNote(self.nid) if anki_point_version <= 53 else mw.col.get_note(self.nid)
    except:   # new note
        self.note.fields[self.original_current_field] = content.replace(unique_string, "")
        # self.note.flush()  # doesn't work in 2.1.28
    else:
        note.fields[self.original_current_field] = content
        note.flush()
        mw.requireReset()
        mw.reset()
    self.loadNote(focusTo=self.original_current_field)
    # the function setSelectionByCharacterOffsets isn't precise and sometimes produces errors
    # with complex content and ruins the field contents. So cursor sync just works in one way ....
    # in 2022-09 I removed the code that inserted the unique_string in tinymce5 to
    # mark the cursor position with commit d082c75
    # self.web.eval(js_move_cursor % pos)
Editor.on_CMdialog_finished = on_CMdialog_finished


def _cm_start_dialog(self):
    win_title = 'Anki - edit html source code for field in codemirror'
    pretty_content = maybe_format__prettify(self.note.fields[self.original_current_field])
    d = CmDialogField(self.widget, pretty_content, "htmlmixed", win_title)
    # exec() doesn't work - jseditor isn't loaded = blocked
    # finished.connect via https://stackoverflow.com/questions/39638749/
    d.finished.connect(self.on_CMdialog_finished)
    d.setModal(True)
    d.show()
    d.web.setFocus()


def cm_start_dialog_helper(self):
    if self.original_current_field is None:
        tooltip("No field selected. Aborting ...")
        return
    self.original_cm_text = self.note.fields[self.original_current_field]
    self.cm_nid = self.note.id
    self.web.eval("""setFormat("insertText", "%s");""" % unique_string)
    self.saveNow(lambda s=self: _cm_start_dialog(s))


def cm_start_dialog(self):
    self.saveNow(lambda s=self: cm_start_dialog_helper(s))


def undo_html_extended(self):
    if self.cm_nid != self.note.id:
        return
    if not hasattr(self, "original_cm_text") or not self.original_cm_text:
        return
    if not hasattr(self, "original_current_field"):  # may be index 0
        return
    self.note.fields[self.original_current_field] = self.original_cm_text
    self.loadNote()
    self.web.setFocus()
    self.loadNote(focusTo=self.original_current_field)


def mirror_start(self):
    modifiers = self.mw.app.queryKeyboardModifiers()
    shift_and_click = modifiers == Qt.KeyboardModifier.ShiftModifier
    if shift_and_click:
        undo_html_extended(self)
        return
    self.original_current_field = self.currentField
    self.saveNow(lambda s=self: cm_start_dialog(s))
Editor.mirror_start = mirror_start


def keystr(k):
    key = QKeySequence(k)
    return key.toString(QKeySequence.SequenceFormat.NativeText)


# Generic function to copy selected HTML from a webview
def copy_selected_html_from_webview(webview, parent_for_dialogs=None, warn_if_empty=True, copy_type="html"): # Added copy_type
    if parent_for_dialogs is None:
        parent_for_dialogs = mw # Default to main window if no specific parent

    def on_selection_copied(payload): # Expects an object/dict
        if not payload:
            if warn_if_empty:
                tooltip("Selection was empty or could not be processed.")
            return

        content_to_copy = ""
        if copy_type == "html":
            content_to_copy = payload.get("html")
        elif copy_type == "text":
            content_to_copy = payload.get("text")

        if not content_to_copy:
            if warn_if_empty:
                tooltip(f"No {copy_type} content found in selection.")
            return

        try:
            cb = QApplication.clipboard()
            if copy_type == "html":
                # For HTML, it's good practice to set both HTML and plain text versions
                # For a richer HTML copy, one would use QMimeData.
                cb.setText(content_to_copy, QClipboard.Mode.Clipboard)
            else: # plain text
                cb.setText(content_to_copy, QClipboard.Mode.Clipboard)
            # tooltip(f"{copy_type.capitalize()} content copied to clipboard.") # Optional feedback
        except Exception as e:
            showWarning(f"Failed to copy {copy_type} to clipboard: {e}", parent=parent_for_dialogs)

    call_get_selection(webview, on_selection_copied)


# Function to handle copying HTML (used by the manual button)
def onCopyHtml(editor):
    # editor.widget is the QWidget containing the editor, good parent for dialogs
    copy_selected_html_from_webview(editor.web, parent_for_dialogs=editor.widget, copy_type="html") # warn_if_empty defaults to True

# New function to handle copying Plain Text
def onCopyPlainText(editor):
    copy_selected_html_from_webview(editor.web, parent_for_dialogs=editor.widget, copy_type="text")

# Function to set up the new copy button
def setupCustomCopyButtons(buttons: list[str], editor): # Renamed function
    # Add a new toolbar button that triggers our onCopyHtml function
    editor._links["copyHtml"] = onCopyHtml
    btn_html = editor.addButton(
        None,
        "copyHtml",
        onCopyHtml,
        tip="Copy selection as HTML source"
    )
    buttons.append(btn_html)

    # Add the "Copy Plain Text" button
    editor._links["copyPlainText"] = onCopyPlainText
    btn_plain_text = editor.addButton(
        None, # No icon for now
        "copyPlainText", # Unique command name
        onCopyPlainText, # Function to call
        tip="Copy selection as Plain Text (MathJax as TeX)" # Tooltip
    )
    buttons.append(btn_plain_text)
    return buttons


def add_editor_button(buttons, editor):
    k = gc("hotkey_codemirror", "Ctrl+Shift+Y")
    b = editor.addButton(
        icon=os.path.join(addon_path, "web/codemirror/doc", "logo.png"),
        cmd="CM",
        func=mirror_start,
        tip="extended edit html source ({})".format(keystr(k)),
        keys=k)
    buttons.append(b)
    return buttons


# set shortcut for built-in viewer WITHOUT adding a button
def setupShortcuts_wrapper(self):
    cuts = [
        (gc('hotkey_codemirror'), self.mirror_start),
    ]
    for row in cuts:
        if len(row) == 2:
            keys, fn = row
            fn = self._addFocusCheck(fn)
        else:
            keys, fn, _ = row
        QShortcut(QKeySequence(keys), self.widget, activated=fn)


if gc("anki editor: add button", True):
    addHook("setupEditorButtons", add_editor_button)
else:
    Editor.setupShortcuts = wrap(Editor.setupShortcuts, setupShortcuts_wrapper)

# Register the new button hook
# Use gui_hooks if available (modern Anki versions), fallback to addHook for older versions
try:
    gui_hooks.editor_did_init_buttons.append(setupCustomCopyButtons) # Use renamed function
except AttributeError:
    # Fallback for older Anki versions that don't have gui_hooks.editor_did_init_buttons
    # addHook is already imported at the top of the file
    addHook("setupEditorButtons", setupCustomCopyButtons) # Use renamed function

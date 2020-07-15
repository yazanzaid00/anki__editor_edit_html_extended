import os

from anki.hooks import addHook, wrap

from aqt import mw
from aqt.qt import (
    QKeySequence,
    QShortcut,
    Qt,
)
from aqt.editor import Editor

from .config import addon_path, gc, unique_string
from .dialog_cm import CmDialog
from .helpers import now, readfile
from .html_process import postprocess, prettify



# from Sync Cursor Between Fields and HTML Editor by Glutanimate
# https://ankiweb.net/shared/info/138856093
# based on SO posts by Tim Down / B T (http://stackoverflow.com/q/16095155)
js_move_cursor = readfile("move_cursor.js")


def _onCMUpdateField(self):
    c = postprocess(mw.col.cmhelper_field_content)
    # bs4ed = bs4.BeautifulSoup(c, "html.parser")
    # ef_text = bs4ed.getText().replace('\n', ' ')
    # pos = len(ef_text.split(unique_string)[0])

    # maybe this?
    # if not self.addMode:
    #     note.fields[self.myfield] = c
    #     note.flush()
    #     mw.requireReset()
    #     mw.reset()
    # else:
    #     self.note.fields[self.myfield] = c.replace(unique_string, "")

    try:
        note = mw.col.getNote(self.nid)
    except:   # new note
        self.note.fields[self.myfield] = c.replace(unique_string, "")
        # self.note.flush()  # doesn't work in 2.1.28
    else:
        note.fields[self.myfield] = c
        note.flush()
        mw.requireReset()
        mw.reset()
    self.loadNote(focusTo=self.myfield)
    # the function setSelectionByCharacterOffsets isn't precise and sometimes produces errors 
    # with complex content and ruins the field contents. So cursor sync just works in one way ....
    # self.web.eval(js_move_cursor % pos)
Editor._onCMUpdateField = _onCMUpdateField


def on_CMdialog_finished(self, status):
    if status:
        self.saveNow(lambda: self._onCMUpdateField())
    else:
        self.note.fields[self.cm_field] = self.original_cm_text
        self.saveTags()
        self.note.flush()
        self.loadNote(focusTo=self.cm_field)
Editor.on_CMdialog_finished = on_CMdialog_finished


def _cm_start_dialog(self, field):
    win_title = 'Anki - edit html source code for field in codemirror'
    pretty_content = prettify(self.note.fields[field])
    d = CmDialog(None, pretty_content, "htmlmixed", win_title, True, False, self.note)
    # exec_() doesn't work - jseditor isn't loaded = blocked
    # finished.connect via https://stackoverflow.com/questions/39638749/
    d.finished.connect(self.on_CMdialog_finished)
    d.setModal(True)
    d.show()
    d.web.setFocus()
Editor._cm_start_dialog = _cm_start_dialog


def cm_start_dialog_helper(self, field):
    self.original_cm_text = self.note.fields[field]
    self.cm_field = field
    self.cm_nid = self.note.id
    self.web.eval("""setFormat("insertText", "%s");""" % unique_string)
    self.saveNow(lambda: self._cm_start_dialog(field))
Editor.cm_start_dialog_helper = cm_start_dialog_helper


def cm_start_dialog(self, field):
    self.saveNow(lambda: self.cm_start_dialog_helper(field))
Editor.cm_start_dialog = cm_start_dialog


def mirror_start(self):
    modifiers = self.mw.app.queryKeyboardModifiers()
    shift_and_click = modifiers == Qt.ShiftModifier
    if shift_and_click:
        self.myOnFieldUndoHtmlExtended()
        return
    self.myfield = self.currentField
    self.saveNow(lambda: self.cm_start_dialog(self.myfield))
Editor.mirror_start = mirror_start


def myOnFieldUndoHtmlExtended(self):
    if self.cm_nid != self.note.id:
        return
    if not hasattr(self, "original_cm_text") or not self.original_cm_text:
        return
    if not hasattr(self, "cm_field"):  # may be index 0
        return
    self.note.fields[self.cm_field] = self.original_cm_text
    self.loadNote()
    self.web.setFocus()
    self.loadNote(focusTo=self.cm_field)
Editor.myOnFieldUndoHtmlExtended = myOnFieldUndoHtmlExtended


def keystr(k):
    key = QKeySequence(k)
    return key.toString(QKeySequence.NativeText)


def setupEditorButtonsFilter(buttons, editor):
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
def mySetupShortcuts(self):
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


if gc("editor_menu_show_button", True):
    addHook("setupEditorButtons", setupEditorButtonsFilter)
else:
    Editor.setupShortcuts = wrap(Editor.setupShortcuts, mySetupShortcuts)

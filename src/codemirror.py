"""
anki-addon: edit html source code for field with codemirror in extrawindow

Copyright (c) 2019 ignd
          (c) 2019 Joseph Lorimer <joseph@lorimer.me>
              https://github.com/luoliyan/anki-misc/blob/master/html-editor-tweaks/__init__.py
              https://ankiweb.net/shared/info/410936778
          (c) 2013, Dave Mankoff
          (c) 2017 Glutanimate
          (c) Ankitects Pty Ltd and contributors


This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.



This add-on bundles the file "sync_execJavaScript.py" which has this copyright and permission
notice: 

    Copyright: 2014 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
                  (taken from https://github.com/pycom/EricShort/blob/master/UI/Previewers/PreviewerHTML.py)
    License: GPLv3 or later, https://github.com/pycom/EricShort/blob/025a9933bdbe92f6ff1c30805077c59774fa64ab/LICENSE.GPL3



This file incorporates work (i.e. the function postprocess and reindent)
covered by the following copyright and permission notice:

    Copyright © 2019 Joseph Lorimer <joseph@lorimer.me>

    Permission to use, copy, modify, and distribute this software for any
    purpose with or without fee is hereby granted, provided that the above
    copyright notice and this permission notice appear in all copies.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.



This add-on bundles and  makes Anki load the js package codemirror, http://codemirror.net/,
which includes this LICENSE file:

    MIT License

    Copyright (C) 2017 by Marijn Haverbeke <marijnh@gmail.com> and others

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.



This addon bundles parts of the htmlmin package, https://github.com/mankyd/htmlmin,
covered by the following copyright and permission notice:
    Copyright (c) 2013, Dave Mankoff
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:
        * Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.
        * Neither the name of Dave Mankoff nor the
        names of its contributors may be used to endorse or promote products
        derived from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL DAVE MANKOFF BE LIABLE FOR ANY
    DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
    ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


This add-on bundles and  makes Anki load the js package htmlhint.js,
which has this LICENSE info, https://github.com/htmlhint/HTMLHint/blob/master/LICENSE.md:
    (https://cdn.jsdelivr.net/npm/htmlhint@latest/dist/htmlhint.js)

    MIT License

    Copyright (c) 2014-2016 Yanis Wang <yanis.wang@gmail.com>

    Copyright (c) 2018 David Dias (Thanks to the initial contributor Yanis Wang)

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



"""


import datetime
import io
import os
import pathlib
from pprint import pprint as pp
import re
import subprocess
from tempfile import NamedTemporaryFile
import warnings

import bs4

from anki.hooks import addHook, wrap
from anki.utils import isWin, isMac
from aqt import mw
from aqt.qt import (
    QCursor,
    QDialog,
    QKeySequence,
    QShortcut,
    QSizePolicy,
    Qt,
)
from aqt.editor import Editor
from aqt.webview import AnkiWebView
from aqt.utils import (
    askUser,
    restoreGeom,
    saveGeom,
    showInfo,
    tooltip,
    openFolder
)

from .htmlmin import Minifier
from .sync_execJavaScript import sync_execJavaScript

from .forms import edit_window
from .forms import versions


from anki import version as anki_version
_, _, point = anki_version.split(".")
pointversion = int(point)




def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    return fail


addon_path = os.path.dirname(__file__)
addonfoldername = os.path.basename(addon_path)
regex = r"(web[/\\].*)"
mw.addonManager.setWebExports(__name__, regex)
codemirror_path = "/_addons/%s/web/" % addonfoldername


# unique_string = '<span style="display:none">äöüäöü</span>'
unique_string = 'äöüäöü'

themes = ["3024-day", "3024-night", "abcdef", "ambiance", "ambiance-mobile",
          "base16-dark", "base16-light", "bespin", "blackboard", "cobalt", "colorforth",
          "darcula", "dracula", "duotone-dark", "duotone-light", "eclipse", "elegant",
          "erlang-dark", "gruvbox-dark", "hopscotch", "icecoder", "idea", "isotope",
          "lesser-dark", "liquibyte", "lucario", "material", "mbo", "mdn-like",
          "midnight", "monokai", "neat", "neo", "night", "oceanic-next", "panda-syntax",
          "paraiso-dark", "paraiso-light", "pastel-on-dark", "railscasts", "rubyblue",
          "seti", "shadowfox", "solarized", "ssms", "the-matrix", "tomorrow-night-bright",
          "tomorrow-night-eighties", "ttcn", "twilight", "vibrant-ink", "xq-dark",
          "xq-light", "yeti", "zenburn",
          "moxer", "material-darker", "material-palenight", "material-ocean"]


if mw.pm.night_mode():
    if gc('theme night mode') in themes:
        selectedtheme = gc('theme night mode')
    else:
        selectedtheme = "dracula"
else:
    if gc('theme') in themes:
        selectedtheme = gc('theme')
    else:
        selectedtheme = "neat"
themepath = "codemirror/theme/" + selectedtheme + ".css"

uk = gc('keymap', "some_string_so_that_I_can_lower_it").lower()
if uk in ["sublime", "emacs", "vim"]:
    if uk == 'vim':
        keymap = [uk, "true"]
    else:
        keymap = [uk, "false"]
else:
    keymap = ["sublime", "false"]
keymappath = "codemirror/keymap/" + keymap[0] + ".js"


addon_cssfiles = ["codemirror/lib/codemirror.css",
                  "codemirror/addon/lint/lint.css",
                  "codemirror/addon/hint/show-hint.css",
                  "codemirror/addon/dialog/dialog.css",
                  "codemirror/addon/search/matchesonscrollbar.css",
                  "codemirror/lib/codemirror.css",
                  themepath,
                  "codemirror/addon/display/fullscreen.css",
                  "webview_override.css",
                  ]
other_cssfiles = []
cssfiles = addon_cssfiles + other_cssfiles

addon_jsfiles = ["codemirror/lib/codemirror.js",
                 "htmlhint.js",
                 keymappath,
                 "codemirror/addon/hint/show-hint.js",
                 "codemirror/addon/hint/javascript-hint.js",
                 "codemirror/addon/hint/html-hint.js",
                 "codemirror/addon/hint/css-hint.js",
                 "codemirror/addon/hint/xml-hint.js",
                 "codemirror/addon/fold/xml-fold.js",
                 "codemirror/mode/xml/xml.js",
                 "codemirror/mode/javascript/javascript.js",
                 "codemirror/mode/css/css.js",
                 "codemirror/mode/htmlmixed/htmlmixed.js",
                 "codemirror/addon/edit/matchbrackets.js",
                 "codemirror/addon/comment/comment.js",
                 "codemirror/addon/dialog/dialog.js",
                 "codemirror/addon/search/searchcursor.js",
                 "codemirror/addon/search/search.js",
                 "codemirror/addon/scroll/annotatescrollbar.js",
                 "codemirror/addon/search/matchesonscrollbar.js",
                 "codemirror/addon/search/jump-to-line.js",
                 "codemirror/addon/selection/active-line.js",
                 "codemirror/addon/edit/closebrackets.js",
                 "codemirror/addon/wrap/hardwrap.js",
                 "codemirror/addon/fold/foldcode.js",
                 "codemirror/addon/fold/brace-fold.js",
                 "codemirror/addon/lint/lint.js",
                 "codemirror/addon/lint/javascript-lint.js",
                 "codemirror/addon/lint/json-lint.js",
                 "codemirror/addon/lint/html-lint.js",
                 "codemirror/addon/lint/css-lint.js",
                 ]

other_jsfiles = ["jquery.js", ]
jsfiles = addon_jsfiles + other_jsfiles


class MyWebView(AnkiWebView):
    def bundledScript(self, fname):
        if fname in addon_jsfiles:
            return '<script src="%s"></script>' % (codemirror_path + fname)
        else:
            return '<script src="%s"></script>' % self.webBundlePath(fname)

    def bundledCSS(self, fname):
        if fname in addon_cssfiles:
            return '<link rel="stylesheet" type="text/css" href="%s">' % (codemirror_path + fname)
        else:
            return '<link rel="stylesheet" type="text/css" href="%s">' % self.webBundlePath(fname)


def now():
    CurrentDT=datetime.datetime.now()
    return CurrentDT.strftime("%Y-%m-%d___%H-%M-%S")


class OldVersions(QDialog):
    def __init__(self, parent, note, boxname, folder, currContent):
        QDialog.__init__(self, parent, Qt.Window)
        self.parent = parent
        self.note = note
        self.boxname = boxname
        self.folder = folder
        self.currContent = currContent
        self.versions = sorted(os.listdir(self.folder), reverse=True)
        self.model = self.note.model()
        self.dialog = versions.Ui_Dialog()
        self.dialog.setupUi(self)
        restoreGeom(self, "1043915942_OldVersions")
        self.setWindowTitle("Anki - manage prior versions of this card template element")
        self.dialog.pb_folder.clicked.connect(self.openFolder)
        self.dialog.pb_diff.clicked.connect(self.onDiff)
        self.dialog.textEdit.setReadOnly(True)
        self.setupCombo()

    def setupCombo(self):
        self.dialog.comboBox.currentIndexChanged.connect(self.updateTextEdit)
        for f in self.versions:
            self.dialog.comboBox.addItem(f)
        self.updateTextEdit()

    def updateTextEdit(self):
        i = self.dialog.comboBox.currentIndex()
        p = os.path.join(self.folder, self.versions[i])
        with io.open(p, "r", encoding="utf-8") as f:
            content = f.read()
        self.dialog.textEdit.setPlainText(content)

    def openFolder(self):
        openFolder(self.folder)

    def onDiff(self):
        i = self.dialog.comboBox.currentIndex()
        try:
            old = self.versions[i]
        except:
            tooltip('no saved versions for the "{}" of this model found. Aborting...'.format(
                self.boxname))
        oldabs = os.path.join(self.folder, old)

        if self.boxname == "css":
            ext = ".css"
        else:
            ext = ".html"
        suf = "current" + ext
        cur = NamedTemporaryFile(delete=False, suffix=suf)
        cur.write(str.encode(self.currContent))
        cur.close()

        cmd = gc("diffcommandstart")
        if not isinstance(cmd, list):
            tooltip("Invalid settings for 'diffcommand'. Must be a list. Aborting ...")
            return
        cmd.extend([cur.name, oldabs])
        try:
            subprocess.Popen(cmd)
        except:
            tooltip("Error while trying to open the external editor. Maybe there's an error in your config.")

    def reject(self):
        saveGeom(self, "1043915942_OldVersions")
        QDialog.reject(self)


class MyDialog(QDialog):
    def __init__(self, parent, bodyhtml, win_title, js_save_cmd, isfield, boxname, note):
        super(MyDialog, self).__init__(parent)
        self.parent = parent
        self.note = note
        self.model = self.note.model()
        self.boxname = boxname
        self.js_save_cmd = js_save_cmd
        self.setWindowTitle(win_title)
        self.dialog = edit_window.Ui_Dialog()
        self.dialog.setupUi(self)
        self.dialog.outer.setContentsMargins(0, 0, 0, 0)
        self.dialog.outer.setSpacing(0)
        if isfield:
            self.dialog.wid_buts.setVisible(False)
        self.web = MyWebView(self)
        self.dialog.outer.addWidget(self.web)
        qsp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        qsp.setVerticalStretch(2)
        self.web.setSizePolicy(qsp)
        acceptShortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        acceptShortcut.activated.connect(self.onAccept)
        self.web.title = "html source with codemirror"
        self.web.contextMenuEvent = self.contextMenuEvent
        self.web.stdHtml(bodyhtml, cssfiles, jsfiles)
        self.dialog.pb_save.clicked.connect(self.onSave)
        self.dialog.pb_viewold.clicked.connect(self.onView)
        restoreGeom(self, "1043915942_MyDialog")

    def onSave(self):
        if self.boxname:
            self.onTemplateSave()
        else:
            pass

    # maybe relevant for editor?
    # def template_save_path(self):
    #     base = os.path.join(addon_path, "user_files")
    #     if gc("backup_template_path"):
    #         user = gc("backup_template_path")
    #         if os.path.isdir(base):
    #             base = user
    #         else:
    #             tooltip('Invalid setting for "backup_template_path". This is not a directory. '
    #                     'Using default path in add-on folder')
    #     # don't use model['name'] in case a user renames a template ...
    #     return os.path.join(base, str(self.model['id']), self.boxname)

    def onTemplateSave(self):
        content = self.__execJavaScript(self.js_save_cmd)
        self.parent.saveStringForBox(self.boxname, content)
        # maybe reintrodue as as class  
        #     if self.boxname == "css":
        #         ext = ".css"
        #     else:
        #         ext = ".html"
        #     folder = self.template_save_path()
        #     filename = now() + ext
        #     pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
        #     p = os.path.join(folder, filename)
        #     with io.open(p, "w", encoding="utf-8") as f:
        #         f.write(content)
        #         tooltip('saved as {}'.format(filename))

    def onView(self):
        currContent = self.__execJavaScript(self.js_save_cmd)
        folder = self.parent.template_save_path(self.boxname)
        if not os.path.isdir(folder):
            tooltip("no prior versions found")
            return
        d = OldVersions(self, self.note, self.boxname, folder, currContent)
        if d.exec():
            pass

    def accept(self):
        self.onAccept()

    def onAccept(self):
        global edited_fieldcontent
        # replace cursor with unique string
        s = """insertTextAtCursor('%s')""" % unique_string
        self.__execJavaScript(s)
        edited_fieldcontent = self.__execJavaScript(self.js_save_cmd)
        saveGeom(self, "1043915942_MyDialog")
        QDialog.accept(self)

    def onReject(self):
        ok = askUser("Close and discard changes?")
        if ok:
            saveGeom(self, "1043915942_MyDialog")
            self.reject()

    def closeEvent(self, event):
        ok = askUser("Close and discard changes?")
        if ok:
            event.ignore()
            saveGeom(self, "1043915942_MyDialog")
            self.reject()
        else:
            event.ignore()

    def __execJavaScript(self, script):
        return sync_execJavaScript(self.web, script)


open_space_open = re.compile('(<[^/>]+>) (<[^/>]+>)')
close_space_close = re.compile('(</[^>]+>) (</)')
open_space_text = re.compile('(<[^/>]+>) ([^<>]+)')
open_text_close = re.compile('(<[^/>]+>) ([^<>]+) (</)')
tag_space_punc = re.compile('(>) ([.,:;])')


# the function postprocess from https://ankiweb.net/shared/info/410936778 
# doesn't work with syntax highlighted code


def postprocess(s):
    if not gc("fold after close", True):
        return s
    minifier = Minifier()
    for l in s.splitlines():
        minifier.input(l)
    out = minifier.output
    return out


def reindent(s, factor=4):
    """Increase indentation of pretty printed HTML.

    Beautiful Soup indents by a single space at each indentation level,
    probably because it also places each tag on its own line, resulting
    in heavily nested markup. In many situations this will pose
    readability issues, but in Anki the editor only deals with HTML
    fragments, not entire documents. 4 spaces is more reasonable.
    """
    t = []
    for line in s.split('\n'):
        r = re.match('( +)([^ ].*)', line)
        if r:
            n = len(r.group(1)) * factor
            t.append('{}{}'.format(' ' * n, r.group(2)))
        else:
            t.append(line)
    return '\n'.join(t)


def prettify(html):
    bs4ed = bs4.BeautifulSoup(html, "html.parser").prettify(formatter='html5')
    if gc("format") == "bs4-prettified":
        return bs4ed
    elif gc("format") == "tweaked":
        return reindent(bs4ed)
    else:
        return html


# from Sync Cursor Between Fields and HTML Editor by Glutanimate
# https://ankiweb.net/shared/info/138856093
# based on SO posts by Tim Down / B T (http://stackoverflow.com/q/16095155)
js_move_cursor = """
    function findHiddenCharacters(node, beforeCaretIndex) {
    var hiddenCharacters = 0
    var lastCharWasWhiteSpace=true
    for(var n=0; n-hiddenCharacters<beforeCaretIndex &&n<node.length; n++) {
        if([' ','\\n','\\t','\\r'].indexOf(node.textContent[n]) !== -1) {
            if(lastCharWasWhiteSpace)
                hiddenCharacters++
            else
                lastCharWasWhiteSpace = true
        } else {
            lastCharWasWhiteSpace = false   
        }
    }

    return hiddenCharacters
}

var setSelectionByCharacterOffsets = null;

if (window.getSelection && document.createRange) {
    setSelectionByCharacterOffsets = function(containerEl, position) {
        var charIndex = 0, range = document.createRange();
        range.setStart(containerEl, 0);
        range.collapse(true);
        var nodeStack = [containerEl], node, foundStart = false, stop = false;

        while (!stop && (node = nodeStack.pop())) {
            if (node.nodeType == 3) {
                var hiddenCharacters = findHiddenCharacters(node, node.length)
                var nextCharIndex = charIndex + node.length - hiddenCharacters;

                if (position >= charIndex && position <= nextCharIndex) {
                    var nodeIndex = position - charIndex
                    var hiddenCharactersBeforeStart = findHiddenCharacters(node, nodeIndex)
                    range.setStart(node, nodeIndex + hiddenCharactersBeforeStart );
                    range.setEnd(node, nodeIndex + hiddenCharactersBeforeStart);
                    stop = true;
                }
                charIndex = nextCharIndex;
            } else {
                var i = node.childNodes.length;
                while (i--) {
                    nodeStack.push(node.childNodes[i]);
                }
            }
        }

        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    }
} else if (document.selection) {
    setSelectionByCharacterOffsets = function(containerEl, start, end) {
        var textRange = document.body.createTextRange();
        textRange.moveToElementText(containerEl);
        textRange.collapse(true);
        textRange.moveEnd("character", end);
        textRange.moveStart("character", start);
        textRange.select();
    };
}


setSelectionByCharacterOffsets(currentField, %s)
"""


def _onCMUpdateField(self):
    c = postprocess(edited_fieldcontent)
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


def readfile():
    addondir = os.path.join(os.path.dirname(__file__))
    templatefile = "codemirror.html"
    filefullpath = os.path.join(addondir, templatefile)
    with io.open(filefullpath, "r", encoding="utf-8") as f:
        return f.read()


def _cm_start_dialog(self, field):
    tmpl_content = readfile()
    win_title = 'Anki - edit html source code for field in codemirror'
    js_save_cmd = "editor.getValue()"
    pretty_content = prettify(self.note.fields[field])
    bodyhtml = tmpl_content.format(
        content=pretty_content,
        isvim=keymap[1],
        keymap=keymap[0],
        mode="htmlmixed",
        theme=selectedtheme,
        unique_string=unique_string,
        lint="true"
    )
    d = MyDialog(None, bodyhtml, win_title, js_save_cmd, True, False, self.note)
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



















from aqt.clayout import CardLayout


def template_save_path(self, boxname):
    base = os.path.join(addon_path, "user_files")
    if gc("backup_template_path"):
        user = gc("backup_template_path")
        if os.path.isdir(base):
            base = user
        else:
            tooltip('Invalid setting for "backup_template_path". This is not a directory. '
                    'Using default path in add-on folder')
    # don't use model['name'] in case a user renames a template ...
    return os.path.join(base, str(self.model['id']), boxname)
CardLayout.template_save_path = template_save_path


def save_clear_editExternal(self, box, tedit):
    self.onTemplateSave(box, tedit)
    content = tedit.toPlainText()
    tedit.setPlainText("")
    if box == "css":
        ext = ".css"
    else:
        ext = ".html"
    suf = "current" + ext
    cur = NamedTemporaryFile(delete=False, suffix=suf)
    cur.write(str.encode(content))
    cur.close()
    cmd = gc("diffcommandstart")
    try:
        subprocess.Popen([cmd[0], cur.name])
    except:
        tooltip("Error while trying to open the external editor. Maybe there's an error in your config.")
        tedit.setPlainText(content)
CardLayout.save_clear_editExternal = save_clear_editExternal


def extra_dialog(self, box, tedit):
    p = self.template_save_path(box)
    if not os.path.isdir(p):
        tooltip("no prior versions found.")
        return
    d = OldVersions(self, self.note, box, p, tedit.toPlainText())
    d.exec()
CardLayout.extra_dialog = extra_dialog


def show_in_filemanager(self, box, tedit):
    p = self.template_save_path(box)
    if os.path.isdir(p):
        openFolder(p)
    else:
        tooltip("folder not found. Maybe no version was saved yet ...")
CardLayout.show_in_filemanager = show_in_filemanager


def saveStringForBox(self, boxname, content):
    if boxname == "css":
        ext = ".css"
    else:
        ext = ".html"
    folder = self.template_save_path(boxname)
    filename = now() + ext
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
    p = os.path.join(folder, filename)
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(content)
        tooltip('saved as {}'.format(filename))
CardLayout.saveStringForBox = saveStringForBox


def onTemplateSave(self, boxname, tedit):
    content = tedit.toPlainText()
    self.saveStringForBox(boxname, content)
CardLayout.onTemplateSave = onTemplateSave


def on_CMdialog_finished(self, status):
    if status:
        # edited_fieldcontent is global var set in MyDialog class.
        # unique string is used so that I find the cursor position in CM. Useless here.
        self.textedit_in_cm.setPlainText(edited_fieldcontent.replace(unique_string, ""))  
CardLayout.on_CMdialog_finished = on_CMdialog_finished


def on_external_edit(self, boxname, textedit):
    self.textedit_in_cm = textedit
    tmpl_content = readfile()
    win_title = 'Anki - edit html source code for field in codemirror'
    js_save_cmd = "editor.getValue()"
    bodyhtml = tmpl_content.format(
        content=textedit.toPlainText(),
        isvim=keymap[1],
        keymap=keymap[0],
        mode="css",
        theme=selectedtheme,
        unique_string=unique_string,
        lint="true"
    )
    d = MyDialog(self, bodyhtml, win_title, js_save_cmd, False, boxname, self.note)
    # exec_() doesn't work - jseditor isn't loaded = blocked
    # finished.connect via https://stackoverflow.com/questions/39638749/
    d.finished.connect(self.on_CMdialog_finished)
    d.setModal(True)
    d.show()
    d.web.setFocus()
CardLayout.on_external_edit = on_external_edit












if pointversion < 27:
    def common_context_menu(self, tedit, box):
        menu = tedit.createStandardContextMenu()
        sla = menu.addAction("edit in extra window with html/css editor")
        sla.triggered.connect(lambda _, s=self: on_external_edit(s, box, tedit))
        sav = menu.addAction("save")
        sav.triggered.connect(lambda _, s=self: onTemplateSave(s, box, tedit))
        a = menu.addAction("prior versions extra dialog")
        a.triggered.connect(lambda _, s=self: extra_dialog(s, box, tedit))
        b = menu.addAction("prior versions in file manager")
        b.triggered.connect(lambda _, s=self: show_in_filemanager(s, box, tedit))
        c = menu.addAction("save, edit external and clear")
        c.triggered.connect(lambda _, s=self: save_clear_editExternal(s, box, tedit))
        return menu
    CardLayout.common_context_menu = common_context_menu


    def make_context_menu_front(self, location):
        menu = self.common_context_menu(self.tform.front, "front")
        menu.exec_(QCursor.pos())
    CardLayout.make_context_menu_front = make_context_menu_front


    def make_context_menu_css(self, location):
        menu = self.common_context_menu(self.tform.css, "css")
        menu.exec_(QCursor.pos())
    CardLayout.make_context_menu_css = make_context_menu_css


    def make_context_menu_back(self, location):
        menu = self.common_context_menu(self.tform.back, "back")
        menu.exec_(QCursor.pos())
    CardLayout.make_context_menu_back = make_context_menu_back


    def additional_clayout_setup(self):
        # https://stackoverflow.com/a/44770024
        self.tform.front.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tform.front.customContextMenuRequested.connect(self.make_context_menu_front)
        self.tform.css.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tform.css.customContextMenuRequested.connect(self.make_context_menu_css)
        self.tform.back.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tform.back.customContextMenuRequested.connect(self.make_context_menu_back)
    CardLayout.setupMainArea = wrap(CardLayout.setupMainArea, additional_clayout_setup)









if pointversion >= 28:
    def make_new_context_menu(self, location):
        if self.tform.front_button.isChecked():
            print('on front')
            box = "front"
        elif self.tform.back_button.isChecked():
            print('on back')
            box = "back"
        else:
            print('in css')
            box = "css"
        tedit = self.tform.edit_area
        menu = tedit.createStandardContextMenu()
        sla = menu.addAction("edit in extra window with html/css editor")
        sla.triggered.connect(lambda _, s=self: on_external_edit(s, box, tedit))
        sav = menu.addAction("save")
        sav.triggered.connect(lambda _, s=self: onTemplateSave(s, box, tedit))
        a = menu.addAction("prior versions extra dialog")
        a.triggered.connect(lambda _, s=self: extra_dialog(s, box, tedit))
        b = menu.addAction("prior versions in file manager")
        b.triggered.connect(lambda _, s=self: show_in_filemanager(s, box, tedit))
        c = menu.addAction("save, edit external and clear")
        c.triggered.connect(lambda _, s=self: save_clear_editExternal(s, box, tedit))
        menu.exec_(QCursor.pos())
    CardLayout.make_new_context_menu = make_new_context_menu


    def additional_clayout_setup(self):
        # https://stackoverflow.com/a/44770024
        self.tform.edit_area.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tform.edit_area.customContextMenuRequested.connect(self.make_new_context_menu)
    CardLayout.setup_edit_area = wrap(CardLayout.setup_edit_area, additional_clayout_setup)

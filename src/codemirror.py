"""
anki-addon: edit html source code for field with codemirror in extrawindow

Copyright (c) 2019 ignd
          (c) 2019 Joseph Lorimer <joseph@lorimer.me>
              https://github.com/luoliyan/anki-misc/blob/master/html-editor-tweaks/__init__.py
              https://ankiweb.net/shared/info/410936778
          (c) 2014 - 2016 Detlev Offenbach
              <detlev@die-offenbachs.de> (the function __execJavaScript)
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


This file incorporates work (i.e. the function postprocess and reindent)
covered by the following copyright and permission notice:
#
# Copyright © 2019 Joseph Lorimer <joseph@lorimer.me>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.



This file make Anki load the js package codemirror, http://codemirror.net/,
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

"""


import os
import bs4
import warnings
import io
import re

from aqt import mw
from aqt.qt import *
from aqt.editor import Editor
from aqt.webview import AnkiWebView
from anki.hooks import addHook, wrap
from aqt.utils import askUser

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
from PyQt5.QtCore import Qt, QMetaObject


def gc(arg, fail=False):
    return mw.addonManager.getConfig(__name__).get(arg, fail)


addon_path = os.path.dirname(__file__)
addonfoldername = os.path.basename(addon_path)
regex = r"(web.*)"
mw.addonManager.setWebExports(__name__, regex)
codemirror_path = "/_addons/%s/web/" % addonfoldername


themes = ["3024-day", "3024-night", "abcdef", "ambiance", "ambiance-mobile",
          "base16-dark", "base16-light", "bespin", "blackboard", "cobalt", "colorforth",
          "darcula", "dracula", "duotone-dark", "duotone-light", "eclipse", "elegant",
          "erlang-dark", "gruvbox-dark", "hopscotch", "icecoder", "idea", "isotope",
          "lesser-dark", "liquibyte", "lucario", "material", "mbo", "mdn-like",
          "midnight", "monokai", "neat", "neo", "night", "oceanic-next", "panda-syntax",
          "paraiso-dark", "paraiso-light", "pastel-on-dark", "railscasts", "rubyblue",
          "seti", "shadowfox", "solarized", "ssms", "the-matrix", "tomorrow-night-bright",
          "tomorrow-night-eighties", "ttcn", "twilight", "vibrant-ink", "xq-dark",
          "xq-light", "yeti", "zenburn"]


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
                 keymappath,
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
                 "codemirror/addon/edit/closebrackets.js",
                 "codemirror/addon/wrap/hardwrap.js",
                 "codemirror/addon/fold/foldcode.js",
                 "codemirror/addon/fold/brace-fold.js",
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


class MyDialog(QDialog):
    def __init__(self, parent, bodyhtml, win_title="", js_save_cmd=""):
        super(MyDialog, self).__init__(parent)
        self.js_save_cmd = js_save_cmd
        self.setWindowTitle(win_title)
        self.resize(gc("default_width", 790), gc("default_height", 1100))
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        self.setLayout(mainLayout)
        self.web = MyWebView(self)
        self.web.title = "html source with codemirror"

        self.web.contextMenuEvent = self.contextMenuEvent
        mainLayout.addWidget(self.web)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        mainLayout.addWidget(self.buttonBox)
        self.buttonBox.accepted.connect(self.onAccept)
        self.buttonBox.rejected.connect(self.onReject)
        QMetaObject.connectSlotsByName(self)
        acceptShortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        acceptShortcut.activated.connect(self.onAccept)

        self.web.stdHtml(bodyhtml, cssfiles, jsfiles)
        # self.web.loadFinished.connect(self.load_finished)
        # self.web.setFocus()

    # def load_finished(self, ok):
    #     pass

    def onAccept(self):
        global edited_fieldcontent
        edited_fieldcontent = self.__execJavaScript(self.js_save_cmd)
        self.accept()

    def onReject(self):
        ok = askUser("Close and discard changes?")
        if ok:
            self.reject()

    def closeEvent(self, event):
        ok = askUser("Close and discard changes?")
        if ok:
            event.accept()
        else:
            event.ignore()

    # via https://riverbankcomputing.com/pipermail/pyqt/2016-May/037449.html
    # https://github.com/pycom/EricShort/blob/master/UI/Previewers/PreviewerHTML.py
    def __execJavaScript(self, script):
        """
        Private function to execute a JavaScript function Synchroneously.
        @param script JavaScript script source to be executed
        @type str
        @return result of the script
        @rtype depending upon script result
        """
        from PyQt5.QtCore import QEventLoop
        loop = QEventLoop()
        resultDict = {"res": None}

        def resultCallback(res, resDict=resultDict):
            if loop and loop.isRunning():
                resDict["res"] = res
                loop.quit()
        self.web.page().runJavaScript(
            script, resultCallback)
        loop.exec_()
        return resultDict["res"]


# overwrite built-in function
# so that also the menu is changed
# def onHtmlEdit(self):
#     field = self.currentField
#     contents = self.note.fields[field]

#     shellfilename = "shell_codemirror.html"
#     win_title = 'Anki - edit html source code for field in codemirror'
#     js_save_cmd = "editor.getValue()"

#     soup = bs4.BeautifulSoup(contents,"html.parser")
#     contents = soup.prettify()
#     path = os.path.dirname(os.path.realpath(__file__))
#     htmlfile = os.path.join(path,shellfilename)
#     with open(htmlfile) as f:
#         h = f.read()
#     html = h % (contents)
#     d = MyDialog(None, self, html, field,win_title,js_save_cmd)
#     d.show()
# Editor.onHtmlEdit = onHtmlEdit
Editor.original_onHtmlEdit = Editor.onHtmlEdit


open_space_open = re.compile('(<[^/>]+>) (<[^/>]+>)')
close_space_close = re.compile('(</[^>]+>) (</)')
open_space_text = re.compile('(<[^/>]+>) ([^<>]+)')
open_text_close = re.compile('(<[^/>]+>) ([^<>]+) (</)')
tag_space_punc = re.compile('(>) ([.,:;])')


def postprocess(s):
    """Collapse pretty printed HTML, keeping somewhat sensible white space.

    Beautiful Soup replaces any spacing around tags with newlines and
    indentation. A naive function that attempts to reverse this by
    collapsing the newlines and indentation into a single white space
    will leave spurious spaces around tags. On the other hand, some of
    this white space is essential both semantically and for readability.
    We attempt to reach a sane compromise via these transformations:

    - <span> text </span> => <span>text</span>
    - <span> text         => <span>text
    - <span> <span>       => <span><span>
    - </span> </span>     => </span></span>
    - <span> ,            => <span>,
    - </span> ,           => </span>,
    """
    s = re.sub('\n', ' ', s)
    s = re.sub('[ ]+', ' ', s)
    new = s
    while True:
        new = open_text_close.sub('\\1\\2\\3', new)
        new = open_space_text.sub('\\1\\2', new)
        new = open_space_open.sub('\\1\\2', new)
        new = close_space_close.sub('\\1\\2', new)
        new = tag_space_punc.sub('\\1\\2', new)
        if new == s:
            break
        s = new
    return s


def compact(html):
    return postprocess(html)


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


def _onCMUpdateField(self):
    try:
        note = mw.col.getNote(self.nid)
    except:   # new note
        self.note.fields[self.myfield] = compact(edited_fieldcontent)
        self.note.flush()
    else:
        note.fields[self.myfield] = compact(edited_fieldcontent)
        note.flush()
        mw.requireReset()
        mw.reset()
    self.loadNote(focusTo=self.myfield)
Editor._onCMUpdateField = _onCMUpdateField


def on_CMdialog_finished(self, status):
    if status:
        self.saveNow(lambda: self._onCMUpdateField())
Editor.on_CMdialog_finished = on_CMdialog_finished


def readfile():
    addondir = os.path.join(os.path.dirname(__file__))
    templatefile = "codemirror.html"
    filefullpath = os.path.join(addondir, templatefile)
    with io.open(filefullpath, 'r', encoding='utf-8') as f:
        return f.read()


def cm_start_dialog(self, field):
    tmpl_content = readfile()
    win_title = 'Anki - edit html source code for field in codemirror'
    js_save_cmd = "editor.getValue()"
    pretty_content = prettify(self.note.fields[field])
    bodyhtml = tmpl_content % (pretty_content, keymap[1], keymap[0], selectedtheme)
    d = MyDialog(None, bodyhtml, win_title, js_save_cmd)
    # exec_() doesn't work - jseditor isn't loaded = blocked
    # finished.connect via https://stackoverflow.com/questions/39638749/
    d.finished.connect(self.on_CMdialog_finished)
    d.setModal(True)
    d.show()
    d.web.setFocus()
Editor.cm_start_dialog = cm_start_dialog


def mirror_start(self):
    self.myfield = self.currentField
    self.saveNow(lambda: self.cm_start_dialog(self.myfield))
Editor.mirror_start = mirror_start


# WITH EXTRA BUTTON
#
# def keystr(k):
#     key = QKeySequence(k)
#     return key.toString(QKeySequence.NativeText)

# hotkey = "Ctrl+Shift+Y"
# def setupEditorButtonsFilter(buttons, editor):
#     b = editor.addButton(
#         icon=None, # os.path.join(addon_path, "icons", "tm.png")
#         cmd="CM",
#         func=mirror_start,
#         tip="edit current field in external window ({})".format(keystr(hotkey)),
#         keys=hotkey)
#     buttons.append(b)
#     return buttons
# addHook("setupEditorButtons", setupEditorButtonsFilter)


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
Editor.setupShortcuts = wrap(Editor.setupShortcuts, mySetupShortcuts)

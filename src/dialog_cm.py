import json
import os

from aqt import mw
from aqt.qt import (
    QDialog,
    QKeySequence,
    QSizePolicy,
    QShortcut,
    pyqtSlot,
    qtmajor,
)
from anki.utils import (
    pointVersion,
)
from aqt.utils import (
    askUser,
    restoreGeom,
    saveGeom,
    tooltip,
)
from aqt.webview import AnkiWebView

from .config import codemirror_path, gc, unique_string
from .dialog_old_versions import OldVersions
if qtmajor == 5:
    from .forms5 import edit_window
else:
    from .forms6 import edit_window    
from .helpers import now, readfile
from .sync_execJavaScript import sync_execJavaScript


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
                  themepath,
                  "codemirror/addon/display/fullscreen.css",
                  "webview_override.css",
                  ]
other_cssfiles = []
cssfiles = addon_cssfiles + other_cssfiles

addon_jsfiles = ["codemirror/lib/codemirror.js",
                 "htmlhint.js",
                #  JS error /_addons/1043915942/web/csslint.js:7719 Uncaught TypeError: Cannot create property 'errors' on string 'true' 
                #  "csslint.js",
                # adding these files also doesn't help
                #  "csslint-node.js",
                #  "csslint-rhino.js",
                #  "csslint-tests.js",
                #  "csslint-worker.js",
                #  "csslint-wsh.js",
                 "beautify.js",
                 "beautify-css.js",
                 "beautify-html.js",
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


def handle_esc_in_vim(webview_inst):
    pass
    # print('in handle_esc_in_vim')
    # https://codemirror.net/doc/manual.html#vimapi
    # As with the configuration API, the methods are exposed on CodeMirror.Vim and may be 
    # called at any time.
    # exitVisualMode(cm: CodeMirror, ?moveHead: boolean)
    #   Exit visual mode. If moveHead is set to false, the CodeMirror selection will not be 
    #   touched. The caller assumes the responsibility of putting the cursor in the right place. 
    # TODO
    # js = ""
    # webview_inst.page().runJavaScript(js)


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

    def onEsc(self):
        if gc("keymap") == "vim":
            handle_esc_in_vim(self)
        else:
            AnkiWebView.onEsc(self)


class CmDialogBase(QDialog):
    def __init__(self, parent, content, mode, win_title):
        super(CmDialogBase, self).__init__(parent)
        if pointVersion() <45:
            mw.setupDialogGC(self)
        else:
            mw.garbage_collect_on_dialog_finish(self)
        self.parent = parent
        self.js_save_cmd = "editor.getValue()"
        self.setWindowTitle(win_title)
        self.dialog = edit_window.Ui_Dialog()
        self.dialog.setupUi(self)
        self.dialog.outer.setContentsMargins(0, 0, 0, 0)
        self.dialog.outer.setSpacing(0)
        self.web = MyWebView(self.parent)
        self.dialog.outer.addWidget(self.web)
        qsp = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        qsp.setVerticalStretch(2)
        self.web.setSizePolicy(qsp)
        acceptShortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        acceptShortcut.activated.connect(self.accept)
        self.web.title = "html source with codemirror"
        self.web.contextMenuEvent = self.contextMenuEvent
        tmpl_content = readfile("codemirror.html")
        # the following seems to break cm so I just remove it <!--StartFragment--><!--EndFragment-->
        self.content = content.replace("<!--StartFragment-->", "").replace("<!--EndFragment-->","")
        bodyhtml = tmpl_content.format(
            autoformat_function="html_beautify" if mode == "htmlmixed" else "css_beautify",
            content="",
            font_family=gc("font-family", "monospace"),
            font_size=gc("font-size", "15px"),
            isvim=keymap[1],
            keymap=keymap[0],
            mode=mode,
            theme=selectedtheme,
            unique_string=unique_string,
            lint="true",
        )
        self.web.stdHtml(bodyhtml, cssfiles, jsfiles)
        restoreGeom(self, "1043915942_CmDialog")
        self.web.loadFinished.connect(self.load_finished)
        # https://stackoverflow.com/questions/56890831/qwidget-cannot-catch-escape-backspace-or-c-x-key-press-events#56895453
        # Answer by user "eyllanesc", CC BY-SA 4.0
        #    Events do not necessarily propagate among all widgets, if a widget consumes it 
        #    then it will no longer propagate to the parent. In the case of the keyboard 
        #    events will only be consumed first by the widget that has the focus, in your case 
        #    QWebEngineView consumes them before and prevents it from being projected in 
        #    other widgets. If you want to hear events from the keyboard of a window then 
        #    you must use the QShortcuts, and for that you must create a QShortcut
        #
        #
        # also see anki commit message for 34dcf64d760d01d3f3e4f7aa4a6738b725e53afa
        #     another attempt at fixing key handling
        #    
        #     we can't use an event filter on the top level webview, because it
        #     ignores the return value of the filter and leads to Anki thinking
        #     keys have been pressed twice
        #    
        #     and if we use an event filter on the focusProxy(), the
        #     keypress/release events are sent even when a text field is currently
        #     focused, leading to shortcuts being triggered when typing in the answer
        #    
        #     to solve this, we move away from handling the key press events
        #     directly, and instead install shortcuts for the events we want to
        #     trigger. in addition to the global shortcuts, each state can install
        #     its own shortcuts, which we remove when transitioning to a new state
        #    
        #     also remove the unused canFocus argument to ankiwebview, and accept a parent
        #     argument as required by the code in forms/
        #
        # NOTE the following deactivates Esc in the dialog but only calls
        # on_Escape if the webview is not focused. With the following line
        # onEsc from webview.py isn't activated when I press Esc and have the webview 
        # focused.
        # QShortcut(QKeySequence("Escape"), self, activated=self.on_Escape)

    # @pyqtSlot()
    # def on_Escape(self):
    #     print("outer_Escape")
    #     if gc("keymap") == "vim":
    #         handle_esc_in_vim(self.web)
    #     else:
    #         self.reject()

    def load_finished(self):
        js = f'editor.setValue({json.dumps(self.content)}); moveCursor();'
        self.web.page().runJavaScript(js)

    def accept(self):
        # replace cursor with unique string
        s = """insertTextAtCursor('%s')""" % unique_string
        self.execJavaScript(s)
        mw.col.cmhelper_field_content = self.execJavaScript(self.js_save_cmd)
        saveGeom(self, "1043915942_CmDialog")
        self.web = None
        QDialog.accept(self)

    def reject(self):
        ok = askUser("Close and discard changes?")
        if ok:
            saveGeom(self, "1043915942_CmDialog")
            self.web = None
            QDialog.reject(self)

    def closeEvent(self, event):
        ok = askUser("Close and discard changes?")
        if ok:
            event.ignore()
            saveGeom(self, "1043915942_CmDialog")
            self.web = None
            QDialog.reject(self)
        else:
            event.ignore()

    def execJavaScript(self, script):
        return sync_execJavaScript(self.web, script)


class CmDialogField(CmDialogBase):
    def __init__(self, parent, content, mode, win_title):
        super(CmDialogField, self).__init__(parent, content, mode, win_title)
        self.dialog.wid_buts.setVisible(False)


# TODO process/remove comments
class CmDialogForTemplate(CmDialogBase):
    def __init__(self, parent, content, mode, win_title, boxname, note):
        super(CmDialogForTemplate, self).__init__(parent, content, mode, win_title)
        self.boxname = boxname
        self.note = note
        self.dialog.pb_save.clicked.connect(self.onTemplateSave)
        self.dialog.pb_viewold.clicked.connect(self.onView)

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
        content = self.execJavaScript(self.js_save_cmd)
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
        currContent = self.execJavaScript(self.js_save_cmd)
        folder = self.parent.template_save_path(self.boxname)
        if not os.path.isdir(folder):
            tooltip("no prior versions found")
            return
        d = OldVersions(self, self.note, self.boxname, folder, currContent)
        if d.exec():
            pass

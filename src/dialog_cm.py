import json
import os

# aqt imports
from aqt import mw
from aqt.qt import (
    QCursor,
    QDialog,
    QDialogButtonBox,
    QKeySequence,
    QMenu,
    QSizePolicy,
    QShortcut,
    pyqtSlot,  # Not used, consider removing if truly unused elsewhere
    qtmajor,
)
from aqt.utils import (
    askUser,
    restoreGeom,
    saveGeom,
    tooltip,
)
from aqt.webview import AnkiWebView
try:
    # new API in Anki ≥ 2.1.49
    from aqt.theme import theme_manager
except ImportError:
    # pre-2.1.49 fallback
    theme_manager = None

# Third-party imports (None in this section currently)

# Own module imports
from .anki_version_detection import anki_point_version
from .config import addon_path, codemirror_path, gc, unique_string
from .dialog_old_versions import OldVersions
if qtmajor == 5:
    from .forms5 import edit_window
else:
    from .forms6 import edit_window
from .helpers import now, read_file # now is not used, consider removing
from .sync_execJavaScript import sync_execJavaScript
from .dialog_text_display import Text_Displayer


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


def dark_mode_active() -> bool:
    try:
        # Anki ≥2.1.49
        # theme_manager is already imported at the top with a try-except
        if theme_manager:
            return bool(theme_manager.night_mode)
        # Fall through to pre-2.1.49 if theme_manager is None (failed import)
    except AttributeError: # Handles cases where theme_manager might exist but not night_mode
        pass # Fall through to pre-2.1.49 logic

    # pre-2.1.49
    try:
        val = mw.pm.night_mode
        return bool(val() if callable(val) else val)
    except Exception:
        return False


def selected_theme() -> str:
    night = dark_mode_active()
    key = 'theme night mode' if night else 'theme'
    default_theme_name = 'dracula' if night else 'neat' # Python-defined default

    val_from_config = gc(key) # gc returns the value or False (its default for `fail`)

    # Use value from config if it's a valid theme string, otherwise use Python-defined default
    return val_from_config if isinstance(val_from_config, str) and val_from_config in themes else default_theme_name


def theme_path():
    return "codemirror/theme/" + selected_theme() + ".css"


def keymap():
    default_keymap_val = "sublime"
    uk_from_gc = gc('keymap')  # Get value or False
    # Apply default if gc returned False or not a string
    current_keymap = uk_from_gc if isinstance(uk_from_gc, str) and uk_from_gc else default_keymap_val
    uk = current_keymap.lower()
    if uk in ["sublime", "emacs", "vim"]:
        if uk == 'vim':
            km_setting = [uk, "true"]
        else:
            km_setting = [uk, "false"]
    else:
        km_setting = ["sublime", "false"] # Default if uk is not one of the recognized keymaps
    return km_setting


def key_map_path():
    return "codemirror/keymap/" + keymap()[0] + ".js"


def css_files():
    return       ["codemirror/lib/codemirror.css",
                  "codemirror/addon/lint/lint.css",
                  "codemirror/addon/hint/show-hint.css",
                  "codemirror/addon/dialog/dialog.css",
                  "codemirror/addon/search/matchesonscrollbar.css",
                  theme_path(),
                  "codemirror/addon/display/fullscreen.css",
                  "webview_override.css",
                  ]



def get_addon_jsfiles():
    return      ["codemirror/lib/codemirror.js",
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
                 key_map_path(),
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


def return_all_js_files():
    return get_addon_jsfiles() + ["jquery.js", ]


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
        if fname in get_addon_jsfiles():
            return '<script src="%s"></script>' % (codemirror_path + fname)
        else:
            return '<script src="%s"></script>' % self.webBundlePath(fname)

    def bundledCSS(self, fname):
        if fname in css_files():
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
        if anki_point_version < 45:
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
        self.dialog.buttonBox.button(QDialogButtonBox.StandardButton.Help).setText('More')
        self.dialog.buttonBox.button(QDialogButtonBox.StandardButton.Help).clicked.connect(self.on_more)
        self.web.title = "html source with codemirror"
        self.web.contextMenuEvent = self.contextMenuEvent
        tmpl_content = read_file("codemirror.html")
        # the following seems to break cm so I just remove it <!--StartFragment--><!--EndFragment-->
        self.content = content.replace("<!--StartFragment-->", "").replace("<!--EndFragment-->","")

        default_font_family_val = "monospace"
        font_family_from_gc = gc("font-family")
        current_font_family = font_family_from_gc if isinstance(font_family_from_gc, str) and font_family_from_gc else default_font_family_val

        default_font_size_val = "15px"
        font_size_from_gc = gc("font-size")
        current_font_size = font_size_from_gc if isinstance(font_size_from_gc, str) and font_size_from_gc else default_font_size_val

        bodyhtml = tmpl_content.format(
            autoformat_function="html_beautify" if mode == "htmlmixed" else "css_beautify",
            content="",
            font_family=current_font_family,
            font_size=current_font_size,
            isvim=keymap()[1],
            keymap=keymap()[0],
            mode=mode,
            theme=selected_theme(),
            unique_string=unique_string,
            lint="true",
        )
        self.web.stdHtml(bodyhtml, css_files(), return_all_js_files())
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

    def on_more(self):
        m = QMenu(self)
        a = m.addAction("about this add-on")
        a.triggered.connect(self.on_about)
        a = m.addAction("Save/Backup")
        a.triggered.connect(self.on_save)
        a = m.addAction("Restore/Import")
        a.triggered.connect(self.on_import)
        a = m.addAction("Send to external")
        a.triggered.connect(self.on_send_to_external)
        m.exec(QCursor.pos())

    def on_save(self):
        tooltip('not implemented yet')

    def on_import(self):
        tooltip('not implemented yet')

    def on_send_to_external(self):
        tooltip('not implemented yet')

    def on_about(self):
        license_file_path = addon_path + "/license.txt"
        try:
            with open(license_file_path) as f:
                text = f.read()
        except FileNotFoundError:
            text = "License file not found."
        help_text = """
If you have problems with this add-on:
1. Read [this Anki FAQ](https://faqs.ankiweb.net/when-problems-occur.html)
2. Disable all other add-ons, then restart Anki and then try again. If this solves your problem you have an add-on conflict and must decide which add-on is more important for you.
3. If you still have problems, reset the config of this add-on and restart Anki and try again.
4. If it still doesn't work you report the problem at https://forums.ankiweb.net/t/extended-html-editor-for-fields-and-card-templates-with-some-versioning-official-support-thread/967 and describe the exact steps needed to reproduce the problem.

Anki changes with each update and sometimes this breaks add-ons or changes how they work. So if an add-on no longer works as expected after an add-on: Make sure to have the latest version by manually  checking for add-on updates. Then also have a look at the add-on listing on ankiweb, e.g. https://ankiweb.net/shared/info/1043915942 for this add-on. On these pages add-on creators often  list changes for their add-ons.






"""
        td = Text_Displayer(
            parent=self,
            text=help_text + text,
            windowtitle="about the add-on extended html editor ...",
            dialogname_for_restore="about_cm_dialog",
            )
        td.show()

    def load_finished(self):
        if self.web:
            js = f'editor.setValue({json.dumps(self.content)}); moveCursor();'
            self.web.page().runJavaScript(js)

    def accept(self):
        # replace cursor with unique string
        # the following code crashes Anki 2.1.54/qt6 on MacOS, see #6
        # s = """insertTextAtCursor('%s')""" % unique_string
        # self.execJavaScript(s)
        if self.web:
            mw.col.cmhelper_field_content = self.execJavaScript(self.js_save_cmd)
        saveGeom(self, "1043915942_CmDialog")
        if self.web:
            self.web.cleanup()
        QDialog.accept(self)
        self.web = None

    def reject(self):
        ok = askUser("Close and discard changes?")
        if ok:
            saveGeom(self, "1043915942_CmDialog")
            if self.web:
                self.web.cleanup()
            QDialog.reject(self)
            self.web = None

    def closeEvent(self, event):
        ok = askUser("Close and discard changes?")
        if ok:
            event.ignore()
            saveGeom(self, "1043915942_CmDialog")
            if self.web:
                self.web.cleanup()
            QDialog.reject(self)
            self.web = None
        else:
            event.ignore()

    def execJavaScript(self, script):
        if self.web:
            return sync_execJavaScript(self.web, script)
        return None


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
        self.dialog.pb_save.clicked.connect(self.on_template_save)
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

    def on_template_save(self):
        content = self.execJavaScript(self.js_save_cmd)
        self.parent.save_string_for_box(self.boxname, content)
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
        curr_content = self.execJavaScript(self.js_save_cmd)
        folder = self.parent.template_save_path(self.boxname)
        if not os.path.isdir(folder):
            tooltip("no prior versions found")
            return
        d = OldVersions(self, self.note, self.boxname, folder, curr_content)
        if d.exec():
            pass

# for license info see lixense.txt in this folder

from typing import Optional # Added for type hinting
from aqt import gui_hooks
from aqt import mw
from aqt.qt import *  # This imports QApplication, QClipboard, QEvent, etc.
from aqt.qt import qtmajor

from . import editor
from . import clayout_adjust

# Import for new features
from .options_dialog import show_config_dialog
from .config import gc # To read the "copyHtmlOnShortcut" preference

from PyQt6.QtCore import QObject, QEvent, Qt as Qt_core, QTimer, QMimeData # Renamed to avoid conflict with wildcard import; Added QTimer and QMimeData
from PyQt6.QtGui import QKeySequence
from aqt.webview import AnkiWebView, AnkiWebViewKind # Ensure AnkiWebViewKind is imported
from aqt.editor import EditorState # Ensure EditorState is imported

# Import CmDialogField
from .dialog_cm import CmDialogField


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
    # Pass __name__ (which is the add-on's package name like "1900436383")
    # to the dialog so it can correctly interact with addonManager for this addon.
    show_config_dialog(__name__)

mw.addonManager.setConfigAction(__name__, on_addon_config_requested)


# --- Global HTML Copy Event Filter ---
class GlobalHtmlCopyFilter(QObject):
    def eventFilter(self, _obj, ev):
        if not (gc("copyHtmlOnShortcut", False) or gc("copyPlainOnShortcut", False)):
            return False # nothing enabled → let macOS/Anki handle Copy
        if ev.type() != QEvent.Type.KeyPress:
            return False
        if not ev.matches(QKeySequence.StandardKey.Copy):
            return False

        w = mw.app.focusWidget()
        while w and not isinstance(w, AnkiWebView):
            w = w.parent()
        if (not isinstance(w, AnkiWebView)
                or w.kind != AnkiWebViewKind.EDITOR
                or (getattr(w, "editor", None)
                    and w.editor.state != EditorState.FIELDS)):
            # fall back → let Qt handle the copy immediately
            return False

        # Try fast path: grab HTML directly if available and not empty
        if hasattr(w, "selectedHtml"):
            selected_html = w.selectedHtml().strip() # Added .strip()
            if selected_html and gc("copyHtmlOnShortcut", False) and not gc("copyPlainOnShortcut", False):
                cb = QApplication.clipboard()
                data = QMimeData()
                data.setText(selected_html) # Set as plain text
                data.setHtml(selected_html) # Set as HTML
                cb.setMimeData(data, QClipboard.Mode.Clipboard)
                return True # Handled

        # Fallback to JS method if selectedHtml is not available or empty
        plain = w.selectedText().strip() # Added .strip()
        if not plain:          # nothing selected -> default copy
            return False       # let Qt handle empty selection

        # full JS that unwraps helpers **and** reconstructs <anki-mathjax>
        js_get_selection_data = r"""
          (function () {
            let sel = (document.activeElement?.shadowRoot
                       ? document.activeElement.shadowRoot.getSelection()
                       : (document.activeElement?.getSelection
                          ? document.activeElement.getSelection()
                          : window.getSelection()));
            if (!sel || !sel.rangeCount) { return { html: "", text: "" }; }

            const c = document.createElement("div");
            c.append(sel.getRangeAt(0).cloneContents());

            // Store HTML before modification for plain text
            const html_content = c.innerHTML;

            c.querySelectorAll('anki-frame,frame-start,frame-end')
              .forEach(n => n.replaceWith(...n.childNodes));
            c.querySelectorAll('[data-frames]').forEach(n => n.removeAttribute('data-frames'));

            c.querySelectorAll('anki-mathjax').forEach(el => {
              let tex = el.getAttribute('data-mathjax');
              if (!tex && window.MathJax?.Hub?.getJaxFor) {
                const jax = MathJax.Hub.getJaxFor(el);
                tex = jax?.originalText;
              }
              tex = tex || el.textContent;
              const clean = document.createElement('anki-mathjax');
              clean.textContent = tex;
              el.replaceWith(clean); // For HTML output
            });

            const final_html = c.innerHTML; // HTML after anki-mathjax processing

            // Define isDisplayContext function (as provided in user prompt)
            function isDisplayContext(el) {
              // TODO: Implement display context detection logic
              /*
              // if they gave us a text node, use its parent
              if (el.nodeType === Node.TEXT_NODE) el = el.parentElement;
              const parent = el.parentElement;

              // 1. block: parent contains *only* this formula (ignoring whitespace)
              const parentText = parent.textContent.trim();
              const formulaText = el.textContent.trim();
              if (parentText === formulaText) {
                console.warn("isDisplayContext: parent contains only this formula");
                return false; // Should be true for block, but per user request, returning false
              }

              // 2. <br> immediately before or after (check any sibling, text or element)
              const prev = el.previousSibling;
              const next = el.nextSibling;
              if ((prev && prev.nodeName === "BR") || (next && next.nodeName === "BR")) {
                console.warn("isDisplayContext: <br> immediately before or after");
                return true;
              }
              */
              // otherwise inline
              return false;
            }

            // For plain text: re-parse original fragment and extract text from MathJax
            const text_c = document.createElement("div");
            text_c.innerHTML = html_content; // Use original HTML to avoid processing anki-mathjax twice for text
            text_c.querySelectorAll('anki-mathjax').forEach(el=>{
             let tex = el.getAttribute('data-mathjax')||el.textContent;
             // Use isDisplayContext to choose delimiters
             let wrappedTex;
             if (isDisplayContext(el)) {
               wrappedTex = '\\[' + tex + '\\]';
             } else {
               wrappedTex = '\\(' + tex + '\\)';
             }
             el.replaceWith(document.createTextNode(wrappedTex));
            });

            return {
              html: final_html,
              text: text_c.innerText.replace(/\u00A0/g,' ').trim()
            };
          })();
        """

        cb = QApplication.clipboard()
        done_flag = {"done": False}    # mutable flag captured by the lambdas

        def publish(payload):
            if done_flag["done"]:
                return
            done_flag["done"] = True

            html = payload.get("html") if isinstance(payload, dict) else None
            plain_tex = payload.get("text") if isinstance(payload, dict) else None

            want_plain = gc("copyPlainOnShortcut", False)
            want_html  = gc("copyHtmlOnShortcut", False) # Added to check if HTML copy is desired
            mime = QMimeData()

            if want_plain:
                # strip all tags, keep MathJax’ TeX
                # The JS already provides cleaned text in plain_tex
                text_out = plain_tex or plain # Fallback to original plain if JS failed
                if text_out: # Ensure text_out is not None or empty before wrapping
                    mime.setText(text_out) # JS will now handle $ wrapping
                else:
                    mime.setText("") # Set empty string if text_out is empty or None
            elif want_html: # Elif to give plain priority
                src = html or plain
                mime.setText(src)
                mime.setHtml(src)
            else:
                return # neither wanted - do nothing (should be caught by the eventFilter's initial check)


            QApplication.clipboard().setMimeData(mime, QClipboard.Mode.Clipboard)

        # ① ask the page for cleaned-up HTML
        w.page().runJavaScript(js_get_selection_data, publish)

        # ② safety-net: after 150 ms publish plain text if JS never replied
        QTimer.singleShot(150, lambda: publish(None))

        return True   # we already handled copy


# Install the event filter instance on application load
# Ensure it's only installed once
if not hasattr(mw, "_global_html_copy_filter_instance_1900436383"): # Unique attribute name
    # Parent the filter to mw to manage its lifetime with Anki's main window
    filter_instance = GlobalHtmlCopyFilter(mw)
    mw.app.installEventFilter(filter_instance)
    setattr(mw, "_global_html_copy_filter_instance_1900436383", filter_instance)

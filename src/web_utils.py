import os, textwrap

# load the file once at import-time
_JS_SOURCE = None
def _js_source():
    global _JS_SOURCE
    if _JS_SOURCE is None:
        here = os.path.dirname(__file__)
        with open(os.path.join(here, "web", "selection_utils.js"),
                  encoding="utf-8") as f:
            _JS_SOURCE = f.read()
    return _JS_SOURCE

def call_get_selection(webview, py_callback):
    """
    Inject selection_utils.js into the *current* page (only the first time)
    and immediately call ankiGetSelectionData(); pass the result to py_callback.
    """
    script = textwrap.dedent(f"""
        (function () {{
          if (!window.__ankiSelectionLoaded) {{
            {_js_source()}
            window.__ankiSelectionLoaded = true;
          }}
          return ankiGetSelectionData();
        }})();
    """)
    webview.page().runJavaScript(script, py_callback)

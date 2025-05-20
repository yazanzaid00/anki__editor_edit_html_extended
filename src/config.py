import os
from aqt import mw
from anki import version as anki_version


def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    return fail


addon_path = os.path.dirname(__file__)
addonfoldername = os.path.basename(addon_path)
codemirror_path = "/_addons/%s/web/" % addonfoldername


# unique_string = '<span style="display:none">äöüäöü</span>'
unique_string = '2508ee56881b40e8a221feaf3605105e'  # random uuid, Umlaute break with json.dumps


regex = r"(web[/\\].*)"
mw.addonManager.setWebExports(__name__, regex)


DEFAULTS = {
    "hotkey_codemirror": "Ctrl+Shift+Y",
    "anki_editor_add_button": True,
    # Default for codemirror theme, matching the default in the cm settings dialog
    "theme": "default",
    "mini": False,  # minify html code after editing in codemirror
    "format": True,  # format html code before editing in codemirror
    "FontSize": 18,
    "addonInfo_removals_version": "0.0.0",  # last version that removed an addon from addonInfo
    "copyHtmlOnShortcut": False, # Added new preference
    "copyShortcut": "Ctrl+Shift+H",   # macOS will display this as ⌘⇧H automatically
}


# stores configuration values
class Config:
    pass

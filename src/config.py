import os
from aqt import mw
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
codemirror_path = "/_addons/%s/web/" % addonfoldername


# unique_string = '<span style="display:none">äöüäöü</span>'
unique_string = '2508ee56881b40e8a221feaf3605105e'  # random uuid, Umlaute break with json.dumps


regex = r"(web[/\\].*)"
mw.addonManager.setWebExports(__name__, regex)

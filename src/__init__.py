# for license info see lixense.txt in this folder

from aqt import gui_hooks
from aqt import mw

from . import editor
from . import clayout_adjust


def onLoadHere():
    mw.col.cmhelper_field_content = None
gui_hooks.profile_did_open.append(onLoadHere)

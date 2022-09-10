# for license info see lixense.txt in this folder

from aqt import gui_hooks
from aqt import mw

from . import editor
from . import clayout_adjust


def run_after_profile_did_open():
    mw.col.cmhelper_field_content = None
gui_hooks.profile_did_open.append(run_after_profile_did_open)

# This is a part of the file "edit_external.py" from External Editor

import sys

from .config import gc
from .utils import is_executable, find_executable


def get_editor():
    user_choice = gc("editor")
    if is_executable(user_choice):
        return user_choice
    editors = [
        user_choice,
        user_choice + ".exe",
        "notepad++.exe",
        "notepad.exe",
        "code --wait",
        "gvim -f",
        "vim -gf",
        "atom",
        "atom.exe",
        "gedit",
    ]
    if sys.platform == "darwin":
        editors.append("open -t")
    for editor in editors:
        command = find_executable(editor)
        if command:
            return command

    raise RuntimeError("Could not find external editor")

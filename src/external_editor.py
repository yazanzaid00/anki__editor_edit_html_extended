from distutils.spawn import find_executable
import shutil
import subprocess
import io
import os
import sys
import tempfile

from anki.utils import isLin
from aqt.utils import tooltip

from .config import gc


def get_editor(block):

    user_choice = gc("editor")
    params = gc("editor parameters")

    if os.path.isfile(user_choice) and os.access(user_choice, os.X_OK):
        return " ".join([user_choice] + params)
    editors = [
        [user_choice, params],
        ["notepad++.exe", []],
        ["notepad.exe", []],
        ["gvim", ["-f"]],
        ["vim", ["-gf"]],
        ["atom", []],
        ["atom.exe", []],
        ["gedit", []],
    ]
    for command, params in editors:
        executable = shutil.which(command)
        # find_executable from original add-on doesn't find my VSCode on
        # Windows but shutil.which does. To avoid other problems I still
        # run the old code if the new one doesn't help.
        if not executable:
            executable = find_executable(command)
        if executable:
            return " ".join([executable] + params)
    if sys.platform == "darwin":
        return "open -t"
    raise RuntimeError("Could not find external editor")


def edit_string_externally_and_return_mod(text, filename=None, block=True, suffix=".html"):
    editor = get_editor(block)
    if not editor:
        tooltip('no editor found.')
        return
    if not filename:
        filename = tempfile.mktemp(suffix=suffix)

    with io.open(filename, 'w', encoding='utf-8') as file:
        file.write(text)

    cmd_list = editor.split() + [filename]

    env = os.environ.copy()
    if isLin:
        toremove = ['LD_LIBRARY_PATH', 'QT_PLUGIN_PATH', 'QML2_IMPORT_PATH']
        for e in toremove:
            env.pop(e, None)
    try:
        proc = subprocess.Popen(cmd_list, close_fds=True, env=env)
    except:
        raise RuntimeError
    else:
        if block:
            proc.communicate()
            with io.open(filename, 'r', encoding='utf-8') as file:
                return file.read()

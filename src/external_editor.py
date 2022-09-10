from distutils.spawn import find_executable
import shutil
import subprocess
import io
import os
import sys
import tempfile

from .anki_version_detection import anki_point_version
if anki_point_version <= 49:
    from anki.utils import isMac
else:
    from anki.utils import is_mac as isMac

from aqt.utils import (
    tooltip,
)

from .config import gc
from .get_text_editor import get_editor


def save_text_to_file(text, boxname, filename=False):
    if boxname == "css":
        ext = ".css"
    else:
        ext = ".html"

    if not filename:
        # https://stackoverflow.com/questions/3924117/how-to-use-tempfile-namedtemporaryfile-in-python
        t = tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix="current"+ext, encoding='utf-8')
        filename = t.name
    else:
        t = io.open(filename, 'w', encoding='utf-8')
    with t as temp:
        temp.write(text)
        # temp.flush()
    return filename


def env_adjust():
    env = os.environ.copy()
    toremove = ['LD_LIBRARY_PATH', 'QT_PLUGIN_PATH', 'QML2_IMPORT_PATH']
    for e in toremove:
        env.pop(e, None)
    return env


def open_external_editor(cmd_list):
    try:
        proc = subprocess.Popen(cmd_list, env=env_adjust())
    except:
        tooltip("Error while trying to open the external editor. Maybe there's an error in your config.")
        return None
    else:
        return proc


def edit_string_externally_and_return_mod(self, text, filename=None, block=True, boxname="css"):
    filename = save_text_to_file(text, boxname, filename=False)

    editor = get_editor()
    if not editor:
        tooltip('no editor found.')
        return
    cmd_list = editor.split() + [filename]

    proc = open_external_editor(cmd_list)
    if proc and block:
        # in MacOS 10.12 the blocked Anki window was on top and I couldn't raise geany on top of it
        # But this setVisible approach doesn't work.
        # if isMac:
        #     self.setVisible(False)
        proc.communicate()
        with io.open(filename, 'r', encoding='utf-8') as file:
            return file.read()
        # if isMac:
        #     self.setVisible(True)

def diff_text_with_other_file_in_external(text, boxname, otherfile):
    filename = save_text_to_file(text, boxname, filename=False)

    cmd_list = gc("external: command to diff versions").split() + [filename, otherfile]
    command = find_executable(cmd_list[0])
    if not command:
        tooltip("Error while trying to open the external editor. Maybe there's an error in your config.")
        return

    open_external_editor(cmd_list)

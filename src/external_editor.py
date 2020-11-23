from distutils.spawn import find_executable
import shutil
import subprocess
import io
import os
import sys
import tempfile

from anki.utils import (
    isLin,
    noBundledLibs,
)
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
        t = tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix="current"+ext)
        filename = t.name
    else:
        t = io.open(filename, 'w', encoding='utf-8')
    with t as temp:
        temp.write(text)
        # temp.flush()
    return filename


def open_external_editor(cmd_list, args):
    try:
        with noBundledLibs():
            proc = subprocess.Popen(cmd_list, **args)
    except:
        tooltip("Error while trying to open the external editor. Maybe there's an error in your config.")
        return None
    else:
        return proc


def edit_string_externally_and_return_mod(text, filename=None, block=True, boxname="css"):
    filename = save_text_to_file(text, boxname, filename=False)

    editor = get_editor()
    if not editor:
        tooltip('no editor found.')
        return
    cmd_list = editor.split() + [filename]

    proc = open_external_editor(cmd_list, {})
    if proc and block:
        proc.communicate()
        with io.open(filename, 'r', encoding='utf-8') as file:
            return file.read()


def diff_text_with_other_file_in_external(text, boxname, otherfile):
    filename = save_text_to_file(text, boxname, filename=False)

    cmd_list = gc("diffcommandstart")
    if not isinstance(cmd_list, list):
        tooltip("Invalid settings for 'diffcommandstart'. Must be a list. Aborting ...")
        return
    cmd_list.extend([filename, otherfile])
    
    open_external_editor(cmd_list, {})

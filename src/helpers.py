import io
import os


def readfile(filename):
    addondir = os.path.join(os.path.dirname(__file__))
    templatefile = filename
    filefullpath = os.path.join(addondir, templatefile)
    with io.open(filefullpath, "r", encoding="utf-8") as f:
        return f.read()

import io
from tempfile import NamedTemporaryFile
import os
import subprocess

from aqt import (
    QDialog,
    Qt
)

from aqt.utils import (
    openFolder,
    restoreGeom,
    saveGeom,
    tooltip,
)

from .config import gc
from .forms import versions


class OldVersions(QDialog):
    def __init__(self, parent, note, boxname, folder, currContent):
        QDialog.__init__(self, parent, Qt.Window)
        self.parent = parent
        self.note = note
        self.boxname = boxname
        self.folder = folder
        self.currContent = currContent
        self.versions = sorted(os.listdir(self.folder), reverse=True)
        self.model = self.note.model()
        self.dialog = versions.Ui_Dialog()
        self.dialog.setupUi(self)
        restoreGeom(self, "1043915942_OldVersions")
        self.setWindowTitle("Anki - manage prior versions of this card template element")
        self.dialog.pb_folder.clicked.connect(self.openFolder)
        self.dialog.pb_diff.clicked.connect(self.onDiff)
        self.dialog.textEdit.setReadOnly(True)
        self.setupCombo()

    def setupCombo(self):
        self.dialog.comboBox.currentIndexChanged.connect(self.updateTextEdit)
        for f in self.versions:
            self.dialog.comboBox.addItem(f)
        self.updateTextEdit()

    def updateTextEdit(self):
        i = self.dialog.comboBox.currentIndex()
        p = os.path.join(self.folder, self.versions[i])
        with io.open(p, "r", encoding="utf-8") as f:
            content = f.read()
        self.dialog.textEdit.setPlainText(content)

    def openFolder(self):
        openFolder(self.folder)

    def onDiff(self):
        i = self.dialog.comboBox.currentIndex()
        try:
            old = self.versions[i]
        except:
            tooltip('no saved versions for the "{}" of this model found. Aborting...'.format(
                self.boxname))
        oldabs = os.path.join(self.folder, old)

        if self.boxname == "css":
            ext = ".css"
        else:
            ext = ".html"
        suf = "current" + ext
        cur = NamedTemporaryFile(delete=False, suffix=suf)
        cur.write(str.encode(self.currContent))
        cur.close()

        cmd = gc("diffcommandstart")
        if not isinstance(cmd, list):
            tooltip("Invalid settings for 'diffcommand'. Must be a list. Aborting ...")
            return
        cmd.extend([cur.name, oldabs])
        try:
            subprocess.Popen(cmd)
        except:
            tooltip("Error while trying to open the external editor. Maybe there's an error in your config.")

    def reject(self):
        saveGeom(self, "1043915942_OldVersions")
        QDialog.reject(self)

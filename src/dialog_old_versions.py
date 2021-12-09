import io
import os

from aqt import (
    QDialog,
    Qt,
    mw,
)
from aqt.qt import (
    qtmajor,
)
from anki.utils import (
    pointVersion,
)
from aqt.utils import (
    openFolder,
    restoreGeom,
    saveGeom,
    tooltip,
)

from .external_editor import diff_text_with_other_file_in_external

if qtmajor == 5:
    from .forms5 import versions
else:
    from .forms6 import versions

class OldVersions(QDialog):
    def __init__(self, parent, note, boxname, folder, currContent):
        QDialog.__init__(self, parent, Qt.WindowType.Window)
        if pointVersion() <45:
            mw.setupDialogGC(self)
        else:
            mw.garbage_collect_on_dialog_finish(self)
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
        diff_text_with_other_file_in_external(self.currContent, self.boxname, oldabs)

    def reject(self):
        saveGeom(self, "1043915942_OldVersions")
        QDialog.reject(self)

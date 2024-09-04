from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import pyqtSignal

class QTextCheckBox(QtWidgets.QCheckBox):
    """This helper class translate CheckState 2 to 1 as needed for OPALS"""
    textChanged = pyqtSignal(str, name="textChanged")

    def __init__(self, *args, **kwargs):
        super(QTextCheckBox, self).__init__(*args, **kwargs)
        self.stateChanged.connect(self.changed)

    def changed(self, text):
        #print(f"QTextCheckBox.stateChanged={text}")
        if self.isChecked():
            self.textChanged.emit("1")
        else:
            self.textChanged.emit("0")

    def text(self):
        #print(f"QTextCheckBox.text: {self.isChecked()}")
        if self.isChecked():
            return "1"
        else:
            return "0"

    def setText(self, QString):
        if QString == "1":
            self.setCheckState(2)
        else:
            self.setCheckState(0)

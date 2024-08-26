from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import pyqtSignal

class QTextComboBox(QtWidgets.QComboBox):
    def __init__(self, *args, **kwargs):
        super(QTextComboBox, self).__init__(*args, **kwargs)
        self.textChanged = self.currentTextChanged

    def text(self):
        return self.currentText()

    def setText(self, QString):
        i = self.findText(QString)
        if i > 0:
            self.setCurrentIndex(i)
        elif self.isEditable():
            self.lineEdit().setText(QString)


from PyQt4 import QtGui

class QTextComboBox(QtGui.QComboBox):
    def __init__(self, *args, **kwargs):
        super(QTextComboBox, self).__init__(*args, **kwargs)

    def text(self):
        return self.currentText()

    def setText(self, QString):
        i = self.findText(QString)
        if i > 0:
            self.setCurrentIndex(i)
        elif self.isEditable():
            self.lineEdit().setText(QString)

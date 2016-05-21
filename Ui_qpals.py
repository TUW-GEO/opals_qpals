# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file Ui_qpals.ui
# Created with: PyQt4 UI code generator 4.4.4
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
import os

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class Ui_qpals(object):
    def __init__(self):
        self.lastpath = os.getenv('HOME')

    def setupUi(self, qpals):
        qpals.setObjectName("qpals")
        qpals.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(qpals)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.label_0 = QtGui.QLabel(qpals)
        self.label_0.setGeometry(QtCore.QRect(10, 10, 100, 10))
        self.label_0.setObjectName("lblId0")

        self.label_1 = QtGui.QLabel(qpals)
        self.label_1.setGeometry(QtCore.QRect(10, 35, 100, 10))
        self.label_1.setObjectName("lblId1")

        self.inFile = QtGui.QLineEdit(qpals)
        self.inFile.setGeometry(QtCore.QRect(190, 10, 170, 20))
        self.inFile.setObjectName("inFile")

        self.cominFile = QtGui.QPushButton(qpals)
        self.cominFile.setGeometry(QtCore.QRect(360, 10, 20, 20))
        self.cominFile.setObjectName(("cominFile"))
        self.inFile.setStyleSheet(("background-color: rgb(255, 255, 127);"))

        self.visType = QtGui.QComboBox(qpals)
        self.visType.setGeometry(QtCore.QRect(190, 35, 170, 20))
        self.visType.setObjectName("comVisType")

        self.retranslateUi(qpals)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), qpals.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), qpals.reject)
        QtCore.QMetaObject.connectSlotsByName(qpals)

    def retranslateUi(self, qpals):
        qpals.setWindowTitle(QtGui.QApplication.translate("qpals", "qpals", None, QtGui.QApplication.UnicodeUTF8))

        self.label_0.setToolTip(_translate("Dialog", " input data manager file ", None))
        self.label_0.setText(_translate("Dialog", "odm to visualize", None))
        self.label_1.setText(_translate("Dialog", "visualisation type", None))

        self.visType.addItems(['zcolor', 'mbr', 'alpha', 'convexhull', 'boundingbox'])

        self.cominFile.setToolTip(_translate("Dialog", "open file browser", None))
        self.cominFile.setText(_translate("Dialog", "...", None))
        self.cominFile.clicked.connect(self.cominFile_clicked)


    def cominFile_clicked(self):
        filename= QtGui.QFileDialog.getOpenFileNames(None, 'File for inFile', self.lastpath) # 0x4 for no confirmation on overwrite
        if filename:
            self.lastpath = os.path.dirname(filename[0])
        self.inFile.setText(_fromUtf8(", ".join(filename)))

    def getFileName(self):
        return self.inFile.text()

    def getVisType(self):
        return str(self.visType.currentText())
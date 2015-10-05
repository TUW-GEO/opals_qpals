# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file Ui_qpals.ui
# Created with: PyQt4 UI code generator 4.4.4
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_qpals(object):
    def setupUi(self, qpals):
        qpals.setObjectName("qpals")
        qpals.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(qpals)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.retranslateUi(qpals)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), qpals.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), qpals.reject)
        QtCore.QMetaObject.connectSlotsByName(qpals)

    def retranslateUi(self, qpals):
        qpals.setWindowTitle(QtGui.QApplication.translate("qpals", "qpals", None, QtGui.QApplication.UnicodeUTF8))

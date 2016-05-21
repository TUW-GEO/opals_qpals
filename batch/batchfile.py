__author__ = 'lukas'
from PyQt4 import QtCore, QtGui

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

class BatchFile():
    def __init__(self, filename=None):
        self.filename = filename
        self.lines = []
        self.opalsCommands = {}

    def load(self):
        if self.filename:
            with open(self.filename) as w:
                lineno = 0
                for line in w:  # Process line in Batch Script
                    self.lines.append(line)
                    if "opals" in line: #
                        words = line.strip().split(" ")
                        module_name = words[0]
                        params = {}
                        paramname = ""
                        for word in words[1:]:
                            if word.startswith("::"):
                                break
                            if word.startswith("-"):
                                paramname = word
                            else:
                                if paramname in params:
                                    params[paramname].append(word)
                                else:
                                    params[paramname] = [word]

                        self.opalsCommands[lineno] = [module_name, params]
                    lineno += 1

        else:
            raise IOError

    def __str__(self):
        ret = "Opals Batch Object\n=================="
        ret += "\nLines:\n"
        for line in self.lines:
            ret += "\t" + line
        ret += "\n\nRecognized commands:"
        for key in self.opalsCommands.iterkeys():
            ret += "\n\t(%2s) %s:\n"%(key, self.opalsCommands[key][0]) + self.opalsCommand2str(self.opalsCommands[key][1])
        return ret

    @staticmethod
    def opalsCommand2str(opalsCommand):
        ret = ""
        print opalsCommand
        for key in opalsCommand.iterkeys():
            ret += "\t\t" + key + ": " + str(opalsCommand[key]) + "\n"
        return ret

    def createUI(self):
        return Ui_Dialog()

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(669, 449)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("/media/lukas/58BA2DF3BA2DCDF6/Users/Lukas/Desktop/FE/logo_geo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.progressBar = QtGui.QProgressBar(Dialog)
        self.progressBar.setGeometry(QtCore.QRect(10, 413, 421, 23))
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.pushButton = QtGui.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(10, 30, 158, 27))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(10, 10, 111, 17))
        self.label.setObjectName(_fromUtf8("label"))
        self.line = QtGui.QFrame(Dialog)
        self.line.setGeometry(QtCore.QRect(170, 10, 16, 361))
        self.line.setFrameShape(QtGui.QFrame.VLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(190, 10, 221, 17))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.line_2 = QtGui.QFrame(Dialog)
        self.line_2.setGeometry(QtCore.QRect(490, 10, 16, 361))
        self.line_2.setFrameShape(QtGui.QFrame.VLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(510, 10, 91, 17))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.pushButton_2 = QtGui.QPushButton(Dialog)
        self.pushButton_2.setGeometry(QtCore.QRect(190, 30, 87, 27))
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.pushButton_3 = QtGui.QPushButton(Dialog)
        self.pushButton_3.setGeometry(QtCore.QRect(340, 30, 121, 27))
        self.pushButton_3.setAcceptDrops(True)
        self.pushButton_3.setObjectName(_fromUtf8("pushButton_3"))
        self.pushButton_4 = QtGui.QPushButton(Dialog)
        self.pushButton_4.setGeometry(QtCore.QRect(190, 70, 87, 27))
        self.pushButton_4.setObjectName(_fromUtf8("pushButton_4"))
        self.pushButton_5 = QtGui.QPushButton(Dialog)
        self.pushButton_5.setGeometry(QtCore.QRect(510, 30, 151, 27))
        self.pushButton_5.setObjectName(_fromUtf8("pushButton_5"))
        self.pushButton_6 = QtGui.QPushButton(Dialog)
        self.pushButton_6.setGeometry(QtCore.QRect(440, 410, 111, 27))
        self.pushButton_6.setObjectName(_fromUtf8("pushButton_6"))
        self.pushButton_7 = QtGui.QPushButton(Dialog)
        self.pushButton_7.setGeometry(QtCore.QRect(556, 410, 101, 27))
        self.pushButton_7.setObjectName(_fromUtf8("pushButton_7"))
        self.pushButton_8 = QtGui.QPushButton(Dialog)
        self.pushButton_8.setGeometry(QtCore.QRect(556, 380, 101, 27))
        self.pushButton_8.setObjectName(_fromUtf8("pushButton_8"))
        self.pushButton_9 = QtGui.QPushButton(Dialog)
        self.pushButton_9.setGeometry(QtCore.QRect(556, 350, 101, 27))
        self.pushButton_9.setObjectName(_fromUtf8("pushButton_9"))
        self.pushButton_10 = QtGui.QPushButton(Dialog)
        self.pushButton_10.setGeometry(QtCore.QRect(10, 110, 151, 27))
        self.pushButton_10.setObjectName(_fromUtf8("pushButton_10"))
        self.pushButton_12 = QtGui.QPushButton(Dialog)
        self.pushButton_12.setGeometry(QtCore.QRect(190, 110, 87, 27))
        self.pushButton_12.setObjectName(_fromUtf8("pushButton_12"))
        self.pushButton_14 = QtGui.QPushButton(Dialog)
        self.pushButton_14.setGeometry(QtCore.QRect(340, 70, 121, 27))
        self.pushButton_14.setObjectName(_fromUtf8("pushButton_14"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "qpals batch planner", None))
        self.progressBar.setFormat(_translate("Dialog", "42 % (import) - module 1/3", None))
        self.pushButton.setText(_translate("Dialog", "C:\\...\\input.las", None))
        self.label.setText(_translate("Dialog", "input files", None))
        self.label_2.setText(_translate("Dialog", "opals Modules and temporary files", None))
        self.label_3.setText(_translate("Dialog", "output files", None))
        self.pushButton_2.setText(_translate("Dialog", "import", None))
        self.pushButton_3.setText(_translate("Dialog", "C:\\..\\input.odm", None))
        self.pushButton_4.setText(_translate("Dialog", "cell", None))
        self.pushButton_5.setText(_translate("Dialog", "C:\\...\\dhm_2.tiff", None))
        self.pushButton_6.setText(_translate("Dialog", "Run", None))
        self.pushButton_7.setText(_translate("Dialog", "Cancel", None))
        self.pushButton_8.setText(_translate("Dialog", "Save to .bat", None))
        self.pushButton_9.setText(_translate("Dialog", "Load from.bat", None))
        self.pushButton_10.setText(_translate("Dialog", "C:\\...\\dhm.tiff", None))
        self.pushButton_12.setText(_translate("Dialog", "algebra", None))
        self.pushButton_14.setText(_translate("Dialog", "C:\\...\\input.tiff", None))

if __name__ == "__main__":
    #BatchInst = Batch(r"C:\Users\Lukas\.qgis2\python\plugins\qpals\batchtest.bat")
    BatchInst = BatchFile(r"/media/lukas/58BA2DF3BA2DCDF6/Dokumente und Einstellungen/Lukas/.qgis2/python/plugins/qpals/batchtest.bat")
    BatchInst.load()
    print(BatchInst)
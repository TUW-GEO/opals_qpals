from PyQt4 import QtGui

class QpalsParamMsgBtn(QtGui.QToolButton):

    def __init__(self, popupmessage, *args, **kwargs):
        self.popupmessage = popupmessage
        super(QpalsParamMsgBtn, self).__init__(*args, **kwargs)

        # connect on-click
        self.clicked.connect(lambda: self.displayParamMsgBox(popupmessage))

    def displayParamMsgBox(self, param):
        msg = QtGui.QMessageBox()
        msg.setIcon(QtGui.QMessageBox.Question)
        msg.setText(param['desc'])
        msg.setInformativeText(param['longdesc'])
        msg.setWindowTitle(param['name'])
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        msg.exec_()

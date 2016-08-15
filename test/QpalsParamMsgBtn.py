from PyQt4 import QtGui, QtCore

class QpalsParamMsgBtn(QtGui.QToolButton):

    def __init__(self, popupmessage, parent, *args, **kwargs):
        self.popupmessage = popupmessage
        super(QpalsParamMsgBtn, self).__init__(*args, **kwargs)
        self.parent = parent
        # connect on-click
        self.clicked.connect(lambda: self.displayParamMsgBox(popupmessage))

    def displayParamMsgBox(self, param):
        msg = QtGui.QMessageBox(self.parent)
        msg.setIcon(QtGui.QMessageBox.Question)
        msg.setText(param['desc'])
        msg.setInformativeText(param['longdesc'])
        msg.setWindowTitle(param['name'])
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        msg.exec_()

    def __deepcopy__(self, memo={}):
        # Disable deep copying because of "parent"
        # Return shallow copy instead
        return self


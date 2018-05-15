from qgis.PyQt import QtWidgets, QtGui
import os


IconPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "media")

lockedIcon = QtGui.QIcon(os.path.join(IconPath, "lockIcon_locked.png"))
unlockedIcon = QtGui.QIcon(os.path.join(IconPath, "lockIcon_open.png"))

class QpalsParamMsgBtn(QtWidgets.QToolButton):

    def __init__(self, popupmessage, parent, *args, **kwargs):
        self.popupmessage = popupmessage
        super(QpalsParamMsgBtn, self).__init__(*args, **kwargs)
        self.parent = parent
        # connect on-click
        self.clicked.connect(lambda: self.displayParamMsgBox(popupmessage))

    def displayParamMsgBox(self, param):
        msg = QtWidgets.QMessageBox(self.parent)
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setText(param.desc)
        msg.setInformativeText(param.longdesc)
        msg.setWindowTitle(param.name)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def __deepcopy__(self, memo={}):
        # Disable deep copying because of "parent"
        # Return shallow copy instead
        return self

class QpalsLockIconBtn(QtWidgets.QToolButton):
    def __init__(self, param, *args, **kwargs):
        super(QpalsLockIconBtn, self).__init__(*args, **kwargs)
        self.setIcon(unlockedIcon)
        self.setStyleSheet("border-style: none;opacity:0.5;")
        self.param = param
        if self.param.changed:
            self.setIcon(lockedIcon)
        self.clicked.connect(self.changeLockStatus)

    def changeLockStatus(self):
        self.param.changed = not self.param.changed
        if self.param.changed:
            self.setIcon(lockedIcon)
        else:
            self.setIcon(unlockedIcon)
from PyQt4 import QtGui

class QpalsParamBrowseBtn(QtGui.QToolButton):

    def __init__(self, paramname, *args, **kwargs):
        self.paramname = paramname
        super(QpalsParamBrowseBtn, self).__init__(*args, **kwargs)

        # connect on-click
        self.clicked.connect(self.getFileName)

    def getFileName(self):

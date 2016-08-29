from PyQt4 import QtCore, QtGui
from matplotlib import pyplot
import QpalsModuleBase

class QpalsSectionTool():

    def __init__(self):
        self.ui = None

    def getUI(self):
        self.ui = QtGui.QWidget()
        layout = QtGui.QFormLayout()
        layout.addItem(QtGui.QLabel("Test"))
        self.ui.setLayout(layout)
        return self.ui
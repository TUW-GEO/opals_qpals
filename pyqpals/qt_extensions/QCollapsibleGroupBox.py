from qgis.PyQt import QtWidgets

class QCollapsibleGroupBox(QtWidgets.QGroupBox):
    def __init__(self, *args,  **kwargs):
        super(QCollapsibleGroupBox, self).__init__(*args, **kwargs)
        self.setCheckable(True)
        self.toggled.connect(self.switchstate)
        self.store_height = self.height()

    def switchstate(self, newstate):
        self.setMaximumHeight(99999 if newstate else 17)

# class QCollapsibleGroupBox(QtGui.QWidget):
#     def __init__(self, title = "", *args,  **kwargs):
#         if "collapsed" in kwargs:
#             self.state = kwargs["collapsed"]
#             kwargs.pop("collapsed")
#         else:
#             self.state = False
#         super(QCollapsibleGroupBox, self).__init__(*args, **kwargs)
#         self.collapsebtn = QtGui.QPushButton("-" if self.state else "+")
#         self.collapsebtn.clicked.connect(self.switchstate)
#         self.layout = QtGui.QVBoxLayout(self)
#         self.layout.setContentsMargins(0, 24, 0, 0)
#         self.groupBox = QtGui.QGroupBox(kwargs.get("title", ""))
#         self.layout.addWidget(self.collapsebtn)
#         self.layout.addWidget(self.groupBox)
#         self.collapsebtn.move(0, -4)
#         self.store_height = self.height()
#         print self.store_height
#         if not self.state:
#             self.setFixedHeight(10)
#
#     def switchstate(self):
#         self.state = not self.state
#         self.collapsebtn.setText("-" if self.state else "+")
#         self.setFixedHeight(self.store_height if self.state else 10)
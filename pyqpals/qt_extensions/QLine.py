
from qgis.PyQt import QtWidgets

class QHLine(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super(QHLine, self).__init__(*args,**kwargs)
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

class QVLine(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super(QVLine, self).__init__(*args,**kwargs)
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

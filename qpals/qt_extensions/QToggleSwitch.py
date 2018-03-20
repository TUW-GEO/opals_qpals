from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui

STATUS_LEFT =  "[X]---[ ]"
STATUS_RIGHT = "[ ]---[X]"

class QToggleSwitch(QtWidgets.QWidget):
    toggled_signal = QtCore.pyqtSignal(bool)

    def __init__(self, left_text="", right_text=""):
        super().__init__()

        self.state = True

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)
        (left, right, top, bottom) = vbox.getContentsMargins()
        vbox.setContentsMargins(0, 0, 5, 5)

        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)

        self.left_text = QtWidgets.QPushButton(left_text)
        self.left_text.setFlat(True)
        self.left_text.clicked.connect(self.clicked_left)
        hbox.addWidget(self.left_text, stretch=0)

        self.btn = QtWidgets.QPushButton(STATUS_LEFT)
        hbox.addWidget(self.btn)
        self.btn.setFixedWidth(45)
        self.btn.clicked.connect(self.clicked)

        self.right_text = QtWidgets.QPushButton(right_text)
        self.right_text.setFlat(True)
        self.right_text.clicked.connect(self.clicked_right)
        hbox.addWidget(self.right_text, stretch=0)

    def clicked(self):
        self.state = not self.state
        if self.state:
            self.btn.setText(STATUS_LEFT)
        else:
            self.btn.setText(STATUS_RIGHT)
        self.toggled_signal.emit(self.state)

    def clicked_left(self):
        self.state = True
        self.btn.setText(STATUS_LEFT)
        self.toggled_signal.emit(self.state)

    def clicked_right(self):
        self.state = False
        self.btn.setText(STATUS_RIGHT)
        self.toggled_signal.emit(self.state)


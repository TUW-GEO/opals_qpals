from builtins import str
from qgis.PyQt import QtCore, QtGui, QtWidgets
from qgis.core import QgsProject as QgsMapLayerRegistry
import os, re

class QpalsDropTextbox(QtWidgets.QComboBox):
    def __init__(self, layerlist=None, text=None, show_layers=True, filterrex='.*', *args, **kwargs):
        super(QpalsDropTextbox, self).__init__(*args, **kwargs)
        self.textChanged = self.currentTextChanged
        self.setAcceptDrops(True)
        #self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred))
        self.setEditable(True)
        if text:
            self.lineEdit().setText(text)
        self.setPlaceholderText("drop file/layer here...")
        self.layerlist = layerlist
        self.editingFinished = self.lineEdit().editingFinished
        self.showLayers = show_layers
        self.filterrex = filterrex
        self.reloadLayers()

    def showPopup(self):
        self.reloadLayers()
        super(QpalsDropTextbox, self).showPopup()


    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(u"application/qgis.layertreemodeldata") or e.mimeData().hasUrls():  #is a qgis layer or a file
            e.accept()
            QtWidgets.QToolTip.showText(self.mapToGlobal(e.pos()), "[Ctrl] to append")
        else:
            e.ignore()

    def dropEvent(self, e):
        paths = []
        if e.mimeData().hasFormat(u"application/qgis.layertreemodeldata"):
            data = str(e.mimeData().data(u"application/qgis.layertreemodeldata"))
            from xml.dom import minidom
            dom = minidom.parseString(data)
            tmd = dom.getElementsByTagName("layer_tree_model_data")[0]
            ltls = tmd.getElementsByTagName("layer-tree-layer")
            for ltl in ltls:
                ide = ltl.attributes["id"].value
                layer = None

                for lyr in list(QgsMapLayerRegistry.instance().mapLayers().values()):
                    if lyr.id() == ide:
                        layer = lyr
                        break
                odmpath = lyr.customProperty("qpals-odmpath", "")
                if odmpath:
                    paths.append(odmpath)  # opals vis file - takes the odm
                else:
                    paths.append(layer.source())  # any other qgis file - takes the real path

        elif e.mimeData().hasUrls():
            data = e.mimeData().urls()

            paths = [str(d.path())[1:] for d in data]

        if e.keyboardModifiers() == QtCore.Qt.ControlModifier and self.text() != "":
            self.setText(";".join([self.text()] + paths))
        else:
            self.setText(";".join(paths))
        #e.acceptProposedAction()
        e.setDropAction(QtCore.Qt.TargetMoveAction)  # retain the original
        e.accept()
        self.editingFinished.emit()

    def setText(self,s):
        self.lineEdit().setText(s)

    def text(self):
        return self.lineEdit().text()

    def reloadLayers(self):
        text = self.text()
        if self.showLayers:
            while self.count() > 0:
                self.removeItem(0)
            if self.text() == "":
                self.addItem("")
            layers = list(QgsMapLayerRegistry.instance().mapLayers().values())
            for layer in layers:
                odmpath = layer.customProperty("qpals-odmpath", "")
                if odmpath:
                    if re.search(self.filterrex, odmpath):
                        self.addItem(odmpath)
                elif os.path.exists(layer.source()):
                    if re.search(self.filterrex, layer.source()):
                        self.addItem(layer.source())
        self.setText(text)

    def setPlaceholderText(self, text):
        self.lineEdit().setPlaceholderText(text)

class droptester(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(droptester, self).__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        lo = QtWidgets.QFormLayout()
        lo.addRow(QtWidgets.QLabel("Drop something here:"))
        l1 = QtWidgets.QLabel("")
        l2 = QtWidgets.QLabel("")
        dropspace = QpalsDropTextbox()
        lo.addRow(dropspace)
        lo.addRow(l1)
        lo.addRow(l2)
        self.setLayout(lo)
        self.setWindowTitle("Hallo Alina")
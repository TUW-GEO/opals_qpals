from PyQt4 import QtCore, QtGui

class QpalsDropTextbox(QtGui.QLineEdit):
    def __init__(self, layerlist=None, *args, **kwargs):
        super(QpalsDropTextbox, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.setPlaceholderText("drop file/layer here...")
        self.layerlist = layerlist

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(u"application/qgis.layertreemodeldata") or e.mimeData().hasUrls():  #is a qgis layer or a file
            e.accept()
            QtGui.QToolTip.showText(self.mapToGlobal(e.pos()), "[Ctrl] to append")
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
                from qgis.core import QgsMapLayerRegistry
                for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
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



class droptester(QtGui.QWidget):

    def __init__(self, *args, **kwargs):
        super(droptester, self).__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        lo = QtGui.QFormLayout()
        lo.addRow(QtGui.QLabel("Drop something here:"))
        l1 = QtGui.QLabel("")
        l2 = QtGui.QLabel("")
        dropspace = QpalsDropTextbox()
        lo.addRow(dropspace)
        lo.addRow(l1)
        lo.addRow(l2)
        self.setLayout(lo)
        self.setWindowTitle("Hallo Alina")
from PyQt4 import QtCore, QtGui

class drop(QtGui.QLineEdit):
    def __init__(self, label1, label2, *args, **kwargs):
        super(drop, self).__init__(*args, **kwargs)
        self.l1 = label1
        self.l2 = label2
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(u"application/qgis.layertreemodeldata") or e.mimeData().hasUrls():  #is a qgis layer or a file
            e.accept()
            self.l2.setText("Is acceptable")
        else:
            e.ignore()
            self.l2.setText("Is not acceptable")

    def dropEvent(self, e):
        if e.mimeData().hasFormat(u"application/qgis.layertreemodeldata"):
            data = str(e.mimeData().data(u"application/qgis.layertreemodeldata"))
            self.l1.setText(data)
            from xml.dom import minidom
            dom = minidom.parseString(data)
            tmd = dom.getElementsByTagName("layer_tree_model_data")[0]
            ltls = tmd.getElementsByTagName("layer-tree-layer")
            paths = []
            for ltl in ltls:
                ide = ltl.attributes["id"].value
                name = ltl.attributes["name"].value
                layer = None
                from qgis.core import QgsMapLayerRegistry
                for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
                    if lyr.id() == ide:
                        layer = lyr
                        break
                paths.append(layer.source())
            self.setText(";".join(paths))

        elif e.mimeData().hasUrls():
            data = e.mimeData().urls()
            self.l1.setText(str(data))
            self.setText(";".join([str(d.path())[1:] for d in data]))
        #e.acceptProposedAction()
        e.setDropAction(QtCore.Qt.TargetMoveAction)  # retain the original
        e.ignore()



class droptester(QtGui.QWidget):

    def __init__(self, *args, **kwargs):
        super(droptester, self).__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        lo = QtGui.QFormLayout()
        lo.addRow(QtGui.QLabel("Drop something here:"))
        l1 = QtGui.QLabel("")
        l2 = QtGui.QLabel("")
        dropspace = drop(l1, l2)
        lo.addRow(dropspace)
        lo.addRow(l1)
        lo.addRow(l2)
        self.setLayout(lo)
        self.setWindowTitle("Hallo Alina")
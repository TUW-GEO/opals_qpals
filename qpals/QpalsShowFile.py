import QpalsDropTextbox
import QpalsModuleBase
import tempfile
import os
import QpalsParameter
from PyQt4 import QtGui, QtCore
from qgis.core import *
from qgis.gui import *

class QpalsShowFile():
    METHOD_SHADING = 0
    METHOD_Z_COLOR = 1
    METHOD_Z = 2
    METHOD_BOX = 3
    METHOD_MBR = 4
    METHOD_CONVEX_HULL = 5
    METHOD_ALPHA_SHAPE = 6

    def __init__(self, iface, qpalsLayerList, project=None):
        self.dropspace = None
        self.visMethod = None
        self.curVisMethod = -1
        if project:
            self.curVisMethod = project.vismethod
        self.iface = iface
        self.layerlist = qpalsLayerList
        self.ui = None
        self.project = project

    def dragEnterEvent(self, e):
        return self.dropspace.dragEnterEvent(e)

    def dropEvent(self, e):
        return self.dropspace.dropEvent(e)

    def show(self):
        if not self.ui:
            self.initUI()
        self.ui.show()

    def initUI(self):
        self.ui = QtGui.QDialog()
        lo = QtGui.QFormLayout()
        self.ui.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        lo.addRow(QtGui.QLabel("Load ALS file(s):"))
        self.dropspace = QpalsDropTextbox.QpalsDropTextbox(layerlist=self.layerlist)
        self.dropspace.setMinimumContentsLength(20)
        self.dropspace.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        lo.addRow(self.dropspace)
        self.visMethod = QtGui.QComboBox()
        self.visMethod.addItem("Shading (raster)")
        self.visMethod.addItem("Z-Color (raster)")
        self.visMethod.addItem("Z-Value (raw height values)(raster)")
        self.visMethod.addItem("Bounding box (vector)")
        self.visMethod.addItem("Minimum bounding rectangle (vector)")
        self.visMethod.addItem("Convex hull (vector)")
        self.visMethod.addItem("Alpha shape (vector)")
        self.visMethod.addItem("Isolines (vector, based on Z-Value)")
        self.visMethod.currentIndexChanged.connect(self.updatevisMethod)


        self.cellSizeLbl = QtGui.QLabel("Set cell size:")
        self.cellSizeBox = QtGui.QLineEdit()
        self.cellFeatLbl = QtGui.QLabel("Set feature:")
        self.cellFeatCmb = QtGui.QComboBox()
        self.isoInteLbl = QtGui.QLabel("Set isoline interval:")
        self.isoInteBox = QtGui.QLineEdit()
        self.isoInteBox.setText("10")
        cellInst = QpalsModuleBase.QpalsModuleBase(os.path.join(self.project.opalspath, "opalsCell.exe"), self.project)
        cellInst.load()
        for param in cellInst.params:
            if param.name.lower() == "cellsize":
                self.cellSizeBox.setText(param.val)
                break
        self.cellFeatCmb.addItems(["min", "max", "diff", "mean", "median", "sum", "variance", "rms", "pdens", "pcount",
                                   "minority", "majority", "entropy"])
        self.cellFeatCmb.setCurrentIndex(3)
        lo.addRow(self.cellSizeLbl, self.cellSizeBox)
        lo.addRow(self.cellFeatLbl, self.cellFeatCmb)
        lo.addRow(self.isoInteLbl, self.isoInteBox)
        lo.addRow(self.visMethod)
        self.okBtn = QtGui.QPushButton("Load")
        self.okBtn.clicked.connect(self.loadHelper)
        lo.addRow(self.okBtn)
        self.ui.setLayout(lo)
        self.ui.setWindowTitle("Open ALS file")

        self.visMethod.setCurrentIndex(3)

    def updatevisMethod(self):
        self.curVisMethod = self.visMethod.currentIndex()
        if self.curVisMethod in [0, 1, 2, 7]:
            self.cellSizeLbl.show()
            self.cellSizeBox.show()
            self.cellFeatLbl.show()
            self.cellFeatCmb.show()
        else:
            self.cellSizeLbl.hide()
            self.cellSizeBox.hide()
            self.cellFeatLbl.hide()
            self.cellFeatCmb.hide()

        if self.curVisMethod in [7]:
            self.isoInteLbl.show()
            self.isoInteBox.show()
        else:
            self.isoInteLbl.hide()
            self.isoInteBox.hide()


    def loadHelper(self):
        return self.load(self.dropspace.text().split(";"))

    def load(self, infile_s=None):
        try:
            layer = None
            if self.ui:
                self.okBtn.setText("Loading...")
                self.okBtn.setEnabled(False)
            for drop in infile_s:
                if drop:
                    if drop.endswith(".tif") or drop.endswith(".tiff"):
                        layer = self.iface.addRasterLayer(drop, os.path.basename(drop))
                    elif drop.endswith(".shp"):
                        layer = self.iface.addVectorLayer(drop, os.path.basename(drop), "ogr")
                    else:
                        if not drop.endswith(".odm"):
                            drop = self.callImport(drop)
                        if self.curVisMethod == 0:
                            cellf = self.callCell(drop)
                            visfile = self.callShade(cellf)
                        elif self.curVisMethod == 1:
                            cellf = self.callCell(drop)
                            visfile = self.callZColor(cellf)
                        elif self.curVisMethod == 2:
                            visfile = self.callCell(drop)
                        elif self.curVisMethod == 3:
                            (xmin, ymin, xmax, ymax) = self.callInfo(drop)
                        elif self.curVisMethod == 4:
                            visfile = self.callBounds(drop, "minimumRectangle")
                        elif self.curVisMethod == 5:
                            visfile = self.callBounds(drop, "convexHull")
                        elif self.curVisMethod == 6:
                            visfile = self.callBounds(drop, "alphaShape")
                        elif self.curVisMethod == 7:
                            cellf = self.callCell(drop)
                            visfile = self.callIsolines(cellf)

                        self.updateText("Loading layer into QGIS...")
                        # load layer
                        if self.curVisMethod in [4, 5, 6, 7]:  # vector file
                            layer = self.iface.addVectorLayer(visfile, os.path.basename(drop), "ogr")
                        elif self.curVisMethod in [0, 1, 2]:
                            layer = self.iface.addRasterLayer(visfile, os.path.basename(drop))
                        elif self.curVisMethod == 3:
                            layer = self.iface.addVectorLayer("Polygon", os.path.basename(drop), "memory")
                            pr = layer.dataProvider()
                            feat = QgsFeature()
                            feat.setGeometry(QgsGeometry.fromPolygon([[QgsPoint(xmin, ymin),
                                                                       QgsPoint(xmax, ymin),
                                                                       QgsPoint(xmax, ymax),
                                                                       QgsPoint(xmin, ymax)]]))
                            pr.addFeatures([feat])
                            layer.updateExtents()


                    layer.setCustomProperty("qpals-odmpath", drop)
                    QgsMapLayerRegistry.instance().addMapLayer(layer)

                    if self.curVisMethod in [3, 4, 5, 6]:
                        layer.setCustomProperty("labeling", "pal")
                        layer.setCustomProperty("labeling/enabled", "true")
                        layer.setCustomProperty("labeling/isExpression", "true")
                        layer.setCustomProperty("labeling/fontFamily", "Arial")
                        layer.setCustomProperty("labeling/fontSize", "10")
                        layer.setCustomProperty("labeling/fieldName", "'%s'" % os.path.splitext(os.path.basename(drop))[0])
                        layer.setCustomProperty("labeling/placement", "1")
                        layer.triggerRepaint()
                        self.iface.mapCanvas().refresh()
                    self.layerlist[layer.id()] = drop
        except Exception as e:
            self.iface.messageBar().pushMessage('Something went wrong! See the message log for more information.',
                                                duration=3)
            print e

        if self.ui:
            self.okBtn.setText("Load")
            self.okBtn.setEnabled(True)
            self.dropspace.setText("")

        return layer

    def callImport(self, infile):
        self.updateText("Importing to odm...")
        odmfile = self.call("opalsImport", {"inFile": infile, "outFile": infile + ".odm"})
        return odmfile

    def callInfo(self, infile):
        self.updateText("Calling module opalsInfo...")
        outdict = self.call("opalsInfo", {"inFile": infile}, returnstdout=True, nooutfile=True)
        lines = outdict["stdout"].split("\n")
        for line in lines:
            if line.startswith("Minimum X-Y-Z"):
                linearr = line.split()
                minX = float(linearr[2])
                minY = float(linearr[3])
            if line.startswith("Maximum X-Y-Z"):
                linearr = line.split()
                maxX = float(linearr[2])
                maxY = float(linearr[3])
                break
        return minX, minY, maxX, maxY

    def callBounds(self, infile, shapetype):
        self.updateText("Calling module opalsBounds...")
        shapefile = self.call("opalsBounds", {"inFile": infile, "boundsType": shapetype}, ".shp")
        return shapefile

    def callIsolines(self, infile):
        self.updateText("Calling module opalsIsolines...")
        shapefile = self.call("opalsIsolines", {"inFile": infile, "interval": self.isoInteBox.text()}, ".shp")
        return shapefile

    def callCell(self, infile):
        self.updateText("Calling module opalsCell...")
        rasfile = self.call("opalsCell", {"inFile": infile, "feature": "mean", "cellSize": self.cellSizeBox.text()}, ".tif")
        return rasfile

    def callShade(self, infile):
        self.updateText("Calling module opalsShade...")
        rasfile = self.call("opalsShade", {"inFile": infile}, ".tif")
        return rasfile

    def callZColor(self, infile):
        self.updateText("Calling module opalsZColor...")
        rasfile = self.call("opalsZColor", {"inFile": infile}, ".tif")
        return rasfile

    def updateText(self, text):
        if self.ui:
            self.okBtn.setText(text)
            QtGui.QApplication.processEvents()

    def call(self, module, params, outext="", returnstdout=False, nooutfile=False):
        Module = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(self.project.opalspath, module+".exe"), QpalsProject=self.project)
        if "outFile" not in params and not nooutfile:
            file = tempfile.NamedTemporaryFile(delete=False)
            params["outFile"] = file.name + outext
            file.close()
        paramlist = []
        for param in params.iterkeys():
            paramlist.append(QpalsParameter.QpalsParameter(param, params[param], None, None, None, None, None))
        Module.params = paramlist
        moduleOut = Module.run(show=0)
        if returnstdout:
            return moduleOut
        return params["outFile"]

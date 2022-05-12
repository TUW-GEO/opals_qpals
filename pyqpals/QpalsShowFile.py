from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import range
from builtins import object
import os
import tempfile

import datetime

from qgis.PyQt import QtGui
from qgis.PyQt import QtWidgets
from qgis.core import *
from qgis.gui import *

from . import QpalsModuleBase
from . import QpalsParameter
from .qt_extensions import QpalsDropTextbox
from .modules.QpalsAttributeMan import getAttributeInformation

VISUALISATION_METHODS = {
    0: "[fast] Bounding box (vector)",
    1: "[fast] Z-Overview (raster)",
    2: "[fast] Point count overview (raster)",
    3: "Shading (raster)",
    4: "Z-Color (raster)",
    5: "Z-Value (raw height values)(raster)",
    6: "Minimum bounding rectangle (vector)",
    7: "Convex hull (vector)",
    8: "Alpha shape (vector)",
    9: "Isolines",
}

class QpalsShowFile(object):
    METHOD_SHADING = 0
    METHOD_Z_COLOR = 1
    METHOD_Z = 2
    METHOD_BOX = 3
    METHOD_MBR = 4
    METHOD_CONVEX_HULL = 5
    METHOD_ALPHA_SHAPE = 6

    features = [
        "min", "max", "diff", "mean", "median", "sum", "variance", "rms", "pdens", "pcount",
        "minority", "majority", "entropy"
    ]

    def __init__(self, iface, qpalsLayerList, project=None):
        self.dropspace = None
        self.visMethod = None
        self.curVisMethod = -1
        if project:
            self.curVisMethod = project.vismethod
            self.cellSize = project.viscells
            self.cellMethod = project.viscellm
            self.isoInt = project.visisoint
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
        self.ui = QtWidgets.QDialog()
        lo = QtWidgets.QFormLayout()
        self.ui.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        lo.addRow(QtWidgets.QLabel("Load ALS file(s):"))
        self.dropspace = QpalsDropTextbox.QpalsDropTextbox(layerlist=self.layerlist)
        self.dropspace.setMinimumContentsLength(20)
        self.dropspace.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLength)
        self.dropspace.editingFinished.connect(self.inFileUpdated)
        lo.addRow(self.dropspace)
        self.visMethod = QtWidgets.QComboBox()
        self.visMethod.addItem(VISUALISATION_METHODS[0])
        self.visMethod.addItem(VISUALISATION_METHODS[1])
        self.visMethod.addItem(VISUALISATION_METHODS[2])
        self.visMethod.addItem(VISUALISATION_METHODS[3])
        self.visMethod.addItem(VISUALISATION_METHODS[4])
        self.visMethod.addItem(VISUALISATION_METHODS[5])
        self.visMethod.addItem(VISUALISATION_METHODS[6])
        self.visMethod.addItem(VISUALISATION_METHODS[7])
        self.visMethod.addItem(VISUALISATION_METHODS[8])
        self.visMethod.addItem(VISUALISATION_METHODS[9])
        self.visMethod.currentIndexChanged.connect(self.updatevisMethod)
        self.cellSizeLbl = QtWidgets.QLabel("Set cell size:")
        self.cellSizeBox = QtWidgets.QLineEdit()
        self.cellFeatLbl = QtWidgets.QLabel("Set feature:")
        self.cellFeatCmb = QtWidgets.QComboBox()
        self.cellAttrLbl = QtWidgets.QLabel("Select attribute:")
        self.cellAttrCmb = QtWidgets.QComboBox()
        self.cellAttrCmb.addItem("Z")
        self.cellAttrCmb.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.isoInteLbl = QtWidgets.QLabel("Set isoline interval:")
        self.isoInteBox = QtWidgets.QLineEdit()
        self.isoInteBox.setText("10")
        cellInst = QpalsModuleBase.QpalsModuleBase(os.path.join(self.project.opalspath, "opalsCell.exe"), self.project)
        cellInst.load()
        for param in cellInst.params:
            if param.name.lower() == "cellsize":
                self.cellSizeBox.setText(param.val)
                break
        self.cellFeatCmb.addItems(self.features)
        self.cellFeatCmb.setCurrentIndex(4)
        lo.addRow(self.cellAttrLbl, self.cellAttrCmb)
        lo.addRow(self.cellSizeLbl, self.cellSizeBox)
        lo.addRow(self.cellFeatLbl, self.cellFeatCmb)
        lo.addRow(self.isoInteLbl, self.isoInteBox)
        lo.addRow(self.visMethod)
        self.okBtn = QtWidgets.QPushButton("Load")
        self.okBtn.clicked.connect(self.loadHelper)
        lo.addRow(self.okBtn)
        self.ui.setLayout(lo)
        self.ui.setWindowTitle("Open ALS file")

        self.visMethod.setCurrentIndex(1)

    def inFileUpdated(self):
        newFile = self.dropspace.text()
        if newFile.endswith(".odm"):
            try:
                attrs, _ = getAttributeInformation(newFile, self.project)
                self.cellAttrCmb.clear()
                self.cellAttrCmb.addItems(["X", "Y", "Z"])
                for attr in attrs:
                    self.cellAttrCmb.addItem(attr[0])
                self.cellAttrCmb.setCurrentIndex(2)
            except:
                self.cellAttrCmb.clear()
                self.cellAttrCmb.addItems(["X", "Y", "Z"])
                self.cellAttrCmb.setCurrentIndex(2)


    def updatevisMethod(self):
        self.curVisMethod = self.visMethod.currentIndex()
        if self.curVisMethod in [3, 4, 5, 9]:
            self.cellSizeLbl.show()
            self.cellSizeBox.show()
            self.cellFeatLbl.show()
            self.cellFeatCmb.show()
            self.cellAttrCmb.show()
            self.cellAttrLbl.show()
        else:
            self.cellSizeLbl.hide()
            self.cellSizeBox.hide()
            self.cellFeatLbl.hide()
            self.cellFeatCmb.hide()
            self.cellAttrCmb.hide()
            self.cellAttrLbl.hide()

        if self.curVisMethod in [9]:
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
                        suffix = ""
                        attribute = "Z" if not hasattr(self, 'cellAttrCmb') else self.cellAttrCmb.currentText()
                        if self.curVisMethod == 3:
                            cellf = self.callCell(drop)
                            visfile = self.callShade(cellf)
                            suffix = "shading (%s)" % attribute
                        elif self.curVisMethod == 4:
                            cellf = self.callCell(drop)
                            visfile = self.callZColor(cellf)
                            suffix = "coloring (%s)" % attribute
                        elif self.curVisMethod == 5:
                            visfile = self.callCell(drop)
                            suffix = "(%s)" % attribute
                        elif self.curVisMethod == 0:
                            (xmin, ymin, xmax, ymax) = self.callInfo(drop)
                            suffix = "BBox"
                        elif self.curVisMethod == 6:
                            visfile = self.callBounds(drop, "minimumRectangle")
                            suffix = "MBR"
                        elif self.curVisMethod == 7:
                            visfile = self.callBounds(drop, "convexHull")
                            suffix = "convex hull"
                        elif self.curVisMethod == 8:
                            visfile = self.callBounds(drop, "alphaShape")
                            suffix = "alpha shape"
                        elif self.curVisMethod == 9:
                            cellf = self.callCell(drop)
                            visfile = self.callIsolines(cellf)
                            suffix = "isolines (%s)" % attribute
                        elif self.curVisMethod == 1:
                            visfile, isMultiBand = self.callInfo(drop, overview='Z')
                            suffix = "overview (Z)"
                            if isMultiBand:
                                bandSel = 1
                        elif self.curVisMethod == 2:
                            visfile, isMultiBand = self.callInfo(drop, overview='Pcount')
                            suffix = "overview (pcount)"
                            if isMultiBand:
                                bandSel = 2

                        self.updateText("Loading layer into QGIS...")
                        # load layer
                        if self.curVisMethod in [6, 7, 8, 9]:  # vector file
                            layer = self.iface.addVectorLayer(visfile,
                                                              os.path.basename(drop) + " - " + suffix, "ogr")
                        elif self.curVisMethod in [1, 2, 3, 4, 5]:
                            layer = self.iface.addRasterLayer(visfile,
                                                              os.path.basename(drop) + " - " + suffix)
                            if isMultiBand:
                                bandRenderer = QgsSingleBandGrayRenderer(layer.dataProvider(), bandSel)
                                layer.setRenderer(bandRenderer)
                        elif self.curVisMethod == 0:
                            layer = self.iface.addVectorLayer("Polygon",
                                                              os.path.basename(drop) + " - " + suffix, "memory")
                            pr = layer.dataProvider()
                            feat = QgsFeature()
                            feat.setGeometry(QgsGeometry.fromPolygonXY([[QgsPointXY(xmin, ymin),
                                                                       QgsPointXY(xmax, ymin),
                                                                       QgsPointXY(xmax, ymax),
                                                                       QgsPointXY(xmin, ymax)]]))
                            pr.addFeatures([feat])
                            layer.updateExtents()

                    if layer:
                        layer.setCustomProperty("qpals-odmpath", drop)
                        QgsProject.instance().addMapLayer(layer)

                        if self.curVisMethod in [0, 6, 7, 8]:
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
            print(e)

        if self.ui:
            self.okBtn.setText("Load")
            self.okBtn.setEnabled(True)
            self.dropspace.setText("")

        return layer

    def callImport(self, infile):
        self.updateText("Importing to odm...")
        odmfile = self.call("opalsImport", {"inFile": infile, "outFile": infile + ".odm"})
        return odmfile

    def callInfo(self, infile, overview=None):
        self.updateText("Calling module opalsInfo...")
        rundict = {"inFile": infile}
        if overview:
            if self.project.opalsBuildDate <= datetime.datetime(year=2022, month=5, day=5, hour=12, minute=0, second=0):
                outfile = infile.replace(".odm", "_overview_%s.tif" % overview)
                if os.path.exists(outfile) and os.stat(outfile).st_ctime == os.stat(infile).st_ctime:
                    return outfile, False  # skip running opalsInfo if file exists and has same date set
                rundict.update({'exportHeader': 'overview%s' % overview})
                outdict = self.call("opalsInfo", rundict, returnstdout=True, nooutfile=True)
                return outfile, False
            else:  #  starting with builds from May 6 2022outfile = infile.replace(".odm", "_overview_%s.tif" % overview)
                outfile = infile.replace(".odm", "_overview.tif")
                if os.path.exists(outfile) and os.stat(outfile).st_ctime == os.stat(infile).st_ctime:
                    return outfile, False  # skip running opalsInfo if file exists and has same date set
                rundict.update({'exportOverview': 'all',
                                'multiBand': '1'})
                outdict = self.call("opalsInfo", rundict, returnstdout=True, nooutfile=True)
                return outfile, True

        lines = outdict["stdout"].split("\n")
        for i in range(len(lines)):
            line = lines[i]
            if line.startswith("Minimum"):
                linearr = line.split()
                minX = float(linearr[1])
                minY = float(linearr[2])
            if line.startswith("Maximum"):
                linearr = line.split()
                maxX = float(linearr[1])
                maxY = float(linearr[2])
                break
        return minX, minY, maxX, maxY

    def callBounds(self, infile, shapetype):
        self.updateText("Calling module opalsBounds...")
        shapefile = self.call("opalsBounds", {"inFile": infile, "boundsType": shapetype}, ".shp")
        return shapefile

    def callIsolines(self, infile):
        self.updateText("Calling module opalsIsolines...")
        interval = str(self.isoInt) if not hasattr(self, 'isoInteBox') else self.isoInteBox.text()
        shapefile = self.call("opalsIsolines", {"inFile": infile, "interval": interval}, ".shp")
        return shapefile

    def callCell(self, infile):
        self.updateText("Calling module opalsCell...")
        cellsize = str(self.cellSize) if not hasattr(self,'cellSizeBox') else self.cellSizeBox.text()
        feature = self.features[self.cellMethod] if not hasattr(self,'cellFeatCmb') else self.cellFeatCmb.currentText()
        attribute = "Z" if not hasattr(self,'cellAttrCmb') else self.cellAttrCmb.currentText()
        rasfile = self.call("opalsCell", {"inFile": infile,
                                          "feature": feature,
                                          "cellSize": cellsize,
                                          "attribute": attribute}, ".tif")
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
            QtWidgets.QApplication.processEvents()

    def call(self, module, params, outext="", returnstdout=False, nooutfile=False):
        Module = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(self.project.opalspath, module+".exe"), QpalsProject=self.project)
        if "outFile" not in params and not nooutfile:
            file = tempfile.NamedTemporaryFile(delete=False)
            params["outFile"] = file.name + outext
            file.close()
        paramlist = []
        for param in params.keys():
            paramlist.append(QpalsParameter.QpalsParameter(param, params[param], None, None, None, None, None))
        Module.params = paramlist
        moduleOut = Module.run(show=0)
        if returnstdout:
            return moduleOut
        return params["outFile"]

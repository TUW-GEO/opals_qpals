"""
/***************************************************************************
Name			 	 : qpalsSection
Description          : GUI for opals module "section"
Date                 : 2016-08-29
copyright            : (C) 2016 by Lukas Winiwarter/TU Wien
email                : lukas.winiwarter@tuwien.ac.at
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 """

import os
import tempfile
from xml.dom import minidom

import matplotlib.pyplot as plt
import numpy as np
import ogr
import re
from PyQt4 import QtGui
from PyQt4.QtGui import QColor
from PyQt4.QtGui import QCursor, QBitmap
from qgis.core import *
from qgis.core import QgsMapLayerRegistry
from qgis.gui import *
from qgis.gui import QgsMapLayerComboBox, QgsMapLayerProxyModel

from ..qt_extensions import QpalsDropTextbox
from .. import QpalsShowFile, QpalsModuleBase, QpalsParameter
from QpalsAttributeMan import getAttributeInformation
from matplotlib_section import plotwindow


class QpalsSection:

    def __init__(self, project, layerlist, iface):
        self.advanced_widget = None
        self.simple_widget = None
        self.ls = None
        self.tabs = None
        self.project = project
        self.layerlist = layerlist
        self.iface = iface
        self.visLayer = None
        self.ltool = LineTool(self.iface.mapCanvas(), self.visLayer, secInst=self)
        self.sections = dict()
        self.bm = QBitmap(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'media', 'cursor-cross.png'))

    def createWidget(self):
        self.advanced_widget = QtGui.QDialog()
        self.simple_widget = QtGui.QDialog()
        self.tabs = QtGui.QTabWidget()
        ### SIMPLE ###
        self.ls = QtGui.QFormLayout()
        self.ls.addRow(QtGui.QLabel("Choose input file:"))
        self.txtinfileSimple = QpalsDropTextbox.QpalsDropTextbox(layerlist=self.layerlist, filterrex=".*\.odm$")
        hboxsimple1 = QtGui.QHBoxLayout()
        hboxsimple1.addWidget(self.txtinfileSimple, 1)
        self.txtinfileSimple.textChanged.connect(self.simpleIsLoaded)
        self.ls.addRow(QtGui.QLabel("Input file (odm)"), hboxsimple1)
        self.linetoolBtn = QtGui.QPushButton("Pick section")
        self.linetoolBtn.clicked.connect(self.activateLineTool)
        self.linetoolBtn.setEnabled(False)
        self.ls.addRow(self.linetoolBtn)
        self.runSecBtnSimple = QtGui.QPushButton("Create section")
        self.runSecBtnSimple.clicked.connect(self.ltool.runsec)
        self.runSecBtnSimple.setEnabled(False)
        self.runSecBtnSimple.setStyleSheet("background-color: rgb(50,240,50)")
        self.simpleLineLayer = QgsMapLayerComboBox()
        self.simpleLineLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.simpleLineLayerChk = QtGui.QCheckBox("Visualize (3D) Line Layer:")
        self.ls.addRow(self.simpleLineLayerChk, self.simpleLineLayer)
        self.showSection = QtGui.QCheckBox("Show section")
        self.progress = QtGui.QProgressBar()
        self.showSection.stateChanged.connect(self.checkBoxChanged)
        self.showSection.setCheckState(2)
        self.showSection.setTristate(False)
        self.ls.addRow(self.showSection)
        self.ls.addRow(self.runSecBtnSimple)
        self.ls.addRow(self.progress)
        self.simple_widget.setLayout(self.ls)
        ### ADVANCED ###
        lo = QtGui.QFormLayout()
        ######
        lo.addRow(QtGui.QLabel("Step 1. Choose point cloud and visualize it:"))
        self.txtinfile = QpalsDropTextbox.QpalsDropTextbox(layerlist=self.layerlist)
        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.txtinfile, 1)
        lo.addRow(QtGui.QLabel("Input file (odm)"), hbox1)
        self.runShdBtn = QtGui.QPushButton("Create shading")
        self.runShdBtn.clicked.connect(self.loadShading)
        lo.addRow(self.runShdBtn)
        ######
        self.status = QtGui.QListWidgetItem("hidden status")
        lo.addRow(QtGui.QLabel("Step 2. Create sections"))
        self.secInst = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(self.project.opalspath, "opalsSection.exe"), QpalsProject=self.project)
        self.secInst.load()
        self.secInst.listitem = self.status
        secUi = self.secInst.getParamUi()
        lo.addRow(secUi)

        self.runSecBtn = QtGui.QPushButton("Calculate sections")
        self.runSecBtn.clicked.connect(self.runSection)
        lo.addRow(self.runSecBtn)
        #######
        lo.addRow(QtGui.QLabel("Step 3. Use the Section picking tool to show Sections"))
        self.pickSecBtn = QtGui.QPushButton("Pick section")
        self.pickSecBtn.clicked.connect(self.activateTool)
        lo.addRow(self.pickSecBtn)

        self.advanced_widget.setLayout(lo)
        self.tabs.addTab(self.simple_widget, "Simple")
        self.tabs.addTab(self.advanced_widget, "Advanced")

        return self.tabs

    def close(self):
        if self.ltool.rb:
            self.ltool.canvas.scene().removeItem(self.ltool.rb)
        self.iface.actionPan().trigger()

    def checkBoxChanged(self):
        if self.showSection.checkState() == 2:
            # on
            if self.ltool.rb:
                self.ltool.canvas.scene().addItem(self.ltool.rb)
        else:
            #off
            if self.ltool.rb:
                self.ltool.canvas.scene().removeItem(self.ltool.rb)


    def simpleIsLoaded(self):
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        self.linetoolBtn.setEnabled(False)
        for layer in layers:
            odmpath = layer.customProperty("qpals-odmpath", "")
            if odmpath:
                if self.txtinfileSimple.text() == odmpath:
                    self.linetoolBtn.setEnabled(True)
                    self.visLayer = layer
                    self.ltool.layer = self.visLayer


    def loadShading(self):
        self.runShdBtn.setEnabled(False)
        self.runShdBtn.setText("Calculating shading...")
        showfile = QpalsShowFile.QpalsShowFile(self.project.iface, self.layerlist, self.project)
        showfile.curVisMethod = QpalsShowFile.QpalsShowFile.METHOD_SHADING
        showfile.cellSizeBox = QtGui.QLineEdit("1")
        self.secInst.getParam("inFile").val = self.txtinfile.text()
        self.secInst.getParam("inFile").field.setText(self.txtinfile.text())

        self.visLayer = showfile.load(infile_s=[self.txtinfile.text(), self.txtinfileSimple.text()])
        self.ltool.layer = self.visLayer
        self.runShdBtn.setText("Create shading")
        self.runShdBtn.setEnabled(True)
        self.linetoolBtn.setEnabled(True)


    def runSection(self):
        outParamFileH = tempfile.NamedTemporaryFile(delete=False)
        outParamFile = outParamFileH.name
        outParamFileH.close()
        self.runSecBtn.setEnabled(False)
        self.runSecBtn.setText("Calculating sections...")
        outParamFileParam = QpalsParameter.QpalsParameter('outParamFile', outParamFile, None, None, None, None, None)
        self.secInst.params.append(outParamFileParam)
        self.secInst.run()
        self.secInst.params.remove(outParamFileParam)
        dom = minidom.parse(outParamFile)
        parameters = dom.getElementsByTagName("Parameter")
        outGeoms = []
        for param in parameters:
            if param.attributes["Name"].value == "outGeometry":
                for val in param.getElementsByTagName("Val"):
                    outGeoms.append(val.firstChild.nodeValue) # contains WKT for one section
        dom.unlink()

        self.secLayer = self.iface.addVectorLayer("Polygon?crs=" + self.visLayer.crs().toWkt(), "Sections", "memory")
        pr = self.secLayer.dataProvider()
        featcnt = 1
        for outGeom in outGeoms:
            obj = ogr.CreateGeometryFromWkt(outGeom)
            geometrycnt = obj.GetGeometryCount()
            centersec = obj.GetGeometryRef(0)
            box = obj.GetGeometryRef(1)
            origin = obj.GetGeometryRef(2)
            pointcloud = obj.GetGeometryRef(3)

            feat = QgsFeature(featcnt)
            points = []
            ring = box.GetGeometryRef(0)
            for i in range(ring.GetPointCount()):
                pt = ring.GetPoint(i)
                points.append(QgsPoint(pt[0], pt[1]))
            feat.setGeometry(QgsGeometry.fromPolygon([points]))
            pr.addFeatures([feat])
            self.sections[featcnt] = {'wkt': pointcloud.ExportToWkt(),
                                      'name': origin.GetY()}
            if geometrycnt > 4:
                attrcloud = obj.GetGeometryRef(4)
                self.sections[featcnt]['attr_wkt'] = attrcloud.ExportToWkt()

            featcnt += 1

        self.secLayer.updateExtents()
        self.secLayer.setCustomProperty("qpals-odmpath", "section")
        self.secLayer.setLayerTransparency(50)
        QgsMapLayerRegistry.instance().addMapLayer(self.secLayer)
        self.iface.mapCanvas().refresh()

        self.runSecBtn.setText("Calculate sections")
        self.runSecBtn.setEnabled(True)

    def activateTool(self):
        self.secLayer.removeSelection()
        tool = PointTool(self.iface.mapCanvas(), self.secLayer, self.sections)
        self.iface.mapCanvas().setMapTool(tool)

    def activateLineTool(self):
        c = QCursor(self.bm, self.bm)
        self.iface.mapCanvas().setCursor(c)
        self.iface.mapCanvas().setMapTool(self.ltool)

class LineTool(QgsMapTool):
    def __init__(self, canvas, layer, secInst):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.layer = layer
        self.secInst = secInst
        self.p1 = None
        self.p2 = None
        self.p3 = None
        self.seclength = 0
        self.width = 0
        self.midpoint = None
        self.ab0N = None
        self.rb = None
        self.pltwindow = None
        self.thread = None
        self.worker = None
        self.outParamFile = None
        self.currattr = None
        self.aoi = None
        self.trafo = None
        self.data = {}
        self.mins = {}
        self.maxes = {}
        self.attrs_left = []
        self.count = 0
        self.total = 0

    def canvasPressEvent(self, event):
        pass

    def canvasMoveEvent(self, event):
        if self.rb and not all([self.p1, self.p2, self.p3]):
            self.canvas.scene().removeItem(self.rb)
        if self.p1 and not self.p2:
            self.rb = QgsRubberBand(self.canvas, False)
            points = [self.p1, self.toLayerCoordinates(self.layer,event.pos())]
            self.rb.setToGeometry(QgsGeometry.fromPolyline(points), None)
            self.rb.setColor(QColor(0, 128, 255))
            self.rb.setWidth(1)
        elif self.p1 and self.p2 and not self.p3:
            self.rb = QgsRubberBand(self.canvas, False)
            p0 = self.toLayerCoordinates(self.layer,event.pos())
            x0 = p0.x()
            x1 = self.p1.x()
            x2 = self.p2.x()
            y0 = p0.y()
            y1 = self.p1.y()
            y2 = self.p2.y()
            dist = (abs((y2-y1)*x0 - (x2-x1)*y0 + x2*y1-y2*x1) / np.sqrt((y2-y1)**2 + (x2-x1)**2))


            a = np.array([self.p1.x(), self.p1.y()])
            b = np.array([self.p2.x(), self.p2.y()])
            ab = b-a
            self.seclength = np.linalg.norm(ab)
            self.midpoint = a + ab/2
            self.width = dist / 2
            ab0 = ab/self.seclength
            self.ab0N = np.array([-ab0[1], ab0[0]])

            c1 = a + dist*self.ab0N
            c2 = b + dist*self.ab0N
            c3 = b - dist*self.ab0N
            c4 = a - dist*self.ab0N
            points = [[QgsPoint(c1[0], c1[1]),
                      QgsPoint(c2[0], c2[1]),
                      QgsPoint(c3[0], c3[1]),
                      QgsPoint(c4[0], c4[1])
                      ]]
            self.rb.setToGeometry(QgsGeometry.fromPolygon(points), None)
            self.rb.setColor(QColor(0, 128, 255))
            fc = QColor(0, 128, 255)
            fc.setAlpha(128)
            self.rb.setFillColor(fc)
            self.rb.setWidth(1)
        else:
            pass


    def canvasReleaseEvent(self, event):
        print self.layer
        layerPoint = self.toLayerCoordinates(self.layer, event.pos())
        if self.p1 and not self.p2:
            self.p2 = layerPoint
        elif self.p1 and self.p2 and not self.p3:
            self.p3 = layerPoint
            self.secInst.runSecBtnSimple.setEnabled(True)
        else:
            self.p1 = layerPoint
            self.p2 = None
            self.p3 = None
            self.secInst.runSecBtnSimple.setEnabled(False)
            self.canvas.scene().removeItem(self.rb)

    def update_status(self, message):
        out_lines = [item for item in re.split("[\n\r\b]", message) if item]
        percentage = out_lines[-1]
        # print percentage
        if r"%" in percentage:
            perc = QpalsModuleBase.get_percentage(percentage)
            self.secInst.progress.setValue(int(perc))


    def runsec(self):
        self.currattr = None
        self.aoi = None
        self.trafo = None
        self.data = {}
        self.mins = {}
        self.maxes = {}
        self.attrs_left = []
        self.count = 0
        self.total = 0

        # grab availiable attributes
        attrs, _ = getAttributeInformation(self.secInst.txtinfileSimple.text(), self.secInst.project)
        self.mins = {attr[0]: attr[3] for attr in attrs}
        self.maxes = {attr[0]: attr[4] for attr in attrs}
        self.attrs_left = [attr[0] for attr in attrs]
        self.attrs_left = [self.attrs_left[0]]
        self.total = len(self.attrs_left)
        if self.pltwindow:
            self.pltwindow.ui.deleteLater()

        self.run_next()

    def run_next(self):
        self.count += 1
        outShapeFileH = tempfile.NamedTemporaryFile(suffix=".shp", delete=True)
        outShapeFile = outShapeFileH.name
        outShapeFileH.close()

        self.write_axis_shape(outShapeFile)

        self.currattr = self.attrs_left.pop()
        self.secInst.progress.setFormat("Running opalsSection for attribute %s (%s/%s)..." % (self.currattr,
                                                                                              self.count,
                                                                                              self.total))
        Module = QpalsModuleBase.QpalsModuleBase(
            execName=os.path.join(self.secInst.project.opalspath, "opalsSection.exe"),
            QpalsProject=self.secInst.project)
        infile = QpalsParameter.QpalsParameter('inFile', self.secInst.txtinfileSimple.text(), None, None, None,
                                               None, None)
        axisfile = QpalsParameter.QpalsParameter('axisFile', outShapeFile, None, None, None, None, None)
        attribute = QpalsParameter.QpalsParameter('attribute', self.currattr, None, None, None, None, None)
        thickness = QpalsParameter.QpalsParameter('patchSize', '%s;%s' % (self.seclength, self.width * 4),
                                                  None, None, None, None, None
                                                  )

        outParamFileH = tempfile.NamedTemporaryFile(delete=False)
        self.outParamFile = outParamFileH.name + "x.xml"
        outParamFileH.close()
        outParamFileParam = QpalsParameter.QpalsParameter('outParamFile', self.outParamFile, None, None, None, None,
                                                          None)
        Module.params.append(infile)
        Module.params.append(axisfile)
        Module.params.append(thickness)
        Module.params.append(attribute)
        Module.params.append(outParamFileParam)

        self.thread, self.worker = Module.run_async(status=self.update_status, on_finish=self.parse_output)

    def parse_output(self):
        #read from file and display
        dom = minidom.parse(self.outParamFile)
        parameters = dom.getElementsByTagName("Parameter")
        outGeoms = []
        for param in parameters:
            if param.attributes["Name"].value == "outGeometry":
                for val in param.getElementsByTagName("Val"):
                    outGeoms.append(val.firstChild.nodeValue)  # contains WKT for one section
        dom.unlink()

        if len(outGeoms) > 0:
            geoms = ogr.CreateGeometryFromWkt(outGeoms[0])
            self.trafo = [geoms.GetGeometryRef(0), geoms.GetGeometryRef(2)]
            self.aoi = geoms.GetGeometryRef(1)
            pointcloud = geoms.GetGeometryRef(3)
            xvec = []
            yvec = []
            zvec = []
            cvec = []
            attrcloud = None
            if geoms.GetGeometryCount() > 4:
                attrcloud = geoms.GetGeometryRef(4)
            for i in range(pointcloud.GetGeometryCount()):
                pt = pointcloud.GetGeometryRef(i)
                xvec.append(pt.GetX())
                yvec.append(pt.GetY())
                zvec.append(pt.GetZ())
                if attrcloud:
                    at = attrcloud.GetGeometryRef(i)
                    cvec.append(at.GetZ())

            self.data.update({'X': np.array(xvec),
                              'Y': np.array(yvec),
                              'Z': np.array(zvec),
                              self.currattr: np.array(cvec)})
        if self.attrs_left:
            self.run_next()
        else:
            self.show_pltwindow()

    def show_pltwindow(self):
        self.secInst.progress.setFormat("")
        self.pltwindow = plotwindow(self.secInst.project, self.secInst.iface, self.data, self.mins, self.maxes,
                                    linelayer=None if self.secInst.simpleLineLayerChk.checkState() != 2 else \
                                    self.secInst.simpleLineLayer.currentLayer(),
                                    aoi=self.aoi,
                                    trafo=self.trafo)
        self.secInst.ls.addRow(self.pltwindow.ui)




    def write_axis_shape(self, outShapeFile):
        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source = driver.CreateDataSource(outShapeFile)
        layer = data_source.CreateLayer(outShapeFile[:-4], None, ogr.wkbLineString)
        layer.CreateField(ogr.FieldDefn("ID", ogr.OFTInteger))
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField("ID", 1)
        line = ogr.Geometry(ogr.wkbLineString)
        prevpoint = self.midpoint - self.ab0N * self.width * 2
        line.AddPoint(prevpoint[0], prevpoint[1])
        nextpoint = self.midpoint + self.ab0N * self.width * 2
        line.AddPoint(nextpoint[0], nextpoint[1])
        feature.SetGeometry(line)
        layer.CreateFeature(feature)

    def activate(self):
        pass

    def deactivate(self):
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

class PointTool(QgsMapTool):
    def __init__(self, canvas, layer, sections):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.layer = layer
        self.sections = sections

    def canvasPressEvent(self, event):
        pass

    def canvasMoveEvent(self, event):
        pass

    def canvasReleaseEvent(self, event):
        if self.sections:
            layerPoint = self.toLayerCoordinates(self.layer, event.pos())

            shortestDistance = float("inf")
            closestFeatureId = -1

            # Loop through all features in the layer
            for f in self.layer.getFeatures():
                dist = f.geometry().distance(QgsGeometry.fromPoint(layerPoint))
                if dist < shortestDistance:
                    shortestDistance = dist
                    closestFeatureId = f.id()

            self.layer.select(closestFeatureId)

            # parse wkt
            pointcloud = ogr.CreateGeometryFromWkt(self.sections[closestFeatureId]['wkt'])
            xvec = []
            yvec = []
            zvec = []

            attrcloud = None
            cvec = []

            if 'attr_wkt' in self.sections[closestFeatureId]:
                attrcloud = ogr.CreateGeometryFromWkt(self.sections[closestFeatureId]['attr_wkt'])

            for i in range(pointcloud.GetGeometryCount()):
                pt = pointcloud.GetGeometryRef(i)
                xvec.append(pt.GetX())
                yvec.append(pt.GetY())
                zvec.append(pt.GetZ())
                if attrcloud:
                    at = attrcloud.GetGeometryRef(i)
                    cvec.append(at.GetZ())

            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.view_init(0, 90)
            if attrcloud:
                ax.scatter(x = xvec, y = yvec, z=zvec, c=cvec, cmap='summer')
                ax.colorbar()
            else:
                ax.scatter(xvec, yvec, zvec)
            plt.title("Section %.1f" %self.sections[closestFeatureId]['name'])
            ax.set_xlabel("Distance across axis")
            ax.set_ylabel("Distance along axis")
            ax.set_zlabel("Height")
            plt.show()

    def activate(self):
        pass

    def deactivate(self):
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True
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

from PyQt4 import QtCore, QtGui

from qgis.core import *
from qgis.gui import *

import os, tempfile
from xml.dom import minidom
import matplotlib.pyplot as plt
import ogr

import QpalsShowFile, QpalsModuleBase, QpalsDropTextbox, QpalsParameter

class QpalsSection:

    def __init__(self, project, layerlist, iface):
        self.widget = None
        self.project = project
        self.layerlist = layerlist
        self.iface = iface
        self.sections = dict()

    def createWidget(self):
        self.widget = QtGui.QDialog()
        lo = QtGui.QFormLayout()
        ######
        lo.addRow(QtGui.QLabel("Step 1. Choose point cloud and visualize it:"))
        self.txtinfile = QpalsDropTextbox.QpalsDropTextbox(layerlist=self.layerlist)
        lo.addRow(QtGui.QLabel("Input file (odm)"), self.txtinfile)
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

        self.widget.setLayout(lo)
        return self.widget

    def loadShading(self):
        self.runShdBtn.setEnabled(False)
        self.runShdBtn.setText("Calculating shading...")
        showfile = QpalsShowFile.QpalsShowFile(self.project.iface, self.layerlist, self.project)
        showfile.curVisMethod = QpalsShowFile.QpalsShowFile.METHOD_SHADING
        showfile.cellSizeBox = QtGui.QLineEdit("1")
        showfile.load(infile_s=[self.txtinfile.text()])
        self.runShdBtn.setText("Create shading")
        self.runShdBtn.setEnabled(True)

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

        self.secLayer = self.iface.addVectorLayer("Polygon", "Sections", "memory")
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

            if attrcloud:
                plt.scatter(x = xvec, y = zvec, c = cvec, cmap='summer')
                plt.colorbar()
            else:
                plt.scatter(xvec,zvec)
            plt.title("Section %.1f" %self.sections[closestFeatureId]['name'])
            plt.xlabel("Distance from Axis")
            plt.ylabel("Height")
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
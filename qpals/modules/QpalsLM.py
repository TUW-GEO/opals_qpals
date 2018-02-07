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
from __future__ import absolute_import

from builtins import str
from builtins import range
from builtins import object
import os
import tempfile
from collections import OrderedDict
from xml.dom import minidom

import matplotlib.pyplot as plt
import numpy as np
import ogr
import re
import time
from qgis.PyQt import QtGui, QtCore, QtWidgets
from qgis.PyQt.QtGui import QMouseEvent
from qgis.PyQt.QtWidgets import QDockWidget, QSpinBox
from qgis.PyQt.QtCore import Qt, QEvent
from qgis.core import *
from qgis.core import QgsProject as QgsMapLayerRegistry, QgsPoint, QgsCoordinateTransform, \
    QgsGeometry, QgsFeatureRequest, QgsRectangle, QgsRaster, QgsCoordinateTransformContext
from qgis.gui import *
from qgis.gui import QgsMapTool, QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel

from ..qt_extensions import QpalsDropTextbox
from .. import QpalsModuleBase
from ..qt_extensions.QCollapsibleGroupBox import QCollapsibleGroupBox
from ..QpalsMultiModuleRunner import qpalsMultiModuleRunner as qMMR
from . import findDoubleSegments



def closestpoint(layer, layerPoint):
    # get closest feature
    shortestDistance = float("inf")
    closestFeature = None
    for f in layer.getFeatures():
        if f.geometry():
            dist = f.geometry().distance(layerPoint)
            if dist < shortestDistance:
                shortestDistance = dist
                closestFeature = f

    if closestFeature and closestFeature.geometry():
        # get closest segment
        shortestDistance = float("inf")
        closestPointID = None
        polyline = closestFeature.geometry().asPolyline()
        for i in range(len(polyline)):
            point = polyline[i]
            dist = QgsGeometry.fromPoint(point).distance(layerPoint)
            if dist < shortestDistance:
                shortestDistance = dist
                closestPointID = i

        return (closestPointID, closestFeature)
    else:
        return (None, None)


class QpalsLM(object):
    def __init__(self, project, layerlist, iface):
        self.tabs = None
        self.project = project
        self.layerlist = layerlist
        self.iface = iface
        self.pcfile = None
        self.multirunner = None

    def switchToNextTab(self):
        curridx = self.tabs.currentIndex()
        self.tabs.setCurrentIndex(curridx + 1)
        self.updateTabs()

    def updateTabs(self):
        curridx = self.tabs.currentIndex()
        # update tabs
        infile = self.settings['settings']['inFile'].currentText()

        if self.names[curridx] == "DTM":
            self.pcfile = "pointcloud.odm"
            if infile.endswith(".tif"):
                self.widgets['dtmGrid'].setEnabled(False)
                self.widgets['dtmImp'].setEnabled(True)
                self.modules['dtmImp'].setParam('inFile', infile)
                self.modules['dtmImp'].setParam('tileSize', '120')
                self.modules['dtmShade'].setParam('inFile', infile)
                self.modules['slope'].setParam('inFile', infile)
                self.modules['dtmGrid'].setParam('outFile', infile)
                self.addDtm()
            elif infile.endswith(".odm"):
                self.widgets['dtmGrid'].setEnabled(True)
                self.widgets['dtmImp'].setEnabled(False)
                self.modules['dtmGrid'].setParam('inFile', infile)
                self.pcfile = infile
            else:
                self.widgets['dtmImp'].setEnabled(True)
                self.widgets['dtmGrid'].setEnabled(True)
                self.modules['dtmImp'].setParam('inFile', infile)
                self.modules['dtmGrid'].setParam('inFile', "pointcloud.odm")

            tempf = self.settings['settings']['tempFolder'].currentText()
            if not os.path.isdir(tempf):
                try:
                    os.makedirs(tempf)
                except:
                    tempf = self.project.tempdir
                    self.settings['settings']['tempFolder'].setText(tempf)

            self.project.tempdir = tempf
            self.project.workdir = tempf

        if self.names[curridx] == "3D-Modelling":
            self.modules['lm'].setParam('inFile', self.pcfile)

        if self.names[curridx] != "Editing" or "Editing (3D)":
            if self.section.ltool.rb:
                self.section.ltool.canvas.scene().removeItem(self.section.ltool.rb)
            self.iface.actionPan().trigger()

        if self.names[curridx] == "Export":
            outdir = self.settings['settings']['outFolder'].currentText()
            self.modules['exp'].setParam('outFile', os.path.join(outdir,
                                                                 '3DSTRULI.shp'))
            if not os.path.isdir(outdir) and outdir:
                os.makedirs(outdir)

    def close(self):
        if self.section.ltool.rb:
            self.section.ltool.canvas.scene().removeItem(self.section.ltool.rb)
        self.iface.actionPan().trigger()

    def switchToPrevTab(self):
        curridx = self.tabs.currentIndex()
        self.tabs.setCurrentIndex(curridx - 1)

    def snapToDtm(self):
        player = self.edit3d_pointlayerbox.currentLayer()
        llayer = self.edit3d_linelayerbox.currentLayer()
        rlayer = self.edit3d_dtmlayerbox.currentLayer()
        llayer.startEditing()
        points = list(player.getFeatures())
        pointid = self.edit3d_currPointId.value()
        if points:
            point = points[pointid]
            pointGeom = point.geometry()
            if pointGeom.asMultiPoint():
                pointGeom = pointGeom.asMultiPoint()[0]
            else:
                pointGeom = pointGeom.asPoint()
            pid, feat = closestpoint(llayer, QgsGeometry.fromPoint(pointGeom))
            linegeom = feat.geometry().asWkb().data()
            olinegeom = ogr.CreateGeometryFromWkb(linegeom)
            dx = rlayer.rasterUnitsPerPixelX()
            dy = rlayer.rasterUnitsPerPixelY()
            xpos = pointGeom.x()
            ypos = pointGeom.y()
            # assume pixel = center
            xll = rlayer.extent().xMinimum() + 0.5*dx
            yll = rlayer.extent().yMinimum() + 0.5*dy
            xoffs = (pointGeom.x()-xll) % dx
            yoffs = (pointGeom.y()-yll) % dy
            dtm_val_ll = rlayer.dataProvider().identify(QgsPoint(xpos-dx/2, ypos-dy/2), QgsRaster.IdentifyFormatValue).results()[1]
            dtm_val_ur = rlayer.dataProvider().identify(QgsPoint(xpos+dx/2, ypos+dy/2), QgsRaster.IdentifyFormatValue).results()[1]
            dtm_val_lr = rlayer.dataProvider().identify(QgsPoint(xpos+dx/2, ypos-dy/2), QgsRaster.IdentifyFormatValue).results()[1]
            dtm_val_ul = rlayer.dataProvider().identify(QgsPoint(xpos-dx/2, ypos+dy/2), QgsRaster.IdentifyFormatValue).results()[1]
            a00 = dtm_val_ll
            a10 = dtm_val_lr - dtm_val_ll
            a01 = dtm_val_ul - dtm_val_ll
            a11 = dtm_val_ur + dtm_val_ll - (dtm_val_lr+dtm_val_ul)
            dtm_bilinear = a00 + a10*xoffs + a01*yoffs + a11*xoffs*yoffs
            x, y = olinegeom.GetPoint_2D(pid)
            olinegeom.SetPoint(pid, x,y,dtm_bilinear)
            llayer.beginEditCommand("Snap point height to DTM")
            updatedGeom = QgsGeometry()
            updatedGeom.fromWkb(olinegeom.ExportToWkb())
            llayer.dataProvider().changeGeometryValues({feat.id(): updatedGeom})
            llayer.endEditCommand()
            # refresh vertex editor
            self.showProblemPoint()


    def removeNode(self):
        player = self.edit3d_pointlayerbox.currentLayer()
        llayer = self.edit3d_linelayerbox.currentLayer()
        llayer.startEditing()
        points = list(player.getFeatures())
        pointid = self.edit3d_currPointId.value()
        if points:
            point = points[pointid]
            pointGeom = point.geometry()
            pid, feat = closestpoint(llayer, pointGeom)
            llayer.beginEditCommand("Vertex removed")
            llayer.deleteVertex(feat.id(), pid)
            llayer.endEditCommand()


    def nextProblemPoint(self):
        pointid = self.edit3d_currPointId.value()
        self.edit3d_currPointId.setValue(pointid+1)

    def showProblemPoint(self):
        player = self.edit3d_pointlayerbox.currentLayer()
        llayer = self.edit3d_linelayerbox.currentLayer()
        self.iface.setActiveLayer(llayer)

        mc = self.iface.mapCanvas()
        # get first layer
        #llayer.startEditing()
        #self.iface.actionVertexTool().trigger()

        # get point position
        points = list(player.getFeatures())
        pointid = self.edit3d_currPointId.value()
        if points:
            point = points[pointid]
            pointGeom = point.geometry().asMultiPoint()[0] if point.geometry().asMultiPoint() else point.geometry().asPoint()

            t = QgsCoordinateTransform(llayer.crs(), mc.mapSettings().destinationCrs(), QgsCoordinateTransformContext())
            tCenter = t.transform(pointGeom)
            rect = QgsRectangle(tCenter, tCenter)
            mc.setExtent(rect)
            #pos = QgsMapTool(self.iface.mapCanvas()).toCanvasCoordinates(tCenter)
            #click = QMouseEvent(QEvent.MouseButtonPress, pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
            #mc.mousePressEvent(click)
            #mc.mousePressEvent(click)
            mc.refresh()
            #vertexDock = \
            #    [ch for ch in self.iface.mainWindow().findChildren(QDockWidget, "") if
            #     ch.windowTitle() == u'Vertex Editor']
            #if vertexDock:
            #    vertexDock = vertexDock[0]
            #    self.editingls.addWidget(vertexDock)
            mc.refresh()

    def nodeLayerChanged(self):
        if self.edit3d_pointlayerbox.currentLayer():
            self.selectNodeBtn.setText("Next point")
            self.selectNodeBtn.setEnabled(True)
            cnt = self.edit3d_pointlayerbox.currentLayer().featureCount() - 1
            self.edit3d_countLabel.setText(str(cnt))
            self.edit3d_currPointId.setMaximum(cnt)

    def createWidget(self):
        self.scrollwidget = QtWidgets.QScrollArea()
        self.scrollwidget.setWidgetResizable(True)
        self.tabs = QtWidgets.QTabWidget()
        self.scrollwidget.setWidget(self.tabs)
        self.names = ['Settings',
                 'DTM',
                 'Slope',
                 '2D-Approximation',
                 'Topologic correction',
                 'Editing',
                 '3D-Modelling',
                 'Editing (3D)',
                 'Export']
        self.widgets = {}
        self.settings = {}
        self.modules = {}

        for idx, name in enumerate(self.names):
            self.widgets[name] = QtWidgets.QDialog()
            ls = QtWidgets.QFormLayout()
            # Tab-specific options
            if name == "Settings":
                desc = QtWidgets.QLabel("Welcome to the qpals LineModeler GUI! \nThis tool will help you to detect and "
                                    "model breaklines based on a DTM and/or a point cloud using the opals module "
                                    "opalsLineModeler.\nThe process includes manual editing in QGIS (\"Editing\") "
                                    "as well as automatic dectection and modelling.\n\n"
                                    "To begin, please enter some basic information.")
                desc.setWordWrap(True)
                ls.addRow(desc)
                boxRun = QtWidgets.QGroupBox("Run multiple steps automatically:")
                boxVL = QtWidgets.QVBoxLayout()
                boxRun.setLayout(boxVL)
                self.settings['settings'] = OrderedDict([
                    ('name', QtWidgets.QLineEdit()),
                    ('inFile', QpalsDropTextbox.QpalsDropTextbox(layerlist=self.layerlist)),
                    ('tempFolder', QpalsDropTextbox.QpalsDropTextbox()),
                    ('outFolder', QpalsDropTextbox.QpalsDropTextbox()),
                    ('chkDTM', QtWidgets.QCheckBox("DTM")),
                    ('chkSlope', QtWidgets.QCheckBox("Slope")),
                    ('chk2D', QtWidgets.QCheckBox("2D-Approximation")),
                    ('chktopo2D', QtWidgets.QCheckBox("Topological correction")),
                    ('chkEditing2d', QtWidgets.QLabel("--- Manual editing of 2D-Approximations ---")),
                    ('chk3Dmodel', QtWidgets.QCheckBox("3D-Modelling")),
                    ('chkEditing3d', QtWidgets.QLabel("--- Manual editing of 3D-Lines ---")),
                    ('chkExport', QtWidgets.QCheckBox("Export")),
                ]
                )
                for key, value in list(self.settings['settings'].items()):
                    if isinstance(value, QpalsDropTextbox.QpalsDropTextbox):
                        value.setMinimumContentsLength(20)
                        value.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLength)
                    if key.startswith("chk"):
                        boxVL.addWidget(value)

                ls.addRow(QtWidgets.QLabel("Project name"), self.settings['settings']['name'])
                hbox_wrap = QtWidgets.QHBoxLayout()
                hbox_wrap.addWidget(self.settings['settings']['inFile'], stretch=1)
                ls.addRow(QtWidgets.QLabel("Input file (TIFF/LAS/ODM)"), hbox_wrap)
                hbox_wrap = QtWidgets.QHBoxLayout()
                hbox_wrap.addWidget(self.settings['settings']['tempFolder'], stretch=1)
                self.settings['settings']['tempFolder'].setPlaceholderText(
                    "drop folder here (will be created if not exists)")
                ls.addRow(QtWidgets.QLabel("Folder for temporary files"), hbox_wrap)
                hbox_wrap = QtWidgets.QHBoxLayout()
                self.settings['settings']['outFolder'].setPlaceholderText(
                    "drop folder here (will be created if not exists)")
                hbox_wrap.addWidget(self.settings['settings']['outFolder'], stretch=1)
                ls.addRow(QtWidgets.QLabel("Folder for output files"), hbox_wrap)
                ls.addRow(QtWidgets.QLabel(""))
                boxBtnRun = QtWidgets.QPushButton("Run selected steps now")
                boxBtnRun.clicked.connect(lambda: self.run_step("all"))
                boxBtnExp = QtWidgets.QPushButton("Export selected steps to .bat")
                boxBtnExp.clicked.connect(self.createBatFile)
                # saveBtn = QtWidgets.QPushButton("Save to project file")
                # saveBtn.clicked.connect(self.save)
                boxVL.addWidget(boxBtnRun)
                boxVL.addWidget(boxBtnExp)
                # boxVL.addWidget(saveBtn)
                ls.addRow(boxRun)

            if name == "DTM":
                desc = QtWidgets.QLabel(
                    "This first step will create a digital terrain model (DTM) from your point cloud data. "
                    "Also, a shading of your DTM "
                    "will be created for visualisation purposes. If the input file is not an ODM, one has to be "
                    "created for the modelling process later on.")
                desc.setWordWrap(True)
                ls.addRow(desc)

                impmod, impscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsImport",
                                                                                   "opalsImport",
                                                                                   self.project,
                                                                                   {'outFile': 'pointcloud.odm'},
                                                                                   ["inFile",
                                                                                    "outFile"])
                self.modules['dtmImp'] = impmod
                self.widgets['dtmImp'] = impscroll
                ls.addRow(impscroll)

                dtmmod, dtmscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsGrid",
                                                                                   "opalsGrid",
                                                                                   self.project,
                                                                                   {'interpolation': 'movingPlanes',
                                                                                    'gridSize': '1',
                                                                                    'outFile': 'DTM_1m.tif'},
                                                                                   ["inFile",
                                                                                    "outFile",
                                                                                    "neighbours",
                                                                                    "searchRadius",
                                                                                    "interpolation"])
                self.modules['dtmGrid'] = dtmmod
                self.widgets['dtmGrid'] = dtmscroll
                dtmmod.afterRun = self.addDtm
                ls.addRow(dtmscroll)

                shdmod, shdscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsShade",
                                                                                   "opalsShade",
                                                                                   self.project,
                                                                                   {'inFile': 'DTM_1m.tif',
                                                                                    'outFile': 'DTM_1m_shd.tif'},
                                                                                   ["inFile",
                                                                                    "outFile", ])
                self.modules['dtmShade'] = shdmod
                shdmod.afterRun = self.addShd
                ls.addRow(shdscroll)

            if name == "Slope":
                desc = QtWidgets.QLabel(
                    "To automatically detect breaklines, a slope map is calculated. This map uses the neighboring 9"
                    " pixels to estimate a plane. The gradient (steepest slope) is then taken, converted to a slope"
                    "in degrees, and assigned to the pixel.")
                desc.setWordWrap(True)
                ls.addRow(desc)

                gfmod, gfscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsGridFeature",
                                                                                 "opalsGridFeature",
                                                                                 self.project,
                                                                                 {'feature': 'slpDeg',
                                                                                  'inFile': 'DTM_1m.tif',
                                                                                  'outFile': 'DTM_1m_slope.tif'},
                                                                                 ["inFile",
                                                                                  "outFile",
                                                                                  "feature"])
                self.modules['slope'] = gfmod
                ls.addRow(gfscroll)

            if name == "2D-Approximation":
                desc = QtWidgets.QLabel(
                    "The slope map is used to detect breaklines. For this, the algorithm by Canny (1986) is used.\n"
                    "First, the slope map is convoluted with a gaussian kernel for smoothing, then the derivative "
                    "is calculated. The two threshold parameters represent the upper and lower values for the "
                    "binarization of the derivative map. Edges that have at least one pixel > upper threshold will be "
                    "followed until they have a pixel < lower threshold.")
                desc.setWordWrap(True)
                ls.addRow(desc)

                edgeDmod, edgeDscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsEdgeDetect",
                                                                                       "opalsEdgeDetect",
                                                                                       self.project,
                                                                                       {'threshold': '2;4',
                                                                                        'sigmaSmooth': '1.8',
                                                                                        'inFile': 'DTM_1m_slope_slpDeg.tif',
                                                                                        'outFile': 'detected_edges.tif'},
                                                                                       ["inFile",
                                                                                        "outFile",
                                                                                        "threshold",
                                                                                        "sigmaSmooth"])
                self.modules['edgeDetect'] = edgeDmod
                ls.addRow(edgeDscroll)

                desc = QtWidgets.QLabel("Since the output of opalsEdgeDetect is still a raster, we need to vectorize it:")
                desc.setWordWrap(True)
                ls.addRow(desc)

                vecmod, vecscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsVectorize",
                                                                                   "opalsVectorize",
                                                                                   self.project,
                                                                                   {'inFile': 'detected_edges.tif',
                                                                                    'outFile': 'detected_edges.shp'},
                                                                                   ["inFile",
                                                                                    "outFile"
                                                                                    ])
                self.modules['vectorize'] = vecmod
                ls.addRow(vecscroll)

            if name == "Topologic correction":
                desc = QtWidgets.QLabel(
                    "Vectorized binary rasters usually need some topological cleaning. Here, this is done in three steps: \n"
                    "1) Find the longest line and remove all lines < 10m\n"
                    "2) Merge lines iteratively\n"
                    "3) Clean up")
                desc.setWordWrap(True)
                ls.addRow(desc)

                lt1mod, lt1scroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsLineTopology",
                                                                                   "opalsLineTopology (1)",
                                                                                   self.project,
                                                                                   {'method': 'longest',
                                                                                    'minLength': '10',
                                                                                    'snapRadius': '0',
                                                                                    'maxTol': '0.5',
                                                                                    'maxAngleDev': '75;15',
                                                                                    'avgDist': '3',
                                                                                    'inFile': 'detected_edges.shp',
                                                                                    'outFile': 'edges1.shp'},
                                                                                   ["inFile",
                                                                                    "outFile",
                                                                                    "method",
                                                                                    "minLength",
                                                                                    "maxTol"])
                self.modules['lt1'] = lt1mod
                ls.addRow(lt1scroll)

                lt2mod, lt2scroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsLineTopology",
                                                                                   "opalsLineTopology (2)",
                                                                                   self.project,
                                                                                   {'method': 'merge',
                                                                                    'minLength': '10',
                                                                                    'snapRadius': '3',
                                                                                    'maxTol': '0',
                                                                                    'maxAngleDev': '150;15',
                                                                                    'avgDist': '3',
                                                                                    'merge.minWeight': '0.75',
                                                                                    'merge.relWeightLead': '0',
                                                                                    'merge.maxIter': '10',
                                                                                    'merge.revertDist': '5',
                                                                                    'merge.revertInterval': '1',
                                                                                    'merge.searchGeneration': '4',
                                                                                    'merge.preventIntersection': '1',
                                                                                    'inFile': 'edges1.shp',
                                                                                    'outFile': 'edges2.shp'},
                                                                                   ["inFile",
                                                                                    "outFile",
                                                                                    "method",
                                                                                    "maxAngleDev",
                                                                                    "snapRadius",
                                                                                    "merge\..*"])
                lt2scroll.setFixedHeight(lt2scroll.height() - 200)
                self.modules['lt2'] = lt2mod
                ls.addRow(lt2scroll)

                lt3mod, lt3scroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsLineTopology",
                                                                                   "opalsLineTopology (3)",
                                                                                   self.project,
                                                                                   {'method': 'longest',
                                                                                    'minLength': '25',
                                                                                    'snapRadius': '0',
                                                                                    'maxTol': '0',
                                                                                    'maxAngleDev': '90;15',
                                                                                    'avgDist': '3',
                                                                                    'inFile': 'edges2.shp',
                                                                                    'outFile': 'edges3.shp'
                                                                                    },
                                                                                   ["inFile",
                                                                                    "outFile",
                                                                                    "method",
                                                                                    "minLength",
                                                                                    "maxTol"])
                self.modules['lt3'] = lt3mod
                ls.addRow(lt3scroll)
                lt3mod.afterRun = self.add2DLines

            if name == "Editing":
                desc = QtWidgets.QLabel(
                    "Please start editing the 2D approximations that have been loaded into qgis. Here are some tools "
                    "that might help:")
                desc.setWordWrap(True)
                ls.addRow(desc)

                box1 = QtWidgets.QGroupBox("QuickLineModeller")
                from . import QpalsQuickLM
                self.quicklm = QpalsQuickLM.QpalsQuickLM(project=self.project, layerlist=self.layerlist,
                                                         iface=self.iface)
                box1.setLayout(self.quicklm.fl)
                ls.addRow(box1)
                box2 = QtWidgets.QGroupBox("qpalsSection")
                from . import QpalsSection
                self.section = QpalsSection.QpalsSection(project=self.project, layerlist=self.layerlist,
                                                         iface=self.iface)
                self.section.createWidget()
                box2.setLayout(self.section.ls)
                ls.addRow(box2)

            if name == "3D-Modelling":
                desc = QtWidgets.QLabel(
                    "The 2D approximations can now be used to model 3D breaklines in the pointcloud/the DTM.")
                desc.setWordWrap(True)
                ls.addRow(desc)

                lmmod, lmscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsLineModeler",
                                                                                 "opalsLineModeler",
                                                                                 self.project,
                                                                                 {#"filter": "Class[Ground]",
                                                                                  "approxFile": "edges3.shp",
                                                                                  "outFile": "modelled_lines.shp"},
                                                                                 ["inFile",
                                                                                  "approxFile",
                                                                                  "outFile",
                                                                                  "filter",
                                                                                  "patchLength",
                                                                                  "patchWidth",
                                                                                  "overlap",
                                                                                  "angle",
                                                                                  "minLength",
                                                                                  "pointCount",
                                                                                  "sigmaApriori"])
                self.modules['lm'] = lmmod
                ls.addRow(lmscroll)

                lmmod.afterRun = self.add3DLines

            if name == "Editing (3D)":
                desc = QtWidgets.QLabel("Before exporting the final product, there are a few tools to check the "
                                    "quality of the result. This includes a topological check as well as a search"
                                    "for points that have a big height difference to the DTM - and might be erraneous.")

                desc.setWordWrap(True)
                ls.addRow(desc)

                self.startQualityCheckBtn = QtWidgets.QPushButton("Start calculation")
                self.startQualityCheckBtn.clicked.connect(self.runProblemSearchAsync)
                self.QualityCheckbar = QtWidgets.QProgressBar()
                self.QualityCheckDtm = QgsMapLayerComboBox()
                self.QualityCheckDtm.setFilters(QgsMapLayerProxyModel.RasterLayer)
                self.QualityCheckThreshold = QtWidgets.QLineEdit("0.5")
                ls.addRow(QtWidgets.QLabel("DTM Layer to compare heights with"), self.QualityCheckDtm)
                ls.addRow(QtWidgets.QLabel("Set height difference threshold [m]"), self.QualityCheckThreshold)
                hb = QtWidgets.QHBoxLayout()
                hb.addWidget(self.QualityCheckbar)
                hb.addWidget(self.startQualityCheckBtn)
                ls.addRow(hb)
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.HLine)
                line.setFrameShadow(QtWidgets.QFrame.Sunken)
                ls.addRow(line)

                self.editingls = ls

                self.edit3d_linelayerbox = QgsMapLayerComboBox()
                self.edit3d_linelayerbox.setFilters(QgsMapLayerProxyModel.LineLayer)
                self.edit3d_pointlayerbox = QgsMapLayerComboBox()
                self.edit3d_pointlayerbox.setFilters(QgsMapLayerProxyModel.PointLayer)
                self.edit3d_dtmlayerbox = QgsMapLayerComboBox()
                self.edit3d_dtmlayerbox.setFilters(QgsMapLayerProxyModel.RasterLayer)
                self.edit3d_pointlayerbox.currentIndexChanged.connect(self.nodeLayerChanged)


                self.edit3d_currPointId = QSpinBox()
                self.edit3d_currPointId.setMinimum(0)
                self.edit3d_currPointId.valueChanged.connect(self.showProblemPoint)

                ls.addRow("Select Line Layer:", self.edit3d_linelayerbox)
                ls.addRow("Select Problem Point layer:", self.edit3d_pointlayerbox)

                self.selectNodeBtn = QtWidgets.QPushButton("Next point")
                self.selectNodeBtn.clicked.connect(lambda: self.edit3d_currPointId.setValue(
                    self.edit3d_currPointId.value()+1))

                self.selectPrevNodeBtn = QtWidgets.QPushButton("Prev point")
                self.selectPrevNodeBtn.clicked.connect(lambda: self.edit3d_currPointId.setValue(
                    self.edit3d_currPointId.value()-1))
                self.edit3d_countLabel = QtWidgets.QLabel()

                self.snapToDtmBtn = QtWidgets.QPushButton("Snap to:")
                self.snapToDtmBtn.clicked.connect(self.snapToDtm)
                self.remonveNodeBtn = QtWidgets.QPushButton("Remove")
                self.remonveNodeBtn.clicked.connect(self.removeNode)

                nextBox = QtWidgets.QHBoxLayout()
                nextBox.addWidget(QtWidgets.QLabel("Current point:"))
                nextBox.addWidget(self.edit3d_currPointId)
                nextBox.addWidget(QtWidgets.QLabel("/"))
                nextBox.addWidget(self.edit3d_countLabel)
                nextBox.addStretch()

                nextBox.addWidget(self.snapToDtmBtn)
                nextBox.addWidget(self.edit3d_dtmlayerbox)
                nextBox.addWidget(self.remonveNodeBtn)
                nextBox.addWidget(self.selectPrevNodeBtn)
                nextBox.addWidget(self.selectNodeBtn)

                ls.addRow(nextBox)
                self.nodeLayerChanged()

            if name == "Export":
                exp2mod, exp2scroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsTranslate",
                                                                                     "opalsTranslate",
                                                                                     self.project,
                                                                                     {'oformat': 'shp',
                                                                                      'inFile': 'modelled_lines.shp',
                                                                                     'outFile': 'STRULI3D.shp',
                                                                                      },
                                                                                     ["inFile",
                                                                                      "outFile"])

                self.modules['exp'] = exp2mod
                ls.addRow(exp2scroll)

            vl = QtWidgets.QVBoxLayout()
            vl.addLayout(ls, 1)
            navbar = QtWidgets.QHBoxLayout()
            next = QtWidgets.QPushButton("Next step >")
            next.clicked.connect(self.switchToNextTab)
            prev = QtWidgets.QPushButton("< Previous step")
            prev.clicked.connect(self.switchToPrevTab)
            runcurr = QtWidgets.QPushButton("Run this step (all modules above)")
            runcurr.clicked.connect(lambda: self.run_step(None))
            if idx > 0:
                navbar.addWidget(prev)
            navbar.addStretch()
            if name in ["DTM",
                        "Slope",
                        "2D-Approximation",
                        "Topologic correction",
                        "3D-Modelling",
                        "Export"]:
                navbar.addWidget(runcurr)
            navbar.addStretch()
            if idx < len(self.names):
                navbar.addWidget(next)
            vl.addLayout(navbar)
            self.widgets[name].setLayout(vl)
            self.tabs.addTab(self.widgets[name], name)

        # set up connections

        self.tabs.currentChanged.connect(self.updateTabs)
        return self.scrollwidget

    def run_step(self, step_name=None):
        curridx = self.tabs.currentIndex()
        if step_name is None:
            step_name = self.names[curridx]

        modules = self.get_step_modules(step_name=step_name)

        self.multirunner = qMMR()
        for mod in modules:
            self.multirunner.add_module(mod, mod.updateBar, mod.run_async_finished, mod.errorBar)
        self.multirunner.start()

    def get_step_modules(self, step_name=None):
        steps_modules = {
            "DTM": [self.modules['dtmImp'], self.modules['dtmGrid'], self.modules['dtmShade']],
            "Slope": [self.modules['slope']],
            "2D-Approximation": [self.modules['edgeDetect'], self.modules['vectorize']],
            "Topologic correction": [self.modules['lt1'], self.modules['lt2'], self.modules['lt3']],
            "3D-Modelling": [self.modules['lm']],
            "Export": [self.modules['exp']]
        }
        if step_name == "all":
            modules = []
            if self.settings['settings']['chkDTM'].isChecked():
                modules += steps_modules["DTM"]
            if self.settings['settings']['chkSlope'].isChecked():
                modules += steps_modules["Slope"]
            if self.settings['settings']['chk2D'].isChecked():
                modules += steps_modules["2D-Approximation"]
            if self.settings['settings']['chktopo2D'].isChecked():
                modules += steps_modules["Topologic correction"]
            if self.settings['settings']['chk3Dmodel'].isChecked():
                modules += steps_modules["3D-Modelling"]
            if self.settings['settings']['chkExport'].isChecked():
                modules += steps_modules["Export"]
        else:
            modules = steps_modules[step_name]
        return modules

    def createBatFile(self):
        saveTo = QtWidgets.QFileDialog.getSaveFileName(None, caption='Save to file')
        try:
            f = open(saveTo, 'w')
            f.write("rem BATCH FILE CREATED WITH QPALS\r\n")
            modules = self.get_step_modules("all")
            for module in modules:
                f.write(str(module) + "\r\n")
            f.close()
        except Exception as e:
            raise Exception("Saving to batch failed.", e)

    def updateBar(self, message):
        out_lines = [item for item in re.split("[\n\r\b]", message) if item]
        percentage = out_lines[-1]
        # print percentage
        if r"%" in percentage:
            perc = QpalsModuleBase.get_percentage(percentage)
            self.secInst.progress.setValue(int(perc))

    def addDtm(self):
        file = self.modules['dtmGrid'].getParam('outFile').val
        if not os.path.isabs(file):
            file = os.path.join(self.project.workdir, file)
        self.iface.addRasterLayer(file, "DTM")

    def addShd(self):
        file = self.modules['dtmShade'].getParam('outFile').val
        if not os.path.isabs(file):
            file = os.path.join(self.project.workdir, file)
        self.iface.addRasterLayer(file, "DTM-Shading")

    def add2DLines(self):
        file = self.modules['lt3'].getParam('outFile').val
        if not os.path.isabs(file):
            file = os.path.join(self.project.workdir, file)
        self.iface.addVectorLayer(file, "2D-Approximations", "ogr")

    def add3DLines(self):
        file = self.modules['lm'].getParam('outFile').val
        if not os.path.isabs(file):
            file = os.path.join(self.project.workdir, file)
        self.iface.addVectorLayer(file, "3D Modelled Lines", "ogr")

    def runProblemSearchAsync(self):
        linefile = self.modules['lm'].getParam('outFile').val
        if not os.path.isabs(linefile):
            linefile = os.path.join(self.project.workdir, linefile)
        dtm = self.QualityCheckDtm.currentLayer()
        dtm_thres = self.QualityCheckThreshold.text()
        try:
            dtm_thres = float(dtm_thres)
        except:
            dtm_thres = 0
        self.QualityWorker = findDoubleSegments.RunWorker(linefile, os.path.join(self.project.workdir, "quality"),
                                                          dtm,dtm_thres,
                                                          50, 1000)
        self.QualityWorker.progress.connect(self.updateQualityBar)
        self.QualityWorker.finished.connect(self.QualityFinished)
        self.QualityWorker.error.connect(self.problemSearchError)
        self.QualityThread = QtCore.QThread()
        self.QualityWorker.moveToThread(self.QualityThread)
        self.QualityThread.started.connect(self.QualityWorker.run)
        self.QualityThread.start()
        self.startQualityCheckBtn.setEnabled(False)
        self.startQualityCheckBtn.setText("processing...")

    def problemSearchError(self, err):
        (msg, e, mod) = err
        print(msg)

    def updateQualityBar(self, fl):
        self.QualityCheckbar.setValue(fl)

    def QualityFinished(self):
        self.startQualityCheckBtn.setEnabled(True)
        self.startQualityCheckBtn.setText("Start calculation")
        self.updateQualityBar(100)
        file = os.path.join(self.project.workdir, "quality", "problems.shp")
        self.iface.addVectorLayer(file, "Problems", "ogr")

    # def save(self):
    #     import cPickle
    #     proj = QgsProject.instance()
    #     tabs = cPickle.dumps(self.tabs, -1)
    #     proj.writeEntry("qpals", "linemodelerinst", tabs)
    #     print tabs


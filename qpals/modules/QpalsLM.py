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
from collections import OrderedDict
from xml.dom import minidom

import matplotlib.pyplot as plt
import numpy as np
import ogr
from PyQt4 import QtGui
from qgis.core import *
from qgis.core import QgsMapLayerRegistry
from qgis.gui import *

from ..qt_extensions import QpalsDropTextbox
from .. import QpalsModuleBase
from ..qt_extensions.QCollapsibleGroupBox import QCollapsibleGroupBox


def switchToNextTab(tabWidget):
    curridx = tabWidget.currentIndex()
    tabWidget.setCurrentIndex(curridx+1)
def switchToPrevTab(tabWidget):
    curridx = tabWidget.currentIndex()
    tabWidget.setCurrentIndex(curridx-1)

class QpalsLM:

    def __init__(self, project, layerlist, iface):
        self.tabs = None
        self.project = project
        self.layerlist = layerlist
        self.iface = iface

    def createWidget(self):
        self.tabs = QtGui.QTabWidget()
        names = ['Settings',
                 'DTM',
                 'Slope',
                 '2D-Approximation',
                 'Topologic correction',
                 'Editing',
                 '3D-Modelling',
                 'Topologic correction (3D)',
                 'Quality check',
                 'Export']
        self.widgets = {}
        self.settings = {}
        self.modules = {}

        for idx, name in enumerate(names):
            self.widgets[name] = QtGui.QDialog()
            ls = QtGui.QFormLayout()
            # Tab-specific options
            if name == "Settings":
                desc = QtGui.QLabel("Welcome to the qpals LineModeler GUI! \nThis tool will help you to detect and "
                                    "model breaklines based on a DTM and/or a point cloud using the opals module "
                                    "opalsLineModeler.\nThe process includes manual editing in QGIS (\"Editing\") "
                                    "as well as automatic dectection and modelling.\n\n"
                                    "To begin, please enter some basic information.")
                desc.setWordWrap(True)
                ls.addRow(desc)
                boxRun = QtGui.QGroupBox("Run multiple steps automatically:")
                boxVL = QtGui.QVBoxLayout()
                boxRun.setLayout(boxVL)
                self.settings['settings'] = OrderedDict([
                    ('name', QtGui.QLineEdit()),
                    ('inFile', QpalsDropTextbox.QpalsDropTextbox(layerlist=self.layerlist)),
                    ('tempFolder', QpalsDropTextbox.QpalsDropTextbox()),
                    ('outFolder', QpalsDropTextbox.QpalsDropTextbox()),
                    ('chkDTM', QtGui.QCheckBox("DTM")),
                    ('chkSlope', QtGui.QCheckBox("Slope")),
                    ('chk2D', QtGui.QCheckBox("2D-Approximation")),
                    ('chktopo2D', QtGui.QCheckBox("Topological correction")),
                    ('chkEditing', QtGui.QLabel("--- Manual editing of 2D-Approximations ---")),
                    ('chk3Dmodel', QtGui.QCheckBox("3D-Modelling")),
                    ('chk3Dquality', QtGui.QCheckBox("Quality check")),
                    ('chkExport', QtGui.QCheckBox("Export")),
                ]
                )
                for key, value in self.settings['settings'].items():
                    if isinstance(value, QpalsDropTextbox.QpalsDropTextbox):
                        value.setMinimumContentsLength(20)
                        value.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
                    if key.startswith("chk"):
                        boxVL.addWidget(value)

                ls.addRow(QtGui.QLabel("Project name"), self.settings['settings']['name'])
                hbox_wrap = QtGui.QHBoxLayout()
                hbox_wrap.addWidget(self.settings['settings']['inFile'], stretch=1)
                ls.addRow(QtGui.QLabel("Input file (TIFF/LAS/ODM)"), hbox_wrap)
                hbox_wrap = QtGui.QHBoxLayout()
                hbox_wrap.addWidget(self.settings['settings']['tempFolder'], stretch=1)
                self.settings['settings']['tempFolder'].setPlaceholderText("drop folder here (will be created if not exists)")
                ls.addRow(QtGui.QLabel("Folder for temporary files"), hbox_wrap)
                hbox_wrap = QtGui.QHBoxLayout()
                self.settings['settings']['outFolder'].setPlaceholderText("drop folder here (will be created if not exists)")
                hbox_wrap.addWidget(self.settings['settings']['outFolder'], stretch=1)
                ls.addRow(QtGui.QLabel("Folder for output files"), hbox_wrap)
                ls.addRow(QtGui.QLabel(""))
                boxBtnRun = QtGui.QPushButton("Run selected steps now")
                boxBtnExp = QtGui.QPushButton("Export selected steps to .bat")
                boxVL.addWidget(boxBtnRun)
                boxVL.addWidget(boxBtnExp)
                ls.addRow(boxRun)

            if name == "DTM":
                desc = QtGui.QLabel("This first step will create a digital terrain model (DTM) from your point cloud data. "
                                    "If you have a DTM to begin with, you can skip this step. Also, a shading of your DTM "
                                    "will be created for visualisation purposes.")
                desc.setWordWrap(True)
                ls.addRow(desc)

                dtmmod, dtmscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsGrid",
                                                                                   "opalsGrid",
                                                                                   self.project,
                                                                                   {'interpolation': 'movingPlanes',
                                                                                    'gridSize': '1'},
                                                                                   ["inFile",
                                                                                    "outFile",
                                                                                    "neighbours",
                                                                                    "searchRadius",
                                                                                    "interpolation"])
                self.modules['dtmGrid'] = dtmmod
                ls.addRow(dtmscroll)

                shdmod, shdscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsShade",
                                                                                   "opalsShade",
                                                                                   self.project,
                                                                                   {},
                                                                                   ["inFile",
                                                                                    "outFile",])
                self.modules['dtmShade'] = shdmod
                ls.addRow(shdscroll)

            if name == "Slope":
                desc = QtGui.QLabel(
                    "To automatically detect breaklines, a slope map is calculated. This map uses the neighboring 9"
                    " pixels to estimate a plane. The gradient (steepest slope) is then taken, converted to a slope"
                    "in degrees, and assigned to the pixel.")
                desc.setWordWrap(True)
                ls.addRow(desc)

                gfmod, gfscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsGridFeature",
                                                                                   "opalsGridFeature",
                                                                                   self.project,
                                                                                   {'feature': 'slpDeg'},
                                                                                   ["inFile",
                                                                                    "outFile",
                                                                                    "feature"])
                self.modules['slope'] = gfmod
                ls.addRow(gfscroll)

            if name == "2D-Approximation":
                desc = QtGui.QLabel(
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
                                                                                   {'threshold': '1 5'},
                                                                                   ["inFile",
                                                                                    "outFile",
                                                                                    "threshold",
                                                                                    "sigmaSmooth"])
                self.modules['edgeDetect'] = edgeDmod
                ls.addRow(edgeDscroll)

                desc = QtGui.QLabel("Since the output of opalsEdgeDetect is still a raster, we need to vectorize it:")
                desc.setWordWrap(True)
                ls.addRow(desc)


                vecmod, vecscroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsVectorize",
                                                                                   "opalsVectorize",
                                                                                   self.project,
                                                                                   {},
                                                                                   ["inFile",
                                                                                    "outFile"
                                                                                    ])
                self.modules['vectorize'] = vecmod
                ls.addRow(vecscroll)

            if name == "Topologic correction":
                desc = QtGui.QLabel(
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
                                                                                   'maxAngleDev': '75 15',
                                                                                   'avgDist': '3'},
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
                                                                                   'maxAngleDev': '150 15',
                                                                                   'avgDist': '3',
                                                                                    'merge.minWeight': '0.75',
                                                                                    'merge.relWeightLead': '0',
                                                                                    'merge.maxIter': '10',
                                                                                    'merge.revertDist': '5',
                                                                                    'merge.revertInterval': '1',
                                                                                    'merge.searchGeneration': '4',
                                                                                    'merge.preventIntersection': '1'},
                                                                                   ["inFile",
                                                                                     "outFile",
                                                                                     "method",
                                                                                     "maxAngleDev",
                                                                                     "merge\..*"])
                lt2scroll.setFixedHeight(lt2scroll.height()-200)
                self.modules['lt2'] = lt2mod
                ls.addRow(lt2scroll)

                lt3mod, lt3scroll = QpalsModuleBase.QpalsModuleBase.createGroupBox("opalsLineTopology",
                                                                                   "opalsLineTopology (3)",
                                                                                   self.project,
                                                                                   {'method': 'longest',
                                                                                   'minLength': '25',
                                                                                   'snapRadius': '0',
                                                                                   'maxTol': '0',
                                                                                   'maxAngleDev': '90 15',
                                                                                   'avgDist': '3'},
                                                                                   ["inFile",
                                                                                    "outFile",
                                                                                    "method",
                                                                                    "minLength",
                                                                                    "maxTol"])
                self.modules['lt3'] = lt3mod
                ls.addRow(lt3scroll)


            vl = QtGui.QVBoxLayout()
            vl.addLayout(ls, 1)
            navbar = QtGui.QHBoxLayout()
            next = QtGui.QPushButton("Next step >")
            next.clicked.connect(lambda: switchToNextTab(self.tabs))
            prev = QtGui.QPushButton("< Previous step")
            prev.clicked.connect(lambda: switchToPrevTab(self.tabs))
            if idx > 0:
                navbar.addWidget(prev)
            navbar.addStretch()
            if idx < len(names):
                navbar.addWidget(next)
            vl.addLayout(navbar)
            self.widgets[name].setLayout(vl)
            self.tabs.addTab(self.widgets[name], name)

        return self.tabs

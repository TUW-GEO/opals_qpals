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
                 'Topologic correction',
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
                dtmBox = QtGui.QGroupBox("opalsGrid")
                self.dtmGridStatus = QtGui.QListWidgetItem("hidden status")
                dtmGrid = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(self.project.opalspath, "opalsGrid.exe"), QpalsProject=self.project)
                dtmGrid.listitem = self.dtmGridStatus
                dtmGrid.load()
                self.modules['dtmGrid'] = dtmGrid
                for p in dtmGrid.params:
                    if p.name == "interpolation":
                        p.val = 'movingPlanes'
                    if p.name == "gridSize":
                        p.val = "1"

                dtmUi = dtmGrid.getFilteredParamUi(filter=["inFile", "outFile", "neighbours", "searchRadius", "interpolation"])
                advancedBox = QCollapsibleGroupBox("Advanced options")
                advancedBox.setChecked(False)
                dtmUi.addRow(advancedBox)
                advancedLa = dtmGrid.getFilteredParamUi(notfilter=["inFile", "outFile", "neighbours", "searchRadius", "interpolation"])
                advancedBox.setLayout(advancedLa)
                dtmBox.setLayout(dtmUi)
                ls.addRow(dtmBox)

                shdBox = QtGui.QGroupBox("opalsShade")
                self.dtmShadeStatus = QtGui.QListWidgetItem("hidden status")
                dtmShade = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(self.project.opalspath, "opalsShade.exe"), QpalsProject=self.project)
                dtmShade.listitem = self.dtmShadeStatus
                dtmShade.load()
                self.modules['dtmShade'] = dtmShade
                shdUi = dtmShade.getFilteredParamUi(filter=["inFile", "outFile"])
                advancedBox = QCollapsibleGroupBox("Advanced options")
                advancedBox.setChecked(False)
                shdUi.addRow(advancedBox)
                advancedLa = dtmShade.getFilteredParamUi(notfilter=["inFile", "outFile"])
                advancedBox.setLayout(advancedLa)
                shdBox.setLayout(shdUi)
                ls.addRow(shdBox)

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

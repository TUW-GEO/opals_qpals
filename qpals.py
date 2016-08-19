"""
/***************************************************************************
Name			 	 : qpals lidar tools
Description          : integrates the opals software as a qgis plugin
Date                 : 04/Oct/15 
copyright            : (C) 2015 by Lukas Winiwarter/TU Wien
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

from test import QpalsShowFile, QpalsProject, moduleSelector

class qpals:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.layerlist = dict()
        self.prjSet = QpalsProject.QpalsProject(name="", opalspath=r"D:\01_opals\01_nightly\opals\\",
                                                tempdir=r"D:\01_opals\temp", iface=self.iface)

    def __del__(self):
        pass

    def showModuleSelector(self):
        self.modSel = moduleSelector.moduleSelector(self.iface, self.layerlist, self.prjSet)
        self.modSelWindow = QDockWidget("Opals Module Selector", self.iface.mainWindow(), Qt.WindowMinimizeButtonHint)
        self.modSelWindow.setWidget(self.modSel)
        self.modSelWindow.setAllowedAreas(Qt.NoDockWidgetArea)  # don't let it dock
        self.modSelWindow.setMinimumSize(800, 400)
        self.modSelWindow.setFloating(True)
        self.modSelWindow.show()

    def showproject(self):
        self.prjUI = self.prjSet.getUI()
        self.prjUI.show()

    def showdd(self):
        import test.QpalsDropTextbox
        self.drop = test.QpalsDropTextbox.droptester()
        self.drop.show()

    def initGui(self):
        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setObjectName("qpalsMenu")
        self.menu.setTitle("qpals")

        self.menuItemModuleSelector = QAction(QIcon("icon.png"), "Module Selector", self.iface.mainWindow())
        self.menuItemModuleSelector.setObjectName("menuModSel")
        self.menuItemModuleSelector.setWhatsThis("Select a module from a list")
        self.menuItemModuleSelector.setStatusTip("Select module from list")
        QObject.connect(self.menuItemModuleSelector, SIGNAL("triggered()"), self.showModuleSelector)
        self.menu.addAction(self.menuItemModuleSelector)

        # self.dd = QAction(QIcon("icon.png"), "Drag&&Drop demo", self.iface.mainWindow())
        # self.dd.setObjectName("menuddDemo")
        # self.dd.setStatusTip("Drag and Drop demo")
        # QObject.connect(self.dd, SIGNAL("triggered()"), self.showdd)
        # self.menu.addAction(self.dd)

        self.mnuproject = QAction(QIcon("icon.png"), "Project settings", self.iface.mainWindow())
        self.mnuproject.setObjectName("menumnuproject")
        self.mnuproject.setStatusTip("Project settings")
        QObject.connect(self.mnuproject, SIGNAL("triggered()"), self.showproject)
        self.menu.addAction(self.mnuproject)

        menuBar = self.iface.mainWindow().menuBar()
        menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)

        self.dropspace = QDockWidget("Opals Visualizer", self.iface.mainWindow())
        self.dropspace.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dropobject = QpalsShowFile.QpalsShowFile(self.iface, self.layerlist, self.prjSet)
        self.dropobject.initUI()
        self.dropspace.setWidget(self.dropobject.ui)
        self.iface.mainWindow().addDockWidget(Qt.LeftDockWidgetArea, self.dropspace)
        self.dropspace.setContentsMargins(9, 9, 9, 9)
        #self.dropspace.removeEventFilter(self.iface.mainWindow())


    def unload(self):
        # Remove the plugin menu item and icon
        self.menu.deleteLater()
        self.dropspace.deleteLater()

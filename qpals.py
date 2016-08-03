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

class qpals:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

    def __del__(self):
        import os
        import glob
        files = glob.glob(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\log\*')
        files += glob.glob(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\tmp\*')
        for f in files:
            os.remove(f)

    def showModuleSelector(self):
        import test.moduleSelector
        self.modSel = test.moduleSelector.moduleSelector(self.iface)
        self.modSel.show()

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

        self.dd = QAction(QIcon("icon.png"), "Drag&&Drop demo", self.iface.mainWindow())
        self.dd.setObjectName("menuddDemo")
        self.dd.setStatusTip("Drag and Drop demo")
        QObject.connect(self.dd, SIGNAL("triggered()"), self.showdd)
        self.menu.addAction(self.dd)

        menuBar = self.iface.mainWindow().menuBar()
        menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)

    def unload(self):
        # Remove the plugin menu item and icon
        self.menu.deleteLater()

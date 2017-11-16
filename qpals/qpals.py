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
import os
import tempfile
import subprocess
import cPickle

# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import QpalsProject
import QpalsShowFile
import moduleSelector
from modules import QpalsSection, QpalsLM, QpalsAttributeMan, QpalsQuickLM



class qpals:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.active = True
        self.layerlist = dict()
        self.linemodeler = None
        QgsProject.instance().readProject.connect(self.projectloaded)
        s = QSettings()
        proj = QgsProject.instance()
        opalspath = s.value("qpals/opalspath", "")
        tempdir = proj.readEntry("qpals","tempdir", tempfile.gettempdir())[0]
        workdir = proj.readEntry("qpals","workdir", tempfile.gettempdir())[0]

        firstrun = False
        while opalspath == "":
            msg = QMessageBox()
            msg.setText("The path to the opals binaries has not been set.")
            msg.setInformativeText("Please set it now, or press cancel to unload the qpals plugin.")
            msg.setWindowTitle("qpals opals path")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ret = msg.exec_()
            if ret == QMessageBox.Ok:
                opalspath = QFileDialog.getExistingDirectory(None, caption='Select path containing opals*.exe binaries')
                if opalspath:
                    if os.path.exists(os.path.join(opalspath, "opalsCell.exe")):
                        s.setValue("qpals/opalspath", opalspath)
                        firstrun = True
                    else:
                        opalspath = ""
                        msg = QMessageBox()
                        msg.setText("Ooops..")
                        msg.setInformativeText("Could not validate opals path. Please make sure to select the folder "
                                               "containing the opals binaries, i.e. opalsCell.exe, opalsInfo.exe, etc.")
                        msg.setWindowTitle("qpals opals path")
                        msg.setStandardButtons(QMessageBox.Ok)
                        ret = msg.exec_()

            else:
                self.active = False

        if self.active:
            self.prjSet = QpalsProject.QpalsProject(name="", opalspath=opalspath,
                                                    tempdir=tempdir, workdir=workdir, iface=self.iface)
            try:
                resource_dir = os.path.join(os.path.dirname(__file__), "resources")
                info = subprocess.STARTUPINFO()
                info.dwFlags = subprocess.STARTF_USESHOWWINDOW
                info.wShowWindow = 0
                proc = subprocess.Popen([os.path.join(opalspath, "python.exe"),
                                         os.path.join(resource_dir, "get_attribute_types.py"),
                                         os.path.join(resource_dir, "attribute_types.py")],
                                        startupinfo=info)
                proc.communicate()
            except:
                print "Failed to update attribute types..."

        if firstrun:
            self.showproject()

    def __del__(self):
        pass

    def projectloaded(self):
        proj = QgsProject.instance()
        tempdir = proj.readEntry("qpals","tempdir", "")[0]
        workdir = proj.readEntry("qpals","workdir", "")[0]
        vismethod = proj.readNumEntry("qpals", "vismethod", -1)[0]
        if tempdir:
            self.prjSet.tempdir = tempdir
        if workdir:
            self.prjSet.workdir = workdir
        if vismethod:
            self.prjSet.vismethod = vismethod
            self.dropobject.visMethod.setCurrentIndex(vismethod)

        # tabs_p = proj.readEntry("qpals", "linemodeler", None)[0]
        # if tabs_p:
        #     tabs = cPickle.loads(tabs_p)
        #     self.linemodeler = self.linemodeler = QpalsLM.QpalsLM(project=self.prjSet, layerlist=self.layerlist,
        #                                                           iface=self.iface)
        #     self.linemodeler.tabs = tabs
        #     self.linemodelerUI = self.linemodeler.tabs


    def showModuleSelector(self):
        self.modSel = moduleSelector.moduleSelector(self.iface, self.layerlist, self.prjSet)
        self.modSelWindow = QDockWidget("qpals ModuleSelector", self.iface.mainWindow(), Qt.WindowMinimizeButtonHint)
        self.modSelWindow.setWidget(self.modSel)
        self.modSelWindow.setAllowedAreas(Qt.NoDockWidgetArea)  # don't let it dock
        self.modSelWindow.setMinimumSize(800, 400)
        self.modSelWindow.setFloating(True)
        self.modSelWindow.show()

    def showproject(self):
        self.prjUI = self.prjSet.getUI()
        self.prjUI.show()

    def showlog(self):
        import webbrowser
        webbrowser.open('file:///' + os.path.join(self.prjSet.tempdir, "opalsLog.xml"))

    def clearlog(self):
        try:
            os.remove(os.path.join(self.prjSet.tempdir, "opalsLog.xml"))
        except Exception as e:
            self.iface.messageBar().pushMessage('Something went wrong! See the message log for more information.',
                                                duration=3)
            print e

    def showAttrMan(self):
        self.attrman = QpalsAttributeMan.QpalsAttributeMan(project=self.prjSet,
                                                           layerlist=self.layerlist,
                                                           iface=self.iface)
        self.attrman.ui.show()

    def showSecGUI(self):
        self.sec = QpalsSection.QpalsSection(project=self.prjSet, layerlist=self.layerlist, iface=self.iface)
        self.secUI = self.sec.createWidget()
        self.secUIDock = QDockWidget("qpals Section", self.iface.mainWindow())
        self.secUIDock.setWidget(self.secUI)
        self.secUIDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.secUIDock.setFloating(True)
        self.secUIDock.show()
        self.secUIDock.visibilityChanged.connect(self.sec.close)

    def showLMGUI(self):
        if not self.linemodeler:
            self.linemodeler = QpalsLM.QpalsLM(project=self.prjSet, layerlist=self.layerlist, iface=self.iface)
            self.linemodeler.createWidget()
        self.linemodelerUIDock = QDockWidget("qpals LineModeler", self.iface.mainWindow())
        self.linemodelerUIDock.setWidget(self.linemodeler.tabs)
        self.linemodelerUIDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.linemodelerUIDock.setFloating(True)
        self.linemodelerUIDock.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.linemodelerUIDock.resize(800, 800)
        self.linemodelerUIDock.move(50,50)
        self.linemodelerUIDock.show()


    def initGui(self):
        if self.active:
            self.menu = QMenu(self.iface.mainWindow())
            self.menu.setObjectName("qpalsMenu")
            self.menu.setTitle("qpals")

            IconPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "media")
            opalsIcon = QIcon(os.path.join(IconPath, "opalsIcon.png"))
            settingsIcon = QIcon(os.path.join(IconPath, "opalsSettings.png"))
            specialIcon = QIcon(os.path.join(IconPath, "opalsSpecial.png"))

            self.menuItemModuleSelector = QAction(opalsIcon, "&ModuleSelector", self.iface.mainWindow())
            self.menuItemModuleSelector.setWhatsThis("Select a module from a list")
            self.menuItemModuleSelector.setStatusTip("Select module from list")
            QObject.connect(self.menuItemModuleSelector, SIGNAL("triggered()"), self.showModuleSelector)

            self.logmnu = QMenu(self.menu)
            self.logmnu.setIcon(settingsIcon)
            self.logmnu.setObjectName("qpalsLogMenu")
            self.logmnu.setTitle("Log")

            self.mnulog = QAction("show opalsLog", self.iface.mainWindow())
            self.mnulog.setStatusTip("Show log information")
            QObject.connect(self.mnulog, SIGNAL("triggered()"), self.showlog)
            self.logmnu.addAction(self.mnulog)

            self.mnuclearlog = QAction("clear opalsLog", self.iface.mainWindow())
            self.mnuclearlog.setStatusTip("Delete log file")
            self.mnuclearlog.triggered.connect(self.clearlog)
            self.logmnu.addAction(self.mnuclearlog)



            self.mnuproject = QAction(settingsIcon, "&ProjectSettings", self.iface.mainWindow())
            self.mnuproject.setStatusTip("ProjectSettings")
            QObject.connect(self.mnuproject, SIGNAL("triggered()"), self.showproject)

            self.mnusec = QAction(specialIcon, "&Section", self.iface.mainWindow())
            self.mnusec.setStatusTip("Section")
            QObject.connect(self.mnusec, SIGNAL("triggered()"), self.showSecGUI)

            self.mnulm = QAction(specialIcon, "&LineModeler", self.iface.mainWindow())
            self.mnulm.setStatusTip("LineModeler")
            QObject.connect(self.mnulm, SIGNAL("triggered()"), self.showLMGUI)


            # QuickLM is acessible through LM
            # self.mnulm = QAction(opalsIcon, "quick LineModeller", self.iface.mainWindow())
            # self.mnulm.setStatusTip("Start the quick LineModeller GUI")
            # QObject.connect(self.mnulm, SIGNAL("triggered()"), self.showQuickLMGUI)
            # self.menu.addAction(self.mnulm)

            self.mnuatt = QAction(opalsIcon, "&AttributeManager", self.iface.mainWindow())
            self.mnuatt.setStatusTip("AttributeManager")
            QObject.connect(self.mnuatt, SIGNAL("triggered()"), self.showAttrMan)

            self.menu.addAction(self.menuItemModuleSelector)
            self.menu.addAction(self.mnuatt)
            self.menu.addSeparator()
            self.menu.addAction(self.mnusec)
            self.menu.addAction(self.mnulm)
            self.menu.addSeparator()
            self.menu.addMenu(self.logmnu)
            self.menu.addAction(self.mnuproject)

            menuBar = self.iface.mainWindow().menuBar()
            menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)

            self.dropspace = QDockWidget("qpals Visualizer", self.iface.mainWindow())
            self.dropspace.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            self.dropobject = QpalsShowFile.QpalsShowFile(self.iface, self.layerlist, self.prjSet)
            self.dropobject.initUI()
            self.dropspace.setWidget(self.dropobject.ui)
            self.iface.mainWindow().addDockWidget(Qt.LeftDockWidgetArea, self.dropspace)
            self.dropspace.setContentsMargins(9, 9, 9, 9)
            #self.dropspace.removeEventFilter(self.iface.mainWindow())


    def unload(self):
        if self.active:
            # Remove the plugin menu item and icon
            self.menu.deleteLater()
            self.dropspace.deleteLater()

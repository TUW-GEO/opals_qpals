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
from __future__ import print_function
from __future__ import absolute_import

import datetime

from builtins import object
import os
import tempfile
import subprocess
import platform
import semantic_version

# Import the PyQt and QGIS libraries
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.core import *
from qgis.gui import *

from . import QpalsProject
from . import QpalsModuleBase
from . import QpalsParameter
from . import QpalsShowFile
from . import moduleSelector
from .modules import QpalsSection, QpalsLM, QpalsAttributeMan, QpalsQuickLM, QpalsWSM

from .. import logMessage   # import qpals log function

def ensure_opals_path(path, project):
    logMessage("ensure_opals_path called")
    while not os.path.exists(os.path.join(path, "opalsInfo.exe")):
        msg = QMessageBox()
        msg.setText("Ooops..")
        msg.setInformativeText("Could not validate opals path. Please make sure to select the folder "
                               "containing the opals binaries, i.e. opalsCell.exe, opalsInfo.exe, etc.")
        msg.setWindowTitle("qpals opals path")
        msg.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        ret = msg.exec_()
        if ret == QMessageBox.Ok:
            path = QFileDialog.getExistingDirectory(None, caption='Select path containing opals*.exe binaries')
        else:
            return None, None, None
    # get opals Version
    mod = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(path, "opalsInfo.exe"),
                                          QpalsProject=project)
    mod.params = [QpalsParameter.QpalsParameter('-version', '', None, None, None, None, None, flag_mode=True)]
    res = mod.run()
    opalsVersion = semantic_version.Version.coerce([item.split()[1].split("(")[0] for item in res['stdout'].split('\r\n')
                                             if item.startswith("opalsInfo")][0])
    opalsBuildDate = datetime.datetime.strptime([item.split("compiled on ")[1] for item in res['stdout'].split('\r\n')
                                             if item.startswith("compiled on ")][0], '%b %d %Y %H:%M:%S')
    return path, opalsVersion, opalsBuildDate


class qpalsSettings(QSettings):
    def __init__(self, plugin_name):
        QSettings.__init__(self)
        self.plugin_name = plugin_name
        self.path_label = f"{self.plugin_name}/opalspath"
    def getOpalsPath(self):
        return self.value(self.path_label, "")

    def setOpalsPath(self, opalspath):
        self.setValue(self.path_label, opalspath)


class qpals(object):
    def __init__(self, iface, plugin_name):
        # Save reference to the QGIS interface
        self.iface = iface
        self.active = True
        self.layerlist = dict()
        self.linemodeler = None
        self.wsm = None
        self.help_action = None
        self.plugin_name = plugin_name
        QgsProject.instance().readProject.connect(self.projectloaded)
        s = qpalsSettings(plugin_name)
        proj = QgsProject.instance()
        opalspath = s.getOpalsPath()
        tempdir = proj.readEntry("qpals","tempdir", tempfile.gettempdir())[0]
        workdir = proj.readEntry("qpals","workdir", tempfile.gettempdir())[0]

        firstrun = False
        if platform.system() != "Windows":
            msg = QMessageBox()
            msg.setText("qpals is currently only supported on Windows, not on '%s'" % platform.system())
            msg.setInformativeText("Please uninstall qpals again")
            msg.setWindowTitle("qpals is not supported on your platform")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            self.active = False
            return 


        if opalspath == "":
            msg = QMessageBox()
            msg.setText("The path to the opals binaries has not been set.")
            msg.setInformativeText("Please set it now, or press cancel to unload the qpals plugin.")
            msg.setWindowTitle("qpals opals path")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ret = msg.exec_()
            if ret == QMessageBox.Ok:
                opalspath = QFileDialog.getExistingDirectory(None, caption='Select path containing opals*.exe binaries')
                s.setOpalsPath(opalspath)
                firstrun = True

        logMessage(f"qpals.__init__ opalspath={opalspath}")
        project = QpalsProject.QpalsProject(name="", opalspath=opalspath,
                                                tempdir=tempdir, workdir=workdir, iface=self.iface)
        opalspath, opalsVersion, opalsBuildDate = ensure_opals_path(opalspath, project)
        project.opalsVersion = opalsVersion
        project.opalsBuildDate = opalsBuildDate

        if not opalspath:
            self.active = False
        else:
            if opalspath != project.opalspath:
                logMessage(f"opalspath has changed from {project.opalspath} to {opalspath}")
                project.opalspath = opalspath
                s.setOpalsPath(opalspath)

        if self.active:
            self.prjSet = project
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
                print("Failed to update attribute types...")

        if firstrun and self.active:
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
            print(e)

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
        self.secUIDock.resize(1000, 800)
        self.secUIDock.move(50, 50)
        self.secUIDock.visibilityChanged.connect(self.sec.close)

    def showLMGUI(self):
        if not self.linemodeler:
            self.linemodeler = QpalsLM.QpalsLM(project=self.prjSet, layerlist=self.layerlist, iface=self.iface)
            self.linemodeler.createWidget()
        self.linemodelerUIDock = QDockWidget("qpals LineModeler", self.iface.mainWindow())
        self.linemodelerUIDock.setWidget(self.linemodeler.scrollwidget)
        self.linemodelerUIDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.linemodelerUIDock.setFloating(True)
        self.linemodelerUIDock.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.linemodelerUIDock.resize(800, 800)
        self.linemodelerUIDock.move(50,50)
        self.linemodelerUIDock.show()
        self.linemodelerUIDock.visibilityChanged.connect(self.linemodeler.close)

    def showWSM(self):
        if not self.wsm:
            self.wsm = QpalsWSM.QpalsWSM(project=self.prjSet, layerlist=self.layerlist, iface=self.iface)
            self.wsm.createWidget()
        self.wsmDock = QDockWidget("qpals WaterSurfaceModeler", self.iface.mainWindow())
        self.wsmDock.setWidget(self.wsm)
        self.wsmDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.wsmDock.setFloating(True)
        self.wsmDock.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.wsmDock.resize(1100, 700)
        self.wsmDock.move(50,50)
        self.wsmDock.show()
        self.wsmDock.visibilityChanged.connect(self.wsm.close)


    def initGui(self):
        if self.active:
            self.menu = QMenu(self.iface.mainWindow())
            self.menu.setObjectName("qpalsMenu")

            self.menu.setTitle(self.plugin_name)

            IconPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "media")
            opalsIcon = QIcon(os.path.join(IconPath, "opalsIcon.png"))
            settingsIcon = QIcon(os.path.join(IconPath, "opalsSettings.png"))
            specialIcon = QIcon(os.path.join(IconPath, "opalsSpecial.png"))

            self.menuItemModuleSelector = QAction(opalsIcon, "&ModuleSelector", self.iface.mainWindow())
            self.menuItemModuleSelector.setWhatsThis("Select a module from a list")
            self.menuItemModuleSelector.setStatusTip("Select module from list")
            self.menuItemModuleSelector.triggered.connect(self.showModuleSelector)

            self.logmnu = QMenu(self.menu)
            self.logmnu.setIcon(settingsIcon)
            self.logmnu.setObjectName("qpalsLogMenu")
            self.logmnu.setTitle("Log")

            self.mnulog = QAction("show opalsLog", self.iface.mainWindow())
            self.mnulog.setStatusTip("Show log information")
            self.mnulog.triggered.connect(self.showlog)
            self.logmnu.addAction(self.mnulog)

            self.mnuclearlog = QAction("clear opalsLog", self.iface.mainWindow())
            self.mnuclearlog.setStatusTip("Delete log file")
            self.mnuclearlog.triggered.connect(self.clearlog)
            self.logmnu.addAction(self.mnuclearlog)



            self.mnuproject = QAction(settingsIcon, "&ProjectSettings", self.iface.mainWindow())
            self.mnuproject.setStatusTip("ProjectSettings")
            self.mnuproject.triggered.connect(self.showproject)

            self.mnusec = QAction(specialIcon, "&Section", self.iface.mainWindow())
            self.mnusec.setStatusTip("Section")
            self.mnusec.triggered.connect(self.showSecGUI)

            self.mnulm = QAction(specialIcon, "&LineModeler", self.iface.mainWindow())
            self.mnulm.setStatusTip("LineModeler")
            self.mnulm.triggered.connect(self.showLMGUI)

            self.mnuWsm = QAction(specialIcon, "&WaterSurfaceModeler", self.iface.mainWindow())
            self.mnuWsm.setStatusTip("WaterSurfaceModeler")
            self.mnuWsm.triggered.connect(self.showWSM)


            # QuickLM is acessible through LM
            # self.mnulm = QAction(opalsIcon, "quick LineModeller", self.iface.mainWindow())
            # self.mnulm.setStatusTip("Start the quick LineModeller GUI")
            # QObject.connect(self.mnulm, SIGNAL("triggered()"), self.showQuickLMGUI)
            # self.menu.addAction(self.mnulm)

            self.mnuatt = QAction(opalsIcon, "&AttributeManager", self.iface.mainWindow())
            self.mnuatt.setStatusTip("AttributeManager")
            self.mnuatt.triggered.connect(self.showAttrMan)

            self.menu.addAction(self.menuItemModuleSelector)
            self.menu.addAction(self.mnuatt)
            self.menu.addSeparator()
            self.menu.addAction(self.mnusec)
            self.menu.addAction(self.mnulm)
            self.menu.addAction(self.mnuWsm)
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

            # create help action
            self.help_action = QAction(
                opalsIcon,
                f"{self.plugin_name}...",
                self.iface.mainWindow()
            )
            # Add the action to the Help menu
            self.iface.pluginHelpMenu().addAction(self.help_action)
            self.help_action.triggered.connect(self.show_help)


    def unload(self):
        if self.active:
            # remove help entry
            self.iface.pluginHelpMenu().removeAction(self.help_action)
            del self.help_action

            # Remove the plugin menu item and icon
            self.menu.deleteLater()
            self.dropspace.deleteLater()

    def show_help(self):
        """ Open the online help. """
        s = qpalsSettings(self.plugin_name)
        opalspath = s.getOpalsPath()
        #QDesktopServices.openUrl(QUrl('https://opals.geo.tuwien.ac.at/html/stable/usr_qpals.html'))
        QDesktopServices.openUrl(QUrl('file:///' + os.path.join(opalspath, "..", "doc", "html", "usr_qpals.html"))) # use local help

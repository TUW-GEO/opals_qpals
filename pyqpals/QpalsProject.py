"""
/***************************************************************************
Name			 	 : qpalsProject
Description          : Managing Project settings for qpals
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

import datetime

from builtins import str
from builtins import object
from qgis.PyQt import QtCore, QtGui, QtWidgets
from qgis.core import *
from qgis.gui import *
import os

import semantic_version

from .QpalsShowFile import VISUALISATION_METHODS
from .qt_extensions import QpalsDropTextbox


class QpalsProject(object):
    def __init__(self, tempdir, name, opalspath, workdir, iface=None):
        self.tempdir = tempdir
        self.workdir = workdir
        self.name = name
        self.opalspath = opalspath
        self.vismethod = 1
        self.viscells = 1
        self.viscellm = 3
        self.visisoint = 10
        self.iface = iface
        self.common = dict()
        self.globals = dict()
        self.PATH = os.environ['PATH']
        self.getEnvVar()
        self.opalsVersion = semantic_version.Version.coerce('0.0.0')
        self.opalsBuildDate = datetime.datetime.utcfromtimestamp(0)

    def getEnvVar(self):
        try:
            import winreg as wreg
            key = wreg.OpenKey(wreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                               0, wreg.KEY_READ)
            self.PATH = wreg.QueryValueEx(key, "Path")[0]
            # self.PATH = str(self.opalspath + ";" + self.PATH)
            self.PATH = str(os.path.join(self.opalspath, "..") + ";" + self.PATH)
        except Exception as e:
            raise e

    def getUI(self):
        self.ui = QtWidgets.QDialog()
        self.ui.setWindowTitle("qpals ProjectSettings")
        lo = QtWidgets.QFormLayout()
        self.txtOpalspath = QpalsDropTextbox.QpalsDropTextbox(show_layers=False)
        self.txtOpalspath.setText(self.opalspath)
        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(self.txtOpalspath,1)
        self.txtWorkdir = QpalsDropTextbox.QpalsDropTextbox(show_layers=False)
        self.txtWorkdir.setText(self.workdir)
        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(self.txtWorkdir,1)
        self.txtTempdir = QpalsDropTextbox.QpalsDropTextbox(show_layers=False)
        self.txtTempdir.setText(self.tempdir)
        hbox3 = QtWidgets.QHBoxLayout()
        hbox3.addWidget(self.txtTempdir,1)
        self.txtOpalspath.setPlaceholderText("drop folder here...")
        self.txtWorkdir.setPlaceholderText("drop folder here...")
        self.txtTempdir.setPlaceholderText("drop folder here...")


        self.txtName = QtWidgets.QLineEdit(self.name)

        self.selVisMethod = QtWidgets.QComboBox()

        self.selVisMethod.addItem(VISUALISATION_METHODS[0])
        self.selVisMethod.addItem(VISUALISATION_METHODS[1])
        self.selVisMethod.addItem(VISUALISATION_METHODS[2])
        self.selVisMethod.addItem(VISUALISATION_METHODS[3])
        self.selVisMethod.addItem(VISUALISATION_METHODS[4])
        self.selVisMethod.addItem(VISUALISATION_METHODS[5])
        self.selVisMethod.addItem(VISUALISATION_METHODS[6])
        self.selVisMethod.addItem(VISUALISATION_METHODS[7])
        self.selVisMethod.addItem(VISUALISATION_METHODS[8])
        self.selVisMethod.addItem(VISUALISATION_METHODS[9])



        self.cellSizeLbl = QtWidgets.QLabel("Set cell size:")
        self.cellSizeBox = QtWidgets.QLineEdit()

        self.cellFeatLbl = QtWidgets.QLabel("Set feature:")
        self.cellFeatCmb = QtWidgets.QComboBox()
        self.isoInteLbl = QtWidgets.QLabel("Set isoline interval:")
        self.isoInteBox = QtWidgets.QLineEdit()
        self.cellFeatCmb.addItems(["min", "max", "diff", "mean", "median", "sum", "variance", "rms", "pdens", "pcount",
                                   "minority", "majority", "entropy"])
        self.cellFeatCmb.setCurrentIndex(3)


        self.selVisMethod.currentIndexChanged.connect(self.updatevisMethod)


        lo.addRow(QtWidgets.QLabel("Path to opals binaries*"), hbox1)
        lo.addRow(QtWidgets.QLabel("Working directory**"), hbox2)
        lo.addRow(QtWidgets.QLabel("Temporary directory**"), hbox3)
        lo.addRow(QtWidgets.QLabel("Project name (unused)"), self.txtName)
        lo.addRow(QtWidgets.QLabel("Default visualisation method**"), self.selVisMethod)
        lo.addRow(self.cellSizeLbl, self.cellSizeBox)
        lo.addRow(self.cellFeatLbl, self.cellFeatCmb)
        lo.addRow(self.isoInteLbl, self.isoInteBox)

        self.okbtn = QtWidgets.QPushButton("Save && Exit")
        self.okbtn.clicked.connect(self.savesettings)
        lo.addRow(self.okbtn)
        lo.addRow(QtWidgets.QLabel("* will be saved within qgis for all projects"))
        lo.addRow(QtWidgets.QLabel("** will be saved in the qgis project"))
        self.ui.setLayout(lo)
        self.loadVissettings()
        return self.ui


    def updatevisMethod(self):
        self.curVisMethod = self.selVisMethod.currentIndex()
        if self.curVisMethod in [3, 4, 5, 9]:
            self.cellSizeLbl.show()
            self.cellSizeBox.show()
            self.cellFeatLbl.show()
            self.cellFeatCmb.show()
            #self.cellAttrCmb.show()
            #self.cellAttrLbl.show()
        else:
            self.cellSizeLbl.hide()
            self.cellSizeBox.hide()
            self.cellFeatLbl.hide()
            self.cellFeatCmb.hide()
            #self.cellAttrCmb.hide()
            #self.cellAttrLbl.hide()

        if self.curVisMethod in [9]:
            self.isoInteLbl.show()
            self.isoInteBox.show()
        else:
            self.isoInteLbl.hide()
            self.isoInteBox.hide()

    def savesettings(self):
        s = QtCore.QSettings()
        proj = QgsProject.instance()
        self.workdir = self.txtWorkdir.text()
        proj.writeEntry("qpals","workdir", self.workdir)
        self.tempdir = self.txtTempdir.text()
        proj.writeEntry("qpals","tempdir", self.tempdir)
        self.opalspath = self.txtOpalspath.text()
        s.setValue("qpals/opalspath", self.opalspath)

        self.name = self.txtName
        self.vismethod = self.selVisMethod.currentIndex()
        self.viscells = self.cellSizeBox.text()
        self.viscellm = self.cellFeatCmb.currentIndex()
        try:
            self.visisoint = int(self.isoInteBox.text())
        except:
            self.visisoint = 10
        proj.writeEntry("qpals","vismethod", self.vismethod)
        proj.writeEntry("qpals","vis-cells", self.viscells)
        proj.writeEntry("qpals","vis-cellm", self.viscellm)
        proj.writeEntry("qpals","vis-isoint", self.visisoint)
        proj.setDirty(True)
        self.getEnvVar()
        self.ui.hide()

    def loadVissettings(self):
        s = QtCore.QSettings()
        proj = QgsProject.instance()
        self.vismethod = proj.readNumEntry('qpals', 'vismethod', 1)[0]
        self.viscells = proj.readEntry('qpals', 'vis-cells', '1;1')[0]
        self.viscellm = proj.readNumEntry('qpals', 'vis-cellm', 3)[0]
        self.visisoint = proj.readNumEntry('qpals', 'vis-isoint', 10)[0]
        self.selVisMethod.setCurrentIndex(self.vismethod)
        self.cellSizeBox.setText(self.viscells)
        self.cellFeatCmb.setCurrentIndex(self.viscellm)
        self.isoInteBox.setText(str(self.visisoint))

    def globals_common(self):
        x = self.common.copy()
        x.update(self.globals)
        return x

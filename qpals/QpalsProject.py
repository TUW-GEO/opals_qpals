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

from PyQt4 import QtCore, QtGui
from qgis.core import *
from qgis.gui import *
import os

from QpalsShowFile import QpalsShowFile
from qt_extensions import QpalsDropTextbox
import QpalsModuleBase


class QpalsProject:
    def __init__(self, tempdir, name, opalspath, workdir, iface=None):
        self.tempdir = tempdir
        self.workdir = workdir
        self.name = name
        self.opalspath = opalspath
        self.vismethod = 3
        self.viscells = 1
        self.viscellm = 3
        self.visisoint = 10
        self.iface = iface
        self.common = dict()
        self.globals = dict()


    def getUI(self):
        self.ui = QtGui.QDialog()
        self.ui.setWindowTitle("Qpals Project Settings")
        lo = QtGui.QFormLayout()
        self.txtOpalspath = QpalsDropTextbox.QpalsDropTextbox(show_layers=False)
        self.txtOpalspath.setText(self.opalspath)
        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.txtOpalspath,1)
        self.txtWorkdir = QpalsDropTextbox.QpalsDropTextbox(show_layers=False)
        self.txtWorkdir.setText(self.workdir)
        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(self.txtWorkdir,1)
        self.txtTempdir = QpalsDropTextbox.QpalsDropTextbox(show_layers=False)
        self.txtTempdir.setText(self.tempdir)
        hbox3 = QtGui.QHBoxLayout()
        hbox3.addWidget(self.txtTempdir,1)
        self.txtOpalspath.setPlaceholderText("drop folder here...")
        self.txtWorkdir.setPlaceholderText("drop folder here...")
        self.txtTempdir.setPlaceholderText("drop folder here...")


        self.txtName = QtGui.QLineEdit(self.name)

        self.selVisMethod = QtGui.QComboBox()
        self.selVisMethod.addItem("Shading (raster)")
        self.selVisMethod.addItem("Z-Color (raster)")
        self.selVisMethod.addItem("Z-Value (raw height values)(raster)")
        self.selVisMethod.addItem("Bounding box (vector)")
        self.selVisMethod.addItem("Minimum bounding rectangle (vector)")
        self.selVisMethod.addItem("Convex hull (vector)")
        self.selVisMethod.addItem("Alpha shape (vector)")
        self.selVisMethod.addItem("Isolines (vector, based on Z-Value)")


        self.cellSizeLbl = QtGui.QLabel("Set cell size:")
        self.cellSizeBox = QtGui.QLineEdit()

        self.cellFeatLbl = QtGui.QLabel("Set feature:")
        self.cellFeatCmb = QtGui.QComboBox()
        self.isoInteLbl = QtGui.QLabel("Set isoline interval:")
        self.isoInteBox = QtGui.QLineEdit()
        self.cellFeatCmb.addItems(["min", "max", "diff", "mean", "median", "sum", "variance", "rms", "pdens", "pcount",
                                   "minority", "majority", "entropy"])
        self.cellFeatCmb.setCurrentIndex(3)


        self.selVisMethod.currentIndexChanged.connect(self.updatevisMethod)


        lo.addRow(QtGui.QLabel("Path to opals binaries*"), hbox1)
        lo.addRow(QtGui.QLabel("Working directory**"), hbox2)
        lo.addRow(QtGui.QLabel("Temporary directory**"), hbox3)
        lo.addRow(QtGui.QLabel("Project name (unused)"), self.txtName)
        lo.addRow(QtGui.QLabel("Default visualisation method**"), self.selVisMethod)
        lo.addRow(self.cellSizeLbl, self.cellSizeBox)
        lo.addRow(self.cellFeatLbl, self.cellFeatCmb)
        lo.addRow(self.isoInteLbl, self.isoInteBox)

        self.okbtn = QtGui.QPushButton("Save && Exit")
        self.okbtn.clicked.connect(self.savesettings)
        lo.addRow(self.okbtn)
        lo.addRow(QtGui.QLabel("* will be saved within qgis for all projects"))
        lo.addRow(QtGui.QLabel("** will be saved in the qgis project"))
        self.ui.setLayout(lo)
        self.loadVissettings()
        return self.ui


    def updatevisMethod(self):
        self.curVisMethod = self.selVisMethod.currentIndex()
        if self.curVisMethod in [0, 1, 2, 7]:
            self.cellSizeLbl.show()
            self.cellSizeBox.show()
            self.cellFeatLbl.show()
            self.cellFeatCmb.show()
        else:
            self.cellSizeLbl.hide()
            self.cellSizeBox.hide()
            self.cellFeatLbl.hide()
            self.cellFeatCmb.hide()

        if self.curVisMethod in [7]:
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
        self.ui.hide()

    def loadVissettings(self):
        s = QtCore.QSettings()
        proj = QgsProject.instance()
        self.vismethod = proj.readNumEntry('qpals', 'vismethod', 3)[0]
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

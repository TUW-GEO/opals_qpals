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

from QpalsShowFile import QpalsShowFile
from qt_extensions import QpalsDropTextbox


class QpalsProject:
    def __init__(self, tempdir, name, opalspath, workdir, vismethod=QpalsShowFile.METHOD_BOX, iface=None):
        self.tempdir = tempdir
        self.workdir = workdir
        self.name = name
        self.opalspath = opalspath
        self.vismethod = vismethod
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
        self.selVisMethod.setCurrentIndex(self.vismethod)
        lo.addRow(QtGui.QLabel("Path to opals binaries*"), hbox1)
        lo.addRow(QtGui.QLabel("Working directory**"), hbox2)
        lo.addRow(QtGui.QLabel("Temporary directory**"), hbox3)
        lo.addRow(QtGui.QLabel("Project name (unused)"), self.txtName)
        lo.addRow(QtGui.QLabel("Default visualisation method**"), self.selVisMethod)

        self.okbtn = QtGui.QPushButton("Save && Exit")
        self.okbtn.clicked.connect(self.savesettings)
        lo.addRow(self.okbtn)
        lo.addRow(QtGui.QLabel("* will be saved within qgis for all projects"))
        lo.addRow(QtGui.QLabel("** will be saved in the qgis project"))
        self.ui.setLayout(lo)
        return self.ui

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
        proj.writeEntry("qpals","vismethod", self.vismethod)
        proj.setDirty(True)
        self.ui.hide()


    def globals_common(self):
        x = self.common.copy()
        x.update(self.globals)
        return x

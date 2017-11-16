"""
/***************************************************************************
Name			 	 : qpalsAttributeMan
Description          : Attribute manager for qpals
Date                 : 2017-07-31
copyright            : (C) 2017 by Lukas Winiwarter/TU Wien
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

from PyQt4 import QtCore, QtGui, QtWebKit
from qgis.core import *
from qgis.gui import *
import os
import operator, webbrowser
from ..qt_extensions import QpalsDropTextbox
from ..resources.attribute_types import odm_predef_attributes, odm_data_types

class QpalsAttributeMan:
    def __init__(self, project, iface=None, layerlist=None):
        self.project = project
        self.iface = iface
        self.layerlist = layerlist
        self.ui = self.getUI()

    def getUI(self):
        self.ui = QtGui.QDialog()
        self.ui.resize(720, 300)
        self.ui.setWindowTitle("qpals AttributeManager")
        lo = QtGui.QFormLayout()
        vb = QtGui.QVBoxLayout()
        hb = QtGui.QHBoxLayout()
        self.pointcloud = QpalsDropTextbox.QpalsDropTextbox(layerlist=self.layerlist)
        hb.addWidget(self.pointcloud,1)
        lo.addRow("ODM File", hb)
        vb.addLayout(lo,0)
        self.attable = QtGui.QTableView()
        self.newnamebox = QtGui.QComboBox()
        self.newnamebox.setEditable(True)
        for attr in odm_predef_attributes:
            self.newnamebox.addItem(attr)
        self.newnamebox.lineEdit().setPlaceholderText("_Name")
        self.typedropdown = QtGui.QComboBox()
        for type in odm_data_types:
            self.typedropdown.addItem(type)
        self.formulabox = QtGui.QLineEdit("")
        self.formulabox.setPlaceholderText("opalsAddInfo formula")
        self.helpbtn = QtGui.QPushButton('?')
        self.helpbtn.setMaximumWidth(self.helpbtn.fontMetrics().boundingRect("?").width() + 7)
        self.addchangebtn = QtGui.QPushButton('Add/Change attribute')
        self.closebtn = QtGui.QPushButton('Close')
        hb2 = QtGui.QHBoxLayout()
        hb2.addWidget(self.newnamebox)
        hb2.addWidget(QtGui.QLabel("("))
        hb2.addWidget(self.typedropdown)
        hb2.addWidget(QtGui.QLabel(")"))
        hb2.addWidget(QtGui.QLabel("="))
        hb2.addWidget(self.formulabox)
        hb2.addWidget(self.addchangebtn)
        hb2.addWidget(self.helpbtn)
        hb2.addStretch()
        hb2.addWidget(self.closebtn)
        vb.addWidget(self.attable, 1)
        vb.addLayout(hb2)
        self.ui.setLayout(vb)
        self.pointcloud.editingFinished.connect(self.pcChanged)
        self.newnamebox.editTextChanged.connect(self.newnameChanged)
        self.closebtn.clicked.connect(self.close)
        self.helpbtn.clicked.connect(self.addinfoHelp)
        self.addchangebtn.clicked.connect(self.fieldcalc)
        self.newnamebox.lineEdit().setText("_")
        return self.ui

    def close(self):
        self.ui.hide()
        self.ui = None

    def addinfoHelp(self):
        webbrowser.open("file:///" + os.path.join(self.project.opalspath,
                                                  r"..\doc\html\ModuleAddInfo.html#addinfo_syntax_formula"))

    def newnameChanged(self):
        attrname = self.newnamebox.currentText()
        if attrname in odm_predef_attributes:
            type = odm_predef_attributes[attrname]
            idx = self.typedropdown.findText(type)
            self.typedropdown.setCurrentIndex(idx)
            self.typedropdown.setEnabled(False)
        else:
            if not attrname.startswith("_"):
                self.newnamebox.lineEdit().setText("_"+attrname)
            self.typedropdown.setEnabled(True)
        if attrname[1:] in odm_predef_attributes:
            self.newnamebox.lineEdit().setText(attrname[1:])

    def fieldcalc(self):
        from .. import QpalsModuleBase, QpalsParameter
        attrname = self.newnamebox.currentText()
        attrtype = self.typedropdown.currentText()
        if attrname not in odm_predef_attributes:
            attrname += "(%s)" % attrtype
        attrformula = self.formulabox.text()
        addinfoinst = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(self.project.opalspath, "opalsAddInfo.exe"),
                                                   QpalsProject=self.project)
        addinfoinst.params = [QpalsParameter.QpalsParameter('inFile', self.pointcloud.text(),
                                                         None, None, None, None, None),
                              QpalsParameter.QpalsParameter('attribute', "%s=%s" % (attrname, attrformula),
                                                         None, None, None, None, None),
                              ]
        try:
            moduleOut = addinfoinst.run(show=0)
            self.pcChanged()
        except Exception as e:
            print e


    def pcChanged(self):
        curitem = self.pointcloud.text()
        if curitem == "":
            return
        if not os.path.exists(curitem):
            self.pointcloud.setStyleSheet('background-color: rgb(255,140,140);')
            self.pointcloud.setToolTip('Invalid file')
            return
        self.pointcloud.setStyleSheet('')
        self.pointcloud.setToolTip('')

        attrs, entries = getAttributeInformation(curitem, self.project)
        if attrs and entries:
            model = QtGui.QStandardItemModel()
            model.setColumnCount(len(entries) - 1)
            model.setHorizontalHeaderLabels(entries[1:])
            for attr in attrs:
                row = []
                for i in attr[1:]:
                    item = QtGui.QStandardItem(i)
                    item.setEditable(False)
                    row.append(item)
                model.appendRow(row)
            model.setVerticalHeaderLabels([attr[0] for attr in attrs])
            self.attable.setModel(model)
        else:
            self.pointcloud.setStyleSheet('background-color: rgb(255,140,140);')
            self.pointcloud.setToolTip('Invalid file')



def getAttributeInformation(file, project):
    from .. import QpalsModuleBase, QpalsParameter
    infoinst = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(project.opalspath, "opalsInfo.exe"),
                                               QpalsProject=project)
    infoinst.params = [QpalsParameter.QpalsParameter('inFile', file,
                                                     None, None, None, None, None)]
    try:
        moduleOut = infoinst.run(show=0)
        outtext = moduleOut['stdout']
        ## begin parsing of log
        header_passed = False
        attrs = []
        entries = []
        for line in outtext.split("\n"):
            if line.startswith("Attribute	type"):
                header_passed = True
                entries = line.split("\t")
            elif header_passed:
                if line.startswith("Index statistics"):
                    break  # end of attribute table
                data = line.split("\t")
                attrs.append(data)
        if not header_passed:
            raise NotImplementedError
        return  attrs, entries
    except Exception:
        return None, None
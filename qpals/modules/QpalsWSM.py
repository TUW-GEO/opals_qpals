"""
/***************************************************************************
Name			 	 : qpalsWSM
Description          : GUI for water surface modelling within qpals
Date                 : 2018-04-04
copyright            : (C) 2018 by Lukas Winiwarter/TU Wien
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
from xml.dom import minidom
import re
import ogr
import numpy as np
import pickle, copy

from qgis.PyQt import QtWidgets, QtCore, QtGui
from ..qt_extensions.QpalsDropTextbox import QpalsDropTextbox
from ..qt_extensions.QLine import QHLine, QVLine
from .. import QpalsModuleBase
from ..QpalsParameter import QpalsParameter

class QpalsWSM:
    def __init__(self, project, layerlist, iface):
        self.tabs = None
        self.project = project
        self.layerlist = layerlist
        self.iface = iface
        self.WSMProj = QpalsWSMProject()


    def createWidget(self):
        self.widget = QtWidgets.QSplitter()

        # Form
        boxleft = QtWidgets.QVBoxLayout()
        loadDir = QtWidgets.QPushButton("load")
        newProj = QtWidgets.QPushButton("new")
        newProj.clicked.connect(self.newProject)
        loadDir.clicked.connect(self.loadProject)
        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(loadDir)
        hbox2.addWidget(newProj)
        boxleft.addLayout(hbox2)
        self.prjBox = QtWidgets.QGroupBox("Project settings")
        self.prjBox.setEnabled(False)
        formL = QtWidgets.QFormLayout()
        self.prjBox.setLayout(formL)
        self.odmText = QpalsDropTextbox(layerlist=self.layerlist)
        self.odmText.currentTextChanged.connect(self.odmFileChanged)
        formL.addRow("odm", self.odmText)
        self.axisText = QpalsDropTextbox(layerlist=self.layerlist, filterrex='.*[\.shp]')
        formL.addRow("axis shp", self.axisText)

        self.widthSpin = QtWidgets.QDoubleSpinBox()
        self.widthSpin.setValue(15)
        self.widthSpin.setSingleStep(0.1)
        self.widthSpin.setRange(1, 50)
        self.widthSpin.setSuffix(" m")
        formL.addRow("sec width", self.widthSpin)

        self.depthSpin = QtWidgets.QDoubleSpinBox()
        self.depthSpin.setValue(5)
        self.depthSpin.setSingleStep(0.1)
        self.depthSpin.setRange(1, 50)
        self.depthSpin.setSuffix(" m")
        formL.addRow("sec depth", self.depthSpin)

        self.overlapSpin = QtWidgets.QDoubleSpinBox()
        self.overlapSpin.setValue(0)
        self.overlapSpin.setSingleStep(1)
        self.overlapSpin.setRange(0, 100)
        self.overlapSpin.setSuffix("%")
        formL.addRow("sec overlap", self.overlapSpin)

        self.attrSel = QtWidgets.QComboBox()
        formL.addRow("attribute", self.attrSel)

        self.shdText = QpalsDropTextbox(layerlist=self.layerlist)
        createShd = QtWidgets.QPushButton("create shading")
        createShd.clicked.connect(self.createShd)
        formL.addRow(createShd)
        formL.addRow("shd", self.shdText)
        self.secText = QpalsDropTextbox(layerlist=self.layerlist)
        self.secText.setPlaceholderText("drop or create shading...")
        createSec = QtWidgets.QPushButton("save && create sections")
        createSec.clicked.connect(self.createSec)
        formL.addRow(createSec)
        self.progress = QtWidgets.QProgressBar()
        formL.addRow(self.progress)
        boxleft.addWidget(self.prjBox)
        modeBox = QtWidgets.QGroupBox("Mode")
        modeBoxL = QtWidgets.QFormLayout()
        modeBox.setLayout(modeBoxL)
        self.modeGrp = QtWidgets.QButtonGroup()
        for mode in ['linear (1,2,3...)', 'alternating (farthest sampling)']:
            btn = QtWidgets.QRadioButton(mode)
            modeBoxL.addRow(btn)
            self.modeGrp.addButton(btn)
            if mode.startswith('alternating'):
                btn.setChecked(True)

        boxleft.addWidget(modeBox)
        saveBtn = QtWidgets.QPushButton("Save progress")
        boxleft.addWidget(saveBtn)
        expBtn = QtWidgets.QPushButton("Export WSM")
        boxleft.addWidget(expBtn)


        self.plotcenter = QtWidgets.QLabel("2D plot")
        self.plotcenter.setAlignment(QtCore.Qt.AlignCenter)
        vboxright = QtWidgets.QVBoxLayout()
        self.plotright = QtWidgets.QLabel("3D plot")
        self.plotright.setAlignment(QtCore.Qt.AlignCenter)

        # Section Grid Buttons
        secGrid = QtWidgets.QGridLayout()
        leftup = QtWidgets.QPushButton("↑")
        self.hleftLbl = QtWidgets.QLabel("h=")
        leftdown = QtWidgets.QPushButton("↓")
        rightup = QtWidgets.QPushButton("↑")
        self.hrightLbl = QtWidgets.QLabel("h=")
        rightdown = QtWidgets.QPushButton("↓")
        symCanvas = QtWidgets.QWidget()
        secGrid.addWidget(leftup, 0, 0)
        secGrid.addWidget(self.hleftLbl, 1, 0)
        secGrid.addWidget(leftdown, 2, 0)
        secGrid.addWidget(rightup, 0, 2)
        secGrid.addWidget(self.hrightLbl, 1, 2)
        secGrid.addWidget(rightdown, 2, 2)
        secGrid.addWidget(symCanvas, 0, 1, 3, 1)

        # Navigation Buttons
        navGrid = QtWidgets.QGridLayout()
        prevBtn = QtWidgets.QPushButton("prev")
        nextBtn = QtWidgets.QPushButton("next")
        incBox = QtWidgets.QSpinBox()
        currBox = QtWidgets.QSpinBox()
        pickBtn = QtWidgets.QPushButton("pick")
        self.status = QtWidgets.QLabel("Section 0/0: 0%")
        navGrid.addWidget(prevBtn, 0, 0)
        navGrid.addWidget(QtWidgets.QLabel("inc"), 0, 1)
        navGrid.addWidget(incBox, 0, 2)
        navGrid.addWidget(nextBtn, 0, 3)
        navGrid.addWidget(QtWidgets.QLabel("Current Index:"))
        navGrid.addWidget(currBox, 1, 1)
        navGrid.addWidget(pickBtn, 1, 3)
        navGrid.addWidget(self.status, 2, 0, 1, 4)


        vboxright.addWidget(self.plotright, stretch=1)
        vboxright.addWidget(QHLine())
        vboxright.addLayout(secGrid)
        vboxright.addWidget(QHLine())
        vboxright.addLayout(navGrid)

        boxleftw = QtWidgets.QWidget()
        boxleftw.setLayout(boxleft)
        vboxrightw = QtWidgets.QWidget()
        vboxrightw.setLayout(vboxright)
        self.widget.addWidget(boxleftw)
        self.widget.addWidget(self.plotcenter)
        self.widget.addWidget(vboxrightw)
        self.widget.setStretchFactor(0, 1)
        self.widget.setStretchFactor(1, 15)
        self.widget.setStretchFactor(2, 1)
        self.widget.setStyleSheet("QSplitter::handle{background-color: #CCCCCC;}")
        self.widget.setHandleWidth(2)

        return self.widget

    def loadProject(self):
        pass

    def newProject(self):
        self.prjBox.setEnabled(True)
        self.WSMProj = QpalsWSMProject()

    def createShd(self):
        pass

    def createSec(self):
        odmpath = self.odmText.text()
        axispath = self.axisText.text()
        if not os.path.exists(odmpath):
            QtWidgets.QMessageBox("Error", "Odm file not found.")
            return
        if not os.path.exists(axispath):
            QtWidgets.QMessageBox("Error", "Axis file not found.")
            return
        outpath = QtWidgets.QFileDialog.getSaveFileName(caption="Select output file", filter="*.qpalsWSM")

        self.WSMProj.odmpath = odmpath
        self.WSMProj.axispath = axispath
        self.WSMProj.savepath = outpath[0]
        self.WSMProj.shdpath = self.shdText.text()
        self.WSMProj.overlap = self.overlapSpin.value()
        self.WSMProj.depth = self.depthSpin.value()
        self.WSMProj.width = self.widthSpin.value()

        self.prjBox.setEnabled(False)
        module = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(self.project.opalspath, "opalsSection.exe"),
                                                 QpalsProject=self.project)
        infile = QpalsParameter('inFile', odmpath, None, None, None, None, None)
        axisfile = QpalsParameter('axisFile', axispath, None, None, None, None, None)
        attribute = QpalsParameter('attribute', self.attrSel.currentText(), None, None, None, None, None)
        overlap = QpalsParameter('overlap', str(self.overlapSpin.value() / 100), None, None, None, None, None)
        thickness = QpalsParameter('patchSize', '%s;%s' % (self.widthSpin.value(), self.depthSpin.value()),
                                   None, None, None, None, None)

        outParamFileH = tempfile.NamedTemporaryFile(suffix='.xml', delete=True)
        self.outParamFile = outParamFileH.name
        outParamFileH.close()
        outParamFileParam = QpalsParameter('outParamFile', self.outParamFile, None, None, None, None,
                                                          None)
        module.params += [infile, axisfile, thickness, attribute, overlap, outParamFileParam]
        self.thread, self.worker = module.run_async(status=self.update_status, on_finish=self.parse_output,
                                                    on_error=self.sec_error)



    def sec_error(self, msg, e, inst):
        raise e

    def parse_output(self):
        dom = minidom.parse(self.outParamFile)
        parameters = dom.getElementsByTagName("Parameter")
        outGeoms = []
        for param in parameters:
            if param.attributes["Name"].value == "outGeometry":
                for val in param.getElementsByTagName("Val"):
                    outGeoms.append(val.firstChild.nodeValue)  # contains WKT for one section
        dom.unlink()
        geomCnt = len(outGeoms)
        for idx, outGeom in enumerate(outGeoms):
            geoms = ogr.CreateGeometryFromWkt(outGeom)
            trafo = [geoms.GetGeometryRef(0), geoms.GetGeometryRef(2)]
            aoi = geoms.GetGeometryRef(1)
            pointcloud = geoms.GetGeometryRef(3)
            xvec = []
            yvec = []
            zvec = []
            cvec = []
            attrcloud = None
            if geoms.GetGeometryCount() > 4:
                attrcloud = geoms.GetGeometryRef(4)
            for i in range(pointcloud.GetGeometryCount()):
                pt = pointcloud.GetGeometryRef(i)
                xvec.append(pt.GetX())
                yvec.append(pt.GetY())
                zvec.append(pt.GetZ())
                if attrcloud:
                    at = attrcloud.GetGeometryRef(i)
                    cvec.append(at.GetZ())
            currsec = QpalsWSMSection(pc=np.array([xvec, yvec, zvec, cvec]), aoi=aoi)
            self.WSMProj.sections.append(currsec)
        self.progress.setEnabled(False)
        self.WSMProj.save()

    def update_status(self, message):
        out_lines = [item for item in re.split("[\n\r\b]", message) if item]
        percentage = out_lines[-1]
        # print percentage
        if r"%" in percentage:
            perc = QpalsModuleBase.get_percentage(percentage)
            self.progress.setValue(int(perc))

    def saveProgress(self):
        pass

    def exportWSM(self):
        pass

    def odmFileChanged(self, odmFile):
        pass

    def secFileChanged(self, secFile):
        pass

    def gotoSec(self, idx=None):
        pass

class QpalsWSMProject:
    def __init__(self, savepath=None, odmpath=None, axispath=None, shdpath=None,
                 width=None, depth=None, overlap=None):
        self.savepath = savepath
        self.odmpath = odmpath
        self.axispath = axispath
        self.shdpath = shdpath
        self.width = width
        self.depth = depth
        self.overlap = overlap
        self.sections = []

    def save(self):
        sec_temp = copy.deepcopy(self.sections)
        #self.sections = None
        with open(self.savepath, 'wb') as f:
            pickle.dump(self, f)
            #np.savez(self.savepath.replace('.qpalsWSM', '.qpalsWSM.data'), *sec_temp)
        self.sections = sec_temp

    @staticmethod
    def load(from_path):
        with open(from_path, 'rb') as f:
            obj = pickle.load(f)
            obj.sections = np.load(from_path.replace('.qpalsWSM', '.qpalsWSM.data'))
            return obj

class QpalsWSMSection:
    def __init__(self, pc, aoi, status='never', left_h=None, left_x=None, right_h=None, right_x=None):
        self.pc = pc
        self.aoi = aoi.ExportToWkb()
        self.status = status
        self.left_h = left_h
        self.left_x = left_x
        self.right_h = right_h
        self.right_x = right_x

    def aoi_as_ogr(self):
        return ogr.CreateGeometryFromWkb(self.aoi)
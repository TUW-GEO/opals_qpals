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
from qgis.gui import QgsRubberBand
from qgis.core import QgsPointXY, QgsGeometry

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.lines as lines

from ..qt_extensions.QpalsDropTextbox import QpalsDropTextbox
from ..qt_extensions.QLine import QHLine, QVLine
from ..modules.QpalsAttributeMan import getAttributeInformation
from .. import QpalsModuleBase
from ..QpalsParameter import QpalsParameter


class QpalsWSM(QtWidgets.QSplitter):
    colors = {
        0: QtGui.QColor(0, 128, 255),  # never seen --> blue
        1: QtGui.QColor(0, 255, 128),  # edited --> green
        -1: QtGui.QColor(255, 128, 128)  # current --> red
    }
    linecolors = {
        0: 'b',
        1: 'g',
        -1: 'r'
    }

    def __init__(self, project, layerlist, iface, *args, **kwargs):
        super(QpalsWSM, self).__init__(*args, **kwargs)
        self.tabs = None
        self.project = project
        self.layerlist = layerlist
        self.iface = iface
        self.WSMProj = QpalsWSMProject()
        self.sectionsRbs = []
        self.currSecRb = None
        self.lastSec = 0
        self.dragStart = (0, 0)
        self.dragEnd = (0, 0)
        self.zoomStart = (0, 0)
        self.dragLine = None

    def createWidget(self):
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
        saveBtn.clicked.connect(self.saveProgress)
        boxleft.addWidget(saveBtn)
        expBtn = QtWidgets.QPushButton("Export WSM")
        boxleft.addWidget(expBtn)

        # center figure
        figure = plt.figure()
        centerbox = QtWidgets.QVBoxLayout()
        self.plotcenter = FigureCanvas(figure)
        self.axcenter = figure.add_subplot(111)
        figure.subplots_adjust(left=0, right=1, top=0.99, bottom=0.01)
        #manager, canvas = figure.canvas.manager, figure.canvas
        #canvas.mpl_disconnect(manager.key_press_handler_id)  # remove default key bindings (ctrl+w = close)
        #cid = self.plotcenter.mpl_connect('key_press_event', self.keyPressed)
        cid2 = self.plotcenter.mpl_connect('button_press_event', self.mousePressed)
        cid2 = self.plotcenter.mpl_connect('motion_notify_event', self.mouseMoved)
        cid3 = self.plotcenter.mpl_connect('button_release_event', self.mouseReleased)
        cid4 = self.plotcenter.mpl_connect('scroll_event', self.mouseScrolled)

        #toolbar = NavigationToolbar(self.plotcenter, self.widget)
        centerbox.addWidget(self.plotcenter)
        #centerbox.addWidget(toolbar)
        centerw = QtWidgets.QWidget()
        centerw.setLayout(centerbox)


        # right figure
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
        nextBtn.clicked.connect(self.nextSec)
        self.incbox = QtWidgets.QSpinBox()
        self.incbox.setMinimum(1)
        self.currbox = QtWidgets.QSpinBox()
        self.currbox.valueChanged.connect(self.currSecChanged)
        self.skipSeen = QtWidgets.QCheckBox("Skip already seen sections")
        self.skipSeen.setChecked(True)
        pickBtn = QtWidgets.QPushButton("pick")
        self.status = QtWidgets.QLabel("Section 0/0: 0%")
        navGrid.addWidget(prevBtn, 0, 0)
        navGrid.addWidget(QtWidgets.QLabel("inc"), 0, 1)
        navGrid.addWidget(self.incbox, 0, 2)
        navGrid.addWidget(nextBtn, 0, 3)
        navGrid.addWidget(self.skipSeen, 1, 0, 1, 4)
        navGrid.addWidget(QtWidgets.QLabel("Current Index:"))
        navGrid.addWidget(self.currbox, 2, 1)
        navGrid.addWidget(pickBtn, 2, 3)
        navGrid.addWidget(self.status, 3, 0, 1, 4)


        vboxright.addWidget(self.plotright, stretch=1)
        vboxright.addWidget(QHLine())
        vboxright.addLayout(secGrid)
        vboxright.addWidget(QHLine())
        vboxright.addLayout(navGrid)

        boxleftw = QtWidgets.QWidget()
        boxleftw.setLayout(boxleft)
        vboxrightw = QtWidgets.QWidget()
        vboxrightw.setLayout(vboxright)
        self.addWidget(boxleftw)
        self.addWidget(centerw)
        self.addWidget(vboxrightw)
        self.setStretchFactor(0, 1)
        self.setStretchFactor(1, 15)
        self.setStretchFactor(2, 1)
        self.setStyleSheet("QSplitter::handle{background-color: #CCCCCC;}")
        self.setHandleWidth(2)


    def loadProject(self):
        inpath = QtWidgets.QFileDialog.getOpenFileName(caption="Select input file", filter="*.qpalsWSM")
        self.WSMProj = QpalsWSMProject.load(inpath[0])
        self.odmText.setText(self.WSMProj.odmpath)
        self.axisText.setText(self.WSMProj.axispath)
        self.shdText.setText(self.WSMProj.shdpath)
        self.depthSpin.setValue(self.WSMProj.depth)
        self.widthSpin.setValue(self.WSMProj.width)

        self.currbox.setMaximum(len(self.WSMProj.sections)-1)
        self.currSecChanged()

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
        self.currbox.setMaximum(len(self.WSMProj.sections)-1)
        self.currSecChanged()

    def update_status(self, message):
        out_lines = [item for item in re.split("[\n\r\b]", message) if item]
        percentage = out_lines[-1]
        # print percentage
        if r"%" in percentage:
            perc = QpalsModuleBase.get_percentage(percentage)
            self.progress.setValue(int(perc))

    def saveProgress(self):
        self.WSMProj.save()
        msg = QtWidgets.QMessageBox()


    def showSectionsInOverview(self):
        # clear existing rubberbands
        for rb in self.sectionsRbs:
            self.iface.mapCanvas().scene().removeItem(rb)
        self.sectionsRbs = []
        # add new rubberbands
        for id, sec in enumerate(self.WSMProj.sections):
            rb = QgsRubberBand(self.iface.mapCanvas(), False)
            rb_geom = QgsGeometry()
            rb_geom.fromWkb(sec.aoi)
            rb.setToGeometry(rb_geom, None)
            if id == self.currbox.value():
                fc = QtGui.QColor(self.colors[-1])
            else:
                fc = QtGui.QColor(self.colors[min(sec.status,1)])
            rb.setColor(fc)
            fc.setAlpha(128)
            rb.setFillColor(fc)
            rb.setWidth(1)
            self.sectionsRbs.append(rb)

    def exportWSM(self):
        pass

    def odmFileChanged(self, odmFile):
        attrs, _ = getAttributeInformation(odmFile, self.project)
        while self.attrSel.count() > 0:
            self.attrSel.removeItem(0)
        for attr in attrs:
            name = attr[0]
            self.attrSel.addItem(name)

    def secFileChanged(self, secFile):
        pass

    def gotoSec(self, idx):
        self.currbox.setValue(idx)

    def nextSec(self):
        if self.getCurrSec().status != 1:
            self.WSMProj.skipped_sections.append(self.currbox.value())
        if self.modeGrp.buttons()[0].isChecked():  # linear
            next_val = self.currbox.value() + self.incbox.value()
            while self.skipSeen.isChecked() and next_val in self.WSMProj.skipped_sections:
                next_val += self.incbox.value()
                if next_val >= len(self.WSMProj.sections):
                    next_val = 0
                    self.skipSeen.setChecked(False)
            self.gotoSec(next_val)
        elif self.modeGrp.buttons()[1].isChecked():  # farthest
            self.gotoSec(self.WSMProj.farthest_new_section(skip=self.skipSeen.isChecked()))

    def currSecChanged(self):
        self.showSectionsInOverview()
        self.lastSec = self.currbox.value()
        doneCount = 0
        totalCount = len(self.WSMProj.sections)-1
        for sec in self.WSMProj.sections:
            doneCount += 1 if sec.status > 0 else 0
        self.status.setText("Section %d/%d: %.2f%%" % (doneCount, totalCount, 100*doneCount/totalCount))
        self.show2DPlot()

    def show2DPlot(self):
        currsec = self.getCurrSec()
        xlim, ylim = self.axcenter.get_xlim(), self.axcenter.get_ylim()

        self.axcenter.cla()
        if len(currsec.pc[3]) > 0:
            self.axcenter.scatter(currsec.pc[0], currsec.pc[2], marker='o', s=1, c=currsec.pc[3], cmap='viridis')
        else:
            self.axcenter.scatter(currsec.pc[0], currsec.pc[2], marker='o', s=1)

        x1, h1, x2, h2 = self.WSMProj.estimate_level(self.currbox.value())
        self.dragLine = self.axcenter.plot([x1,x2], [h1,h2])[0]
        if all([currsec.left_h, currsec.left_x, currsec.right_h, currsec.right_x]):
            self.dragLine.set_xdata([currsec.left_x, currsec.right_x])
            self.dragLine.set_ydata([currsec.left_h, currsec.right_h])
            self.dragLine.set_linestyle("-")
            self.dragLine.set_color(self.linecolors[currsec.status])

        self.axcenter.set_axis_off()

        # reset lims if no points are left in visible area, for x and y separately
        if currsec.xrange[0] > xlim[0] > currsec.xrange[1] or currsec.xrange[0] > xlim[1] > currsec.xrange[1]:
            self.axcenter.set_xlim(xlim)

        if currsec.hrange[0] > ylim[0] > currsec.hrange[1] or currsec.hrange[0] > ylim[1] > currsec.hrange[1]:
            self.axcenter.set_ylim(ylim)

        self.plotcenter.draw()

    def close(self):
        for rb in self.sectionsRbs:
            self.iface.mapCanvas().scene().removeItem(rb)


    def mousePressed(self, e):
        if e.button == 1:
            self.dragStart = (e.xdata, e.ydata)
            self.dragLine.set_linestyle("--")
        elif e.button in [2,3]:
            self.dragStart = (e.xdata, e.ydata)
            self.zoomStart = [self.axcenter.get_xlim(), self.axcenter.get_ylim()]

    def mouseMoved(self, e):
        if e.button == 1:
            self.dragEnd = (e.xdata, e.ydata)
            self.dragLine.set_xdata([self.dragEnd[0], self.dragStart[0]])
            self.dragLine.set_ydata([self.dragEnd[1], self.dragStart[1]])
            self.dragLine.set_color(self.linecolors[-1])
        elif e.button == 2:
            xlim, ylim = self.zoomStart
            x_add = (self.dragStart[0] - e.xdata)
            y_add = (self.dragStart[1] - e.ydata)
            xlim = xlim + x_add
            ylim = ylim + y_add
            self.axcenter.set_xlim(xlim)
            self.axcenter.set_ylim(ylim)
        elif e.button == 3:
            xlim, ylim = self.zoomStart
            x_fac = 1 + (self.dragStart[0] - e.xdata) / (self.zoomStart[0][1] - self.zoomStart[0][0])
            y_fac = 1 + (self.dragStart[1] - e.ydata) / (self.zoomStart[1][1] - self.zoomStart[1][0])
            xlim = np.mean(xlim) + x_fac*(xlim - np.mean(xlim))
            ylim = np.mean(ylim) + y_fac*(ylim - np.mean(ylim))
            self.axcenter.set_xlim(xlim)
            self.axcenter.set_ylim(ylim)
        else:
            return
        self.plotcenter.draw()


    def mouseReleased(self, e):
        if e.button != 1:
            return
        widthL = min(e.xdata, self.dragStart[0])
        widthR = max(e.xdata, self.dragStart[0])

        heightL = e.ydata if e.xdata < self.dragStart[0] else self.dragStart[1]
        heightR = e.ydata if e.xdata >= self.dragStart[0] else self.dragStart[1]

        if self.dragStart[0] != e.xdata and self.dragStart[1] != e.ydata: # not just a click
            currsec = self.getCurrSec()
            currsec.left_x, currsec.right_x, currsec.left_h, currsec.right_h = widthL, widthR, heightL, heightR

        self.dragLine.set_linestyle("-")

    def mouseScrolled(self, e):
        dir = e.button

    def getCurrSec(self):
        return self.WSMProj.sections[self.currbox.value()]

    def keyPressEvent(self, event):
        if type(event) == QtGui.QKeyEvent:
            #here accept the event and do something
            print(event.key())
            if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
                print("Enter")
                self.getCurrSec().status = 1
                self.dragLine.set_color(self.linecolors[1])
            elif event.key() == QtCore.Qt.Key_Delete:
                self.getCurrSec().status = 0
                self.dragLine.set_color(self.linecolors[0])
            elif event.key() == QtCore.Qt.Key_PageDown:
                self.nextSec()
            self.plotcenter.draw()
            event.accept()
        else:
            event.ignore()

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
        self.skipped_sections = []

    def save(self):
        with open(self.savepath, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load(from_path):
        with open(from_path, 'rb') as f:
            obj = pickle.load(f)
            return obj

    def estimate_level(self, idx):
        # inverse distance weighting of sections that have status > 0:
        dist_vec = []
        left_x_vec = []
        left_h_vec = []
        right_x_vec = []
        right_h_vec = []
        for curridx, sec in enumerate(self.sections):
            if sec.status < 1 or curridx == idx:
                continue
            dist_vec.append(abs(idx - curridx))
            left_x_vec.append(sec.left_x)
            right_x_vec.append(sec.right_x)
            left_h_vec.append(sec.left_h)
            right_h_vec.append(sec.right_h)
        weights = 1/np.array(dist_vec)
        left_x = np.sum(np.array(left_x_vec) * weights) / np.sum(weights) if len(weights) > 2 else self.sections[idx].xrange[0]
        right_x = np.sum(np.array(right_x_vec) * weights) / np.sum(weights) if len(weights) > 2 else self.sections[idx].xrange[1]
        left_h = np.sum(np.array(left_h_vec) * weights) / np.sum(weights) if len(weights) > 2 else np.mean(self.sections[idx].hrange)
        right_h = np.sum(np.array(right_h_vec) * weights) / np.sum(weights) if len(weights) > 2 else np.mean(self.sections[idx].hrange)
        return (left_x, left_h, right_x, right_h)

    def farthest_new_section(self, skip):
        list_of_old_sections = np.array([idx for
                                         idx, sec in
                                         enumerate(self.sections) if sec.status > 0] +
                                        self.skipped_sections if skip else [])
        next_old_section = []
        if len(list_of_old_sections) == 0:
            return 0
        for idx in range(len(self.sections)):
            next_old_section.append(np.min(np.abs(idx - list_of_old_sections)))
        return np.argmax(np.array(next_old_section))



class QpalsWSMSection:
    def __init__(self, pc, aoi, status=0, left_h=None, left_x=None, right_h=None, right_x=None):
        """

        :param pc:
        :param aoi:
        :param status: 0 --> never seen; 1 --> seen; 2 --> seen and edited
        :param left_h:
        :param left_x:
        :param right_h:
        :param right_x:
        """
        self.pc = pc
        self.aoi = aoi.ExportToWkb()
        self.status = status
        self.left_h = left_h
        self.left_x = left_x
        self.right_h = right_h
        self.right_x = right_x
        self.hrange = [np.min(self.pc[2]), np.max(self.pc[2])]
        self.xrange = [np.min(self.pc[0]), np.max(self.pc[0])]

    def aoi_as_ogr(self):
        return ogr.CreateGeometryFromWkb(self.aoi)
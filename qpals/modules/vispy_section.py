"""
/***************************************************************************
Name			 	 : matplotlib_section
Description          : Supply a canvas and a dropdown for visualizing 3d sections in vispy
Date                 : 2018-03-19
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
from __future__ import print_function
import numpy as np
import vispy
vispy.set_log_level('warning')
from vispy import visuals, scene, gloo
from vispy.visuals import ColorBarVisual, MarkersVisual
from vispy.visuals.transforms import STTransform
from vispy.color import colormap
from vispy.color import Color, ColorArray
from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.core import QgsFeatureRequest, QgsGeometry
import ogr

class classesColorMap:
    colors = { # asprs standard classes
        0: [0.1, 0.1, 0.1],  # never classified
        1: [0.4, 0.4, 0.4],  # unclassified
        2: [0.7, 0.0, 0.7],  # ground
        3: [0.1, 0.7, 0.2],  # low veg
        4: [0.1, 0.6, 0.2],  # med veg
        5: [0.1, 0.5, 0.2],  # hi veg
        6: [1, 0, 0],  # building
        7: [1, 1, 1],  # lo point
        8: [1, 1, 0],  # hi point
        9: [0, 0, 1],  # water
    }

    def __init__(self):
        pass

    def __getitem__(self, items):
        colorlist = []
        for item in items:
            if item in classesColorMap.colors:
                colorlist.append(classesColorMap.colors[item])
            else:
                colorlist.append([0.5, 0.5, 1])
        return colorlist


class plotwindow(object):
    def __init__(self, project, iface=None, data=None, mins=None, maxes=None, linelayer=None, aoi=None, trafo=None):
        Scatter3D = scene.visuals.create_visual_node(visuals.MarkersVisual)
        Line3D = scene.visuals.create_visual_node(visuals.LineVisual)
        self.widg = QtWidgets.QWidget()
        self.canvas = scene.SceneCanvas(bgcolor=(1,1,1), parent=self.widg, resizable=True)
        #self.canvas.events.mouse_press.connect(self.canvasClicked)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'turntable'  # or try 'turntable', 'arcball'

        self.view.camera.fov = 45
        self.view.camera.pan_factor = 1000
        self.view.padding = 10

        self.p1 = Scatter3D(parent=self.view.scene)
        self.p1.picking = True
        self.p1.interactive = True
        self.l1 = Line3D(parent=self.view.scene, method='gl')
        self.l1.antialias = True
        self.p1.antialias = True
        self.p1.set_gl_state('translucent', blend=True, depth_test=True, blend_func=('src_alpha', 'one_minus_src_alpha'))

        self.project = project
        self.iface = iface
        self.data = data
        self.mins = mins
        self.maxes = maxes
        for coord in ['X', 'Y', 'Z']:
            self.mins[coord] = np.min(self.data[coord])
            self.maxes[coord] = np.max(self.data[coord])
        self.lines = None
        if linelayer and trafo:
            avgZ = np.mean(self.data['Z'])
            X1 = trafo[0].GetPoint(0)[0]
            Y1 = trafo[0].GetPoint(0)[1]
            transX = -X1
            transY = -Y1
            X2 = trafo[0].GetPoint(1)[0]
            Y2 = trafo[0].GetPoint(1)[1]
            phi = np.arctan2((Y2 - Y1), (X2 - X1))
            rot = np.array([[np.cos(phi), np.sin(phi)], [-np.sin(phi), np.cos(phi)]])
            x2 = trafo[1].GetPoint(0)[0]
            y2 = trafo[1].GetPoint(0)[1]
            self.lines = []
            self.connections = []
            nodecount = 0
            aoirect = QgsGeometry()
            aoirect.fromWkb(aoi.ExportToWkb())
            aoirect = aoirect.boundingBox()
            req = QgsFeatureRequest(aoirect)
            for feat in linelayer.getFeatures(req):
                geom = feat.geometry()
                wkb = geom.asWkb().data()
                ogeom = ogr.CreateGeometryFromWkb(wkb)
                usegeom = ogeom.Intersection(aoi.Buffer(2))
                if not usegeom:
                    print(ogeom.Intersection(aoi))
                    continue
                linelist = []
                if usegeom.GetGeometryType() in [ogr.wkbMultiLineString, ogr.wkbMultiLineString25D]:
                    for lineId in range(usegeom.GetGeometryCount()):
                        linelist.append(usegeom.GetGeometryRef(lineId))
                else:
                    linelist = [usegeom]

                for line in linelist:
                    for i in range(line.GetPointCount()):
                        pi = line.GetPoint(i)
                        xi = pi[0]
                        yi = pi[1]
                        zi = pi[2] if len(pi) > 2 else 0
                        p_loc = np.dot(rot, (np.array([xi, yi]).T + np.array([transX, transY]).T)) + np.array(
                            [x2, y2]).T
                        x_loc = p_loc[0]
                        y_loc = p_loc[1]
                        self.lines.append([x_loc, y_loc, zi])
                        self.connections.append([nodecount, nodecount + 1])
                        nodecount += 1
                    if self.connections:
                        self.connections.pop()
        self.lines = np.array(self.lines)
        self.ui = self.getUI()

        self.CM = None
        for cm_name in sorted(colormap.get_colormaps()):
            if not self.CM:
                self.CM = colormap.get_colormap(cm_name)
            self.CMbox.addItem(cm_name)
        self.CMbox.addItem('classes')
        self.CMbox.currentIndexChanged.connect(self.cmChanged)

        self.markerBox.addItems(["disc", "arrow", "ring", "clobber", "square", "diamond",
                                 "vbar", "hbar", "cross", "tailed_arrow",
                                 "x", "triangle_up", "triangle_down", "star"])
        self.markerBox.setCurrentIndex(0)
        self.markerBox.currentIndexChanged.connect(self.draw_new_plot)

        self.attrBox.addItems(sorted([m for m in self.data]))
        self.attrBox.currentIndexChanged.connect(self.attrChanged)
        self.attrBox.setCurrentIndex(self.attrBox.count()-1)


    def getUI(self):
        lay = QtWidgets.QVBoxLayout()
        self.widg.setLayout(lay)
        lay.addWidget(self.canvas.native, stretch=1)
        policy = self.widg.sizePolicy()
        policy.setVerticalStretch(1)
        self.widg.setSizePolicy(policy)
        self.toolbar = QtWidgets.QHBoxLayout()
        self.toolbar2 = QtWidgets.QHBoxLayout()
        lay.addLayout(self.toolbar)
        lay.addLayout(self.toolbar2)
        self.CMbox = QtWidgets.QComboBox()
        self.attrBox = QtWidgets.QComboBox()

        self.toolbar.addWidget(QtWidgets.QLabel("Attribute:"))
        self.toolbar.addWidget(self.attrBox)
        self.toolbar.addWidget(QtWidgets.QLabel("Colormap:"))
        self.toolbar.addWidget(self.CMbox)
        self.toolbar.addWidget(QtWidgets.QLabel("Min:"))
        self.scaleMin = QtWidgets.QLineEdit()
        self.scaleMin.editingFinished.connect(self.draw_new_plot)
        self.toolbar.addWidget(self.scaleMin)
        self.toolbar.addWidget(QtWidgets.QLabel("Max:"))
        self.scaleMax = QtWidgets.QLineEdit()
        self.scaleMax.editingFinished.connect(self.draw_new_plot)
        self.toolbar.addWidget(self.scaleMax)

        self.markerBox = QtWidgets.QComboBox()
        self.toolbar.addWidget(QtWidgets.QLabel("Marker:"))
        self.toolbar.addWidget(self.markerBox)
        self.markerSize = QtWidgets.QSpinBox()
        self.markerSize.setValue(2)
        self.markerSize.valueChanged.connect(self.draw_new_plot)
        self.toolbar.addWidget(QtWidgets.QLabel("Marker size:"))
        self.toolbar.addWidget(self.markerSize)
        self.bgColorBtn = QtWidgets.QPushButton('#FFFFFF')
        self.bgColorBtn.setStyleSheet('color: #FFFFFF')
        self.bgColorBtn.clicked.connect(self.bgColorPick)
        self.lineColorBtn = QtWidgets.QPushButton('#FF0000')
        self.lineColorBtn.setStyleSheet('color: #FF0000')
        self.lineColorBtn.clicked.connect(self.lineColorPick)

        self.toolbar2.addWidget(QtWidgets.QLabel("bg color:"))
        self.toolbar2.addWidget(self.bgColorBtn)

        self.toolbar2.addWidget(QtWidgets.QLabel("line color:"))
        self.toolbar2.addWidget(self.lineColorBtn)


        self.lineWidth = QtWidgets.QSpinBox()
        self.lineWidth.setValue(2)
        self.lineWidth.valueChanged.connect(self.draw_new_plot)
        self.toolbar2.addWidget(QtWidgets.QLabel("line width:"))
        self.toolbar2.addWidget(self.lineWidth)


        self.zex = QtWidgets.QDoubleSpinBox()
        self.zex.setValue(1)
        self.zex.setRange(0.1, 50)
        self.zex.setSingleStep(0.1)
        self.zex.setDecimals(1)
        self.zex.valueChanged.connect(self.draw_new_plot)
        self.toolbar2.addWidget(QtWidgets.QLabel("Z exagg."))
        self.toolbar2.addWidget(self.zex)

        self.toolbar.addStretch()
        self.toolbar2.addStretch()

        return self.widg

    def draw_new_plot(self):
        X = self.data['X']
        Y = self.data['Y']
        Z = self.data['Z']
        x_mean = np.mean(X)
        y_mean = np.mean(Y)
        z_mean = np.mean(Z)
        curr_attr = self.attrBox.currentText()
        offset = float(self.scaleMin.text())
        scale = float(self.scaleMax.text()) - float(self.scaleMin.text())
        c = self.colorify((self.data[curr_attr] - offset) / scale)
        X = X - x_mean
        Y = Y - y_mean
        Z = (Z - z_mean) * self.zex.value()
        self.canvas.bgcolor = self.bgColorBtn.text()
        self.p1.set_data(np.vstack((X,Y,Z)).T, face_color=c, symbol=self.markerBox.currentText(),
                         size=self.markerSize.value(), edge_color=None, edge_width=0)
        linesX = self.lines[:, 0] - x_mean
        linesY = self.lines[:, 1] - y_mean
        linesZ = (self.lines[:, 2] - z_mean) * self.zex.value()
        self.l1.set_data(np.vstack((linesX, linesY, linesZ)).T, connect=np.array(self.connections),
                         color=self.lineColorBtn.text(), width=self.lineWidth.value())

    def bgColorPick(self):
        color = QtWidgets.QColorDialog.getColor()
        self.bgColorBtn.setText(color.name())
        self.bgColorBtn.setStyleSheet('color: ' + color.name())
        self.draw_new_plot()

    def lineColorPick(self):
        color = QtWidgets.QColorDialog.getColor()
        self.lineColorBtn.setText(color.name())
        self.lineColorBtn.setStyleSheet('color: ' + color.name())
        self.draw_new_plot()

    def attrChanged(self, idx):
        name = str(self.attrBox.itemText(idx))
        self.scaleMin.setText(str(self.mins[name]))
        self.scaleMax.setText(str(self.maxes[name]))
        self.draw_new_plot()

    def cmChanged(self, idx):
        name = str(self.CMbox.itemText(idx))
        if name == 'classes':
            self.CM = classesColorMap()
        else:
            self.CM = colormap.get_colormap(name)
        self.draw_new_plot()

    def colorify(self, values):
        return self.CM[values]

    def close(self):
        self.ui.hide()
        self.ui = None
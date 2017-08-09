"""
/***************************************************************************
Name			 	 : matplotlib_section
Description          : Supply a canvas and a dropdown for visualizing 3d sections in matplotlib
Date                 : 2017-08-31
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

from PyQt4 import QtGui, QtCore
import matplotlib
import ogr
import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from mpl_toolkits.mplot3d import Axes3D


class plotwindow():
    def __init__(self, project, iface=None, data=None, mins=None, maxes=None, linelayer=None, aoi=None, trafo=None):
        self.project = project
        self.iface = iface
        self.data = data
        self.mins = mins
        self.maxes = maxes
        self.lines = None
        if linelayer and trafo:
            avgZ = np.mean(self.data['Z'])
            X1 = trafo[0].GetPoint(0)[0]
            Y1 = trafo[0].GetPoint(0)[1]
            transX = -X1
            transY = -Y1
            X2 = trafo[0].GetPoint(1)[0]
            Y2 = trafo[0].GetPoint(1)[1]
            phi = np.arctan2((Y2-Y1), (X2-X1))
            rot = np.array([[np.cos(phi), np.sin(phi)], [-np.sin(phi), np.cos(phi)]])
            x2 = trafo[1].GetPoint(0)[0]
            y2 = trafo[1].GetPoint(0)[1]
            self.lines = []
            for feat in linelayer.getFeatures():
                geom = feat.geometry()
                wkb = geom.asWkb()
                ogeom = ogr.CreateGeometryFromWkb(wkb)
                usegeom = ogeom.Intersection(aoi.Buffer(2))
                if not usegeom:
                    continue
                x = []
                y = []
                z = []
                for i in range(usegeom.GetPointCount()):
                    pi = usegeom.GetPoint(i)
                    xi = pi[0]
                    yi = pi[1]
                    zi = pi[2] if len(pi) > 2 else 0
                    p_loc = np.dot(rot, (np.array([xi, yi]).T + np.array([transX, transY]).T)) + np.array([x2, y2]).T
                    x_loc = p_loc[0]
                    y_loc = p_loc[1]
                    x.append(x_loc)
                    y.append(y_loc)
                    z.append(zi)
                self.lines.append([x, y, z])

        self.ui = self.getUI()
        #self.ui.show()
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.figure.subplots_adjust(left=0, right=1, top=0.99, bottom=0.01)
        self.curplot = self.ax.scatter(self.data['X'], self.data['Y'], self.data['Z'])
        self.figure.canvas.mpl_connect('pick_event', self.pointPicked)
        self.ax.view_init(0, 0)
        self.colorbar = None
        self.ann = None
        self.currattr = "Z"
        self.attrsel.setCurrentIndex(self.attrsel.findText('Z'))
        self.draw_new_plot()


    def getUI(self):
        ui = QtGui.QWidget()
        self.figure = plt.figure()
        self.mpl_canvas = FigureCanvas(self.figure)
        self.attrsel = QtGui.QComboBox()
        self.attrsel.addItems(sorted([m for m in self.data]))
        self.attrsel.currentIndexChanged.connect(self.draw_new_plot)
        self.scale_min = QtGui.QLineEdit("0")
        self.scale_min.setMinimumWidth(5)
        self.scale_min.textChanged.connect(self.draw_new_plot)
        self.scale_max = QtGui.QLineEdit("10")
        self.scale_max.setMinimumWidth(5)
        self.scale_max.textChanged.connect(self.draw_new_plot)
        self.colormap = QtGui.QComboBox()
        self.colormap.addItems(sorted(m for m in cm.datad))
        self.colormap.setCurrentIndex(self.colormap.findText("gist_earth"))
        self.colormap.currentIndexChanged.connect(self.draw_new_plot)
        self.marker = QtGui.QComboBox()
        self.marker.addItems(['.', ',', 'o', 'v', '^', '<', '>', '1', '2', '3', '4', '8', 's', 'p',
                              'P', '*', 'h', 'H', '+', 'x', 'X', 'D', 'd', '|', '_'])
        self.marker.setCurrentIndex(2)
        self.marker.currentIndexChanged.connect(self.draw_new_plot)
        self.markerSize = QtGui.QDoubleSpinBox()
        self.markerSize.setValue(0.5)
        self.markerSize.setRange(0.1, 50)
        self.markerSize.setSingleStep(0.1)
        self.markerSize.valueChanged.connect(self.draw_new_plot)
        self.lineSize = QtGui.QDoubleSpinBox()
        self.lineSize.setValue(1)
        self.lineSize.setRange(0.1, 20)
        self.lineSize.setSingleStep(0.1)
        self.lineSize.valueChanged.connect(self.draw_new_plot)
        self.zex = QtGui.QDoubleSpinBox()
        self.zex.setValue(1)
        self.zex.setRange(0.1, 50)
        self.zex.setSingleStep(0.1)
        self.zex.setDecimals(1)
        self.zex.valueChanged.connect(self.draw_new_plot)

        self.linecolor = QtGui.QPushButton("#000000")
        self.linecolor.clicked.connect(self.colorpicker)

        self.hb = QtGui.QHBoxLayout()
        self.hb2 = QtGui.QHBoxLayout()

        self.hb.addWidget(QtGui.QLabel("Select attribute:"))
        self.hb.addWidget(self.attrsel)
        self.hb.addWidget(QtGui.QLabel("Scale from:"))
        self.hb.addWidget(self.scale_min)
        self.hb.addWidget(QtGui.QLabel("Scale to:"))
        self.hb.addWidget(self.scale_max)
        self.hb.addStretch()

        self.hb2.addWidget(QtGui.QLabel("Colormap:"))
        self.hb2.addWidget(self.colormap)
        self.hb2.addWidget(QtGui.QLabel("Marker:"))
        self.hb2.addWidget(self.marker)
        self.hb2.addWidget(QtGui.QLabel("Marker size:"))
        self.hb2.addWidget(self.markerSize)
        self.hb2.addWidget(QtGui.QLabel("Line color:"))
        self.hb2.addWidget(self.linecolor)
        self.hb2.addWidget(QtGui.QLabel("Line width:"))
        self.hb2.addWidget(self.lineSize)
        self.hb2.addWidget(QtGui.QLabel("Z exagg.:"))
        self.hb2.addWidget(self.zex)
        self.hb2.addStretch()


        self.vb = QtGui.QVBoxLayout()
        self.vb.addWidget(self.mpl_canvas, 1)
        self.vb.addWidget(NavigationToolbar(self.mpl_canvas, ui))
        self.vb.addLayout(self.hb)
        self.vb.addLayout(self.hb2)

        ui.setLayout(self.vb)
        return ui

    def colorpicker(self):
        color = QtGui.QColorDialog.getColor()
        self.linecolor.setStyleSheet('color: %s' % color.name())
        self.linecolor.setText(color.name())
        self.draw_new_plot()

    def pointPicked(self, ev):
        if self.ann:
            self.ann.remove()
            self.ann = None
        if ev.mouseevent.button != 2:
            return
        x = self.data['X'][ev.ind[0]]
        y = self.data['Y'][ev.ind[0]]
        z = self.data['Z'][ev.ind[0]] * self.zex.value()
        str = "\n".join(["%s: %s" % (key, self.data[key][ev.ind[0]]) for key in self.data])
        self.ann = self.ax.text(x, y, z, str, zorder=1, color='k', size=8)
        self.figure.canvas.draw()

    def draw_new_plot(self):
        newattr = self.attrsel.currentText()
        if self.currattr == newattr:
            low = float(self.scale_min.text())
            hi = float(self.scale_max.text())
        elif newattr in ['X', 'Y', 'Z']:
            low = -10
            hi = 10
        else:
            low = float(self.mins[newattr])
            hi = float(self.maxes[newattr])
        self.scale_min.setText(str(low))
        self.scale_max.setText(str(hi))
        self.currattr = newattr
        colormap = self.colormap.currentText()
        self.ax.cla()
        self.ann = None
        if self.colorbar:
            self.colorbar.remove()
        X = self.data['X']
        Y = self.data['Y']
        Z = self.data['Z'] * self.zex.value()
        self.curplot = self.ax.scatter(X, Y, Z,
                        c=self.data[newattr], cmap=colormap,
                        clim=[low, hi], marker=self.marker.currentText(), s=self.markerSize.value(), picker=1)
        self.colorbar = self.figure.colorbar(self.curplot)
        if self.lines:
            for line in self.lines:
                self.ax.plot(line[0], line[1], line[2], color=self.linecolor.text(), linewidth=self.lineSize.value())

        max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max()
        Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (X.max() + X.min())
        Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (Y.max() + Y.min())
        Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][2].flatten() + 0.5 * (Z.max() + Z.min())
        # Comment or uncomment following both lines to test the fake bounding box:
        for xb, yb, zb in zip(Xb, Yb, Zb):
            self.ax.plot([xb], [yb], [zb], 'w')

        self.ax.set_axis_off()
        self.figure.canvas.draw()


    def close(self):
        self.ui.hide()
        self.ui = None

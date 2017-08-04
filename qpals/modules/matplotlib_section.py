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


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=7, height=6, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111, projection='3d')
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)



class plotwindow():
    def __init__(self, project, iface=None, data=None, mins=None, maxes=None, linelayer=None, aoi=None, trafo=None):
        self.project = project
        self.iface = iface
        self.data = data
        self.mins = mins
        self.maxes = maxes

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
        self.ui.show()
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.figure.subplots_adjust(left=0, right=1, top=0.99, bottom=0.01)
        self.curplot = self.ax.scatter(self.data['X'], self.data['Y'], self.data['Z'])
        self.ax.view_init(0, 90)
        self.colorbar = None
        self.currattr = "Z"
        self.attrsel.setCurrentIndex(self.attrsel.findText('Z'))
        self.draw_new_plot()


    def getUI(self):
        ui = QtGui.QDialog()
        self.figure = plt.figure()
        self.mpl_canvas = FigureCanvas(self.figure)
        self.attrsel = QtGui.QComboBox()
        self.attrsel.addItems(sorted([m for m in self.data]))
        self.attrsel.currentIndexChanged.connect(self.draw_new_plot)
        self.scale_min = QtGui.QLineEdit("0")
        self.scale_min.textChanged.connect(self.draw_new_plot)
        self.scale_max = QtGui.QLineEdit("10")
        self.scale_max.textChanged.connect(self.draw_new_plot)
        self.colormap = QtGui.QComboBox()
        self.colormap.addItems(sorted(m for m in cm.datad))
        self.colormap.setCurrentIndex(self.colormap.findText("gist_earth"))
        self.colormap.currentIndexChanged.connect(self.draw_new_plot)
        self.closebtn = QtGui.QPushButton("Close")

        self.hb = QtGui.QHBoxLayout()

        self.hb.addWidget(QtGui.QLabel("Select attribute:"))
        self.hb.addWidget(self.attrsel)
        self.hb.addWidget(QtGui.QLabel("Scale from:"))
        self.hb.addWidget(self.scale_min)
        self.hb.addWidget(QtGui.QLabel("Scale to:"))
        self.hb.addWidget(self.scale_max)
        self.hb.addWidget(QtGui.QLabel("Colormap:"))
        self.hb.addWidget(self.colormap)
        self.hb.addStretch()
        self.hb.addWidget(self.closebtn)

        self.vb = QtGui.QVBoxLayout()
        self.vb.addWidget(self.mpl_canvas, 1)
        self.vb.addWidget(NavigationToolbar(self.mpl_canvas, ui))
        self.vb.addLayout(self.hb)

        ui.setLayout(self.vb)
        return ui

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
        if self.colorbar:
            self.colorbar.remove()
        self.curplot = self.ax.scatter(self.data['X'], self.data['Y'], self.data['Z'],
                        c=self.data[newattr], cmap=colormap,
                        clim=[low, hi])
        self.colorbar = self.figure.colorbar(self.curplot)
        for line in self.lines:
            self.ax.plot(line[0], line[1], line[2], 'k-')
        self.ax.set_axis_off()
        self.ax.autoscale_view(True, True, True)
        self.ax.axis('equal')


    def close(self):
        self.ui.hide()
        self.ui = None

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
from vispy import visuals, scene, gloo
from vispy.visuals import ColorBarVisual, MarkersVisual
from vispy.visuals.transforms import STTransform
from vispy.color import colormap
from vispy.color import Color, ColorArray
from qgis.PyQt import QtWidgets, QtCore, QtGui


class plotwindow(object):
    def __init__(self, project, iface=None, data=None, mins=None, maxes=None, linelayer=None, aoi=None, trafo=None):
        Scatter3D = scene.visuals.create_visual_node(visuals.MarkersVisual)
        Line3D = scene.visuals.create_visual_node(visuals.LineVisual)
        self.canvas = scene.SceneCanvas(keys='interactive', bgcolor=(0.4,0.4,0.4))
        #self.canvas.events.mouse_press.connect(self.canvasClicked)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'turntable'  # or try 'turntable', 'arcball'

        self.view.camera.fov = 45
        self.view.camera.pan_factor = 1000
        self.view.padding = 10

        self.p1 = Scatter3D(parent=self.view.scene)
        self.p1.picking = True
        self.p1.interactive = True
        self.l1 = Line3D(parent=self.view.scene)
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
                    x = []
                    y = []
                    z = []
                    for i in range(line.GetPointCount()):
                        pi = line.GetPoint(i)
                        xi = pi[0]
                        yi = pi[1]
                        zi = pi[2] if len(pi) > 2 else 0
                        p_loc = np.dot(rot, (np.array([xi, yi]).T + np.array([transX, transY]).T)) + np.array(
                            [x2, y2]).T
                        x_loc = p_loc[0]
                        y_loc = p_loc[1]
                        x.append(x_loc)
                        y.append(y_loc)
                        z.append(zi)
                    self.lines.append([x, y, z])
        self.ui = self.getUI()

    def getUI(self):
        widg = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout()
        widg.setLayout(lay)
        lay.addWidget(self.canvas.native, stretch=1)
        return widg

    def draw_new_plot(self):
        X = self.data['X']
        Y = self.data['Y']
        Z = self.data['Z']
        print('XYZ')
        X = X - np.mean(X)
        Y = Y - np.mean(Y)
        Z = Z - np.mean(Z)
        self.p1.set_data([X,Y,Z], face_color='white', symbol='o', size=3, edge_color=None, edge_width=0)

    def close(self):
        pass
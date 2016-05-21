__author__ = 'lukas'
from .. import modules, test
import os

# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

def show_as_boundingbox(filename):
    try:
        os.remove(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\log\opalsLog.xml')
    except OSError:
        pass
    info = modules.Info.Info.Info(logpath=r'C:\Users\Lukas\.qgis2\python\plugins\qpals\log\opalsLog.xml')
    info.set_inFile(filename)
    QgsMessageLog.logMessage("Visualizing:"+filename, 'qpals', QgsMessageLog.INFO)
    subp = info.run()
    subp.wait()
    logInst = test.logparse.parse_log(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\log\opalsLog.xml')
    logInst.run()
    min = filter(None,logInst.output["Minimum X-Y-Z"].strip().split(" "))
    max = filter(None,logInst.output["Maximum X-Y-Z"].strip().split(" "))
    QgsMessageLog.logMessage("min:"+str(min), 'qpals', QgsMessageLog.INFO)
    QgsMessageLog.logMessage("max:"+str(max), 'qpals', QgsMessageLog.INFO)
    minx = float(min[0])
    maxx = float(max[0])
    miny = float(min[1])
    maxy = float(max[1])
    point1 = QgsPoint(minx, miny)
    point2 = QgsPoint(minx, maxy)
    point3=  QgsPoint(maxx,maxy)
    point4 = QgsPoint(maxx,miny)
    layer =  QgsVectorLayer("Polygon", filename.split(os.sep)[-1] , "memory")
    pr = layer.dataProvider()
    poly = QgsFeature()
    points = [point1,point2,point3,point4]
    poly.setGeometry(QgsGeometry.fromPolygon([points]))
    pr.addFeatures([poly])
    layer.updateExtents()
    QgsMapLayerRegistry.instance().addMapLayers([layer])

def show_as_zcolor(filename):
    grid = modules.Grid.Grid.Grid()
    grid.set_inFile(filename)
    grid.set_outFile(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\tmp\grid.tif')
    grid.run().wait()
    zcolor = modules.ZColor.ZColor.ZColor()
    zcolor.set_inFile(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\tmp\grid.tif')
    zcolor_file = find_next_free_filename(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\tmp\zcolor%s.tif')
    zcolor.set_outFile(zcolor_file)
    zcolor.run().wait()
    layer = QgsRasterLayer(zcolor_file,filename.split(os.sep)[-1])
    QgsMapLayerRegistry.instance().addMapLayers([layer])

def show_as_alphashape(filename, coarse=True):
    bounds = modules.getFromName('Bounds')
    bounds.set_inFile(filename)
    bounds.set_boundsType('alphaShape')
    shapefile = find_next_free_filename(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\tmp\alphashape%s.shp')
    bounds.set_outFile(shapefile)
    bounds.run().wait()
    layer = QgsVectorLayer(shapefile, filename.split(os.sep)[-1], 'ogr')
    QgsMapLayerRegistry.instance().addMapLayers([layer])

def show_as_convexhull(filename, coarse=True):
    bounds = modules.getFromName('Bounds')
    bounds.set_inFile(filename)
    bounds.set_boundsType('convexHull')
    shapefile = find_next_free_filename(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\tmp\alphashape%s.shp')
    bounds.set_outFile(shapefile)
    bounds.run().wait()
    layer = QgsVectorLayer(shapefile, filename.split(os.sep)[-1], 'ogr')
    QgsMapLayerRegistry.instance().addMapLayers([layer])

def show_as_oriented_rectange(filename, coarse=True):
    bounds = modules.getFromName('Bounds')
    bounds.set_inFile(filename)
    bounds.set_boundsType('minimumRectangle')
    shapefile = find_next_free_filename(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\tmp\alphashape%s.shp')
    bounds.set_outFile(shapefile)
    bounds.run().wait()
    layer = QgsVectorLayer(shapefile, filename.split(os.sep)[-1], 'ogr')
    QgsMapLayerRegistry.instance().addMapLayers([layer])

def find_next_free_filename(filename):
    ind = 0
    while True:
        if not os.path.isfile(filename % ind):
            return filename % ind
        else:
            ind +=1
from __future__ import print_function
from builtins import range
import ogr
import os, sys, glob
import numpy as np
from qgis.PyQt import QtCore
from qgis.core import QgsPoint, QgsRaster

class RunWorker(QtCore.QObject):
    def __init__(self, SOURCE_LINES, tempf, dtm, dtm_thres, split_size, max_elements):
        QtCore.QObject.__init__(self)
        self.SOURCE_LINES = SOURCE_LINES
        self.tempf = tempf
        self.split_size = split_size
        self.max_elements = max_elements
        self.dtm = dtm
        self.dtm_thres = dtm_thres

    def run(self):
        try:
            main(self.SOURCE_LINES, self.tempf, self.split_size, self.max_elements, self.progress, self.dtm, self.dtm_thres)
        except Exception as e:
            import traceback
            traceback.print_exc()
            #print "Error:", str(e)
        ret = 1
        self.finished.emit(ret)

    finished = QtCore.pyqtSignal(int)
    progress = QtCore.pyqtSignal(float)


def main(SOURCE_LINES, tempf, split_size, max_elements, progressslot=None, dtm=None, dtmThres=0):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if not os.path.exists(tempf):
        os.mkdir(tempf)

    collected_file = os.path.join(tempf, "collected.shp")
    if os.path.exists(collected_file):
        driver.DeleteDataSource(collected_file)
    dsOutC = driver.CreateDataSource(collected_file)
    outLayerC = dsOutC.CreateLayer("collected", geom_type=ogr.wkbLineString)
    fDefC = outLayerC.GetLayerDefn()

    ang_list = []
    doublenode_list = []
    dtm_list = []

    # if source.shp is not a file, use it as regexp pattern
    for input_file in glob.glob(SOURCE_LINES):
        dsIn = driver.Open(input_file, 0)  # 0 means read-only
        layerIn = dsIn.GetLayer()
        for feat in layerIn:
            geom_ref = feat.GetGeometryRef()
            if geom_ref is not None:
                for i in range(0, geom_ref.GetPointCount()):
                    if i < geom_ref.GetPointCount()-1:
                        pt1 = list(geom_ref.GetPoint(i))
                        pt2 = list(geom_ref.GetPoint(i+1))
                        del pt1[2]
                        del pt2[2]
                        outGeom = ogr.Geometry(ogr.wkbLineString)
                        outGeom.AddPoint(*pt1)
                        outGeom.AddPoint(*pt2)
                        outFeat = ogr.Feature(fDefC)
                        outFeat.SetGeometry(outGeom)
                        outLayerC.CreateFeature(outFeat)
                        outFeat = None
                        if (pt1 == pt2):
                            doublenode_list.append(pt1)
                        if i > 0:
                            pt0 = list(geom_ref.GetPoint(i-1))
                            del pt0[2]
                            v10 = np.array([pt0[i]-pt1[i] for i in range(len(pt1))])
                            v12 = np.array([pt2[i]-pt1[i] for i in range(len(pt1))])
                            v10n = np.linalg.norm(v10)
                            v12n = np.linalg.norm(v12)
                            if v10n == 0 or v12n == 0:
                                continue
                            v10u = v10/v10n
                            v12u = v12/v12n
                            ang = np.arccos(np.clip(np.dot(v10u, v12u), -1.0, 1.0)) * 180/np.pi
                            if ang <= 90:  # spitze winkel
                                ang_list.append([pt1, ang])
                    if dtm:
                        pt = list(geom_ref.GetPoint(i))
                        rlayer = dtm
                        dx = rlayer.rasterUnitsPerPixelX()
                        dy = rlayer.rasterUnitsPerPixelY()
                        xpos = pt[0]
                        ypos = pt[1]
                        # assume pixel = center
                        xll = rlayer.extent().xMinimum() + 0.5 * dx
                        yll = rlayer.extent().yMinimum() + 0.5 * dy
                        xoffs = (pt[0] - xll) % dx
                        yoffs = (pt[1] - yll) % dy
                        dtm_val_ll = rlayer.dataProvider().identify(QgsPoint(xpos - dx / 2, ypos - dy / 2),
                                                                    QgsRaster.IdentifyFormatValue).results()[1]
                        dtm_val_ur = rlayer.dataProvider().identify(QgsPoint(xpos + dx / 2, ypos + dy / 2),
                                                                    QgsRaster.IdentifyFormatValue).results()[1]
                        dtm_val_lr = rlayer.dataProvider().identify(QgsPoint(xpos + dx / 2, ypos - dy / 2),
                                                                    QgsRaster.IdentifyFormatValue).results()[1]
                        dtm_val_ul = rlayer.dataProvider().identify(QgsPoint(xpos - dx / 2, ypos + dy / 2),
                                                                    QgsRaster.IdentifyFormatValue).results()[1]
                        if all([dtm_val_ll, dtm_val_lr, dtm_val_ul, dtm_val_ur]):
                            a00 = dtm_val_ll
                            a10 = dtm_val_lr - dtm_val_ll
                            a01 = dtm_val_ul - dtm_val_ll
                            a11 = dtm_val_ur + dtm_val_ll - (dtm_val_lr + dtm_val_ul)
                            dtm_bilinear = a00 + a10 * xoffs + a01 * yoffs + a11 * xoffs * yoffs
                            if abs(pt[2] - dtm_bilinear) > dtmThres:
                                addPoint = True
                                for (p, v) in dtm_list:
                                    if p[0] == pt[0] and p[1] == pt[1]:
                                        addPoint=False
                                        break
                                if addPoint:
                                    dtm_list.append([pt, (dtm_bilinear-pt[2])])


    SOURCE_LINES = collected_file
    outLayerC = None
    dsOutC = None


    PROBLEMS_NAME = "problems.shp"
    ERROR_NAME = "errors.shp"

    if os.path.exists(os.path.join(tempf, PROBLEMS_NAME)):
        driver.DeleteDataSource(os.path.join(tempf, PROBLEMS_NAME))

    if os.path.exists(os.path.join(tempf, ERROR_NAME)):
        driver.DeleteDataSource(os.path.join(tempf, ERROR_NAME))

    # open output file for intersection points
    dsOutI = driver.CreateDataSource(os.path.join(tempf, PROBLEMS_NAME))
    outLayerI = dsOutI.CreateLayer(PROBLEMS_NAME[:-4], geom_type=ogr.wkbMultiPoint)
    type_field = ogr.FieldDefn("TYPE", ogr.OFTString)
    type_field.SetWidth(24)
    value_field = ogr.FieldDefn("VAL", ogr.OFTReal)
    value_field.SetPrecision(3)
    value_field.SetWidth(10)
    outLayerI.CreateField(type_field)
    outLayerI.CreateField(value_field)
    fDefI = outLayerI.GetLayerDefn()
    # open output file for error areas (>max_elements geoms)
    dsOutE = driver.CreateDataSource(os.path.join(tempf, ERROR_NAME))
    outLayerE = dsOutE.CreateLayer(ERROR_NAME[:-4], geom_type=ogr.wkbPolygon)
    fDefE = outLayerE.GetLayerDefn()

    # open input file
    dsIn = driver.Open(SOURCE_LINES, 0) # 0 means read-only
    try:
        dsIn.ExecuteSQL("CREATE SPATIAL INDEX ON %s"%os.path.basename(SOURCE_LINES[:-4]))
    except:
        pass
    layerIn = dsIn.GetLayer()

    areas = []
    if split_size > 0:
        (xmin, xmax, ymin, ymax) = layerIn.GetExtent()
        xcurr = xmin
        i = 0
        while xcurr < xmax:
            ycurr = ymin
            while ycurr < ymax:
                i += 1
                rect = ogr.Geometry(ogr.wkbPolygon)
                ring = ogr.Geometry(ogr.wkbLinearRing)
                ring.AddPoint(xcurr, ycurr)
                ring.AddPoint(xcurr + split_size, ycurr)
                ring.AddPoint(xcurr + split_size, ycurr + split_size)
                ring.AddPoint(xcurr, ycurr + split_size)
                ring.AddPoint(xcurr, ycurr)
                rect.AddGeometry(ring)
                areas.append(rect)
                ycurr += split_size
            xcurr += split_size
    else:
        areas.append(None)


    for (pt, val) in ang_list:
        outFeat = ogr.Feature(fDefI)
        outFeat.SetField("TYPE", "angle")
        outFeat.SetField("VAL", val)
        geom = ogr.Geometry(ogr.wkbMultiPoint)
        pgeom = ogr.Geometry(ogr.wkbPoint)
        pgeom.AddPoint(*pt)
        geom.AddGeometry(pgeom)
        outFeat.SetGeometryDirectly(geom)
        outLayerI.CreateFeature(outFeat)
        outFeat = None

    for (pt, val) in dtm_list:
        outFeat = ogr.Feature(fDefI)
        outFeat.SetField("TYPE", "distance")
        outFeat.SetField("VAL", val)
        geom = ogr.Geometry(ogr.wkbMultiPoint)
        pgeom = ogr.Geometry(ogr.wkbPoint)
        pgeom.AddPoint(*pt)
        geom.AddGeometry(pgeom)
        outFeat.SetGeometryDirectly(geom)
        outLayerI.CreateFeature(outFeat)
        outFeat = None

    for pt in doublenode_list:
        outFeat = ogr.Feature(fDefI)
        outFeat.SetField("TYPE", "double node")
        geom = ogr.Geometry(ogr.wkbMultiPoint)
        pgeom = ogr.Geometry(ogr.wkbPoint)
        pgeom.AddPoint(*pt)
        geom.AddGeometry(pgeom)
        outFeat.SetGeometryDirectly(geom)
        outLayerI.CreateFeature(outFeat)
        outFeat = None

    k = len(areas)
    counts = {
        'intersection': 0,
        'double lines': 0,
        'overlap': 0,
        'close': 0,
        'errors': 0,
    }
    for (j, area) in enumerate(areas):
        layerIn.ResetReading()
        layerIn.SetSpatialFilter(area)

        geometries = []
        if progressslot:
            progressslot.emit(j*100./k)
        for feat in layerIn:
            geomref = feat.GetGeometryRef()
            geometries.append(geomref.Clone())
        while len(geometries) > 0:
            currgeom = geometries.pop(0)
            i = len(geometries)
            if i > max_elements:
                f = ogr.Feature(fDefE)
                f.SetGeometry(area)
                outLayerE.CreateFeature(f)
                f = None
                geometries = []
                counts['errors'] += 1
                continue
            for comparegeom in geometries:
                if currgeom.Intersects(comparegeom):
                    if currgeom.Crosses(comparegeom):
                        outFeat = ogr.Feature(fDefI)
                        outFeat.SetField("TYPE", "intersection")
                        outFeat.SetGeometry(ogr.ForceToMultiPoint(currgeom.Intersection(comparegeom)))
                        outLayerI.CreateFeature(outFeat)
                        outFeat = None
                        counts['intersection'] += 1
                    if currgeom.Within(comparegeom) or currgeom.Contains(comparegeom):  # order-dependent, complimentary
                        outFeat = ogr.Feature(fDefI)
                        outFeat.SetField("TYPE", "double line")
                        outFeat.SetGeometry(ogr.ForceToMultiPoint(currgeom.Centroid()))
                        outLayerI.CreateFeature(outFeat)
                        outFeat = None
                        counts['double lines'] += 1
                    if currgeom.Overlaps(comparegeom):
                        outFeat = ogr.Feature(fDefI)
                        outFeat.SetField("TYPE", "overlap")
                        outFeat.SetGeometry(ogr.ForceToMultiPoint(currgeom.Centroid()))
                        outLayerI.CreateFeature(outFeat)
                        outFeat = None
                        counts['overlap'] += 1
                dist = currgeom.Distance(comparegeom)
                if 0 < dist < 0.02:
                    outFeat = ogr.Feature(fDefI)
                    outFeat.SetField("TYPE", "close")
                    outFeat.SetField("VAL", dist)
                    outFeat.SetGeometry(ogr.ForceToMultiPoint(currgeom.Centroid()))
                    outLayerI.CreateFeature(outFeat)
                    outFeat = None
                    counts['close'] += 1


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: findDoubleSegments.py source.shp result_dir [split_size=50] [max_elements=1000]")
        exit(1)

    SOURCE_LINES = sys.argv[1]
    tempf = sys.argv[2]
    split_size = int(sys.argv[3]) if len(sys.argv) > 3 else 50  # meters (set to 0 to skip splitting)
    max_elements = int(sys.argv[4]) if len(
        sys.argv) > 4 else 1000  # skip tile if more than this many elements (export to polygon shapefile)
    main(SOURCE_LINES, tempf, split_size, max_elements)
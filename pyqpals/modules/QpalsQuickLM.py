"""
/***************************************************************************
Name			 	 : qpalsQuickLM
Description          : Allows quick modelling of selected lines based on a DTM/pointcloud
Date                 : 2017-08-04
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

from builtins import object
from qgis.PyQt import QtGui, QtWidgets
from qgis.core import *
from qgis.gui import *
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel

import os
from osgeo import ogr
import tempfile
from .. import QpalsModuleBase, QpalsParameter
from ..qt_extensions import QpalsDropTextbox

class QpalsQuickLM(object):

    def __init__(self, project, layerlist, iface):
        self.ui = None
        self.project = project
        self.layerlist = layerlist
        self.iface = iface
        self.createUi()

    def createUi(self):
        self.selectedChkBox = QtWidgets.QCheckBox("Use selected lines only")
        self.selectedChkBox.setCheckState(2)
        self.cmbLineLayer = QgsMapLayerComboBox()
        self.cmbLineLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.cmbOdmPath =QpalsDropTextbox.QpalsDropTextbox(layerlist=self.layerlist, filterrex=".*\\.odm$")
        self.runBtn = QtWidgets.QPushButton("Run")
        self.runBtn.clicked.connect(self.runLM)
        self.ui = QtWidgets.QWidget()
        self.fl = QtWidgets.QFormLayout()
        self.ui.setLayout(self.fl)
        self.fl.addRow(QtWidgets.QLabel("Line layer:"), self.cmbLineLayer)
        self.fl.addRow(QtWidgets.QLabel("Point cloud:"), self.cmbOdmPath)
        self.fl.addRow(self.selectedChkBox)
        self.fl.addRow(self.runBtn)

    def runLM(self):
        params = {}
        layer = self.cmbLineLayer.currentLayer()
        if self.selectedChkBox.checkState() == 2:
            infile = tempfile.NamedTemporaryFile(delete=False)
            params["approxFile"] = infile.name + ".shp"
            infile.close()
            QgsVectorFileWriter.writeAsVectorFormat(layer, params["approxFile"],
                                                    "utf-8", layer.crs(), "ESRI Shapefile", 1)  # 1 for selected only
            try:
                os.remove(infile.name + ".prj")
            except:
                pass
        else:
            params["approxFile"] = layer.source()

        outfile = tempfile.NamedTemporaryFile(delete=False)
        params["outFile"] = outfile.name + ".shp"
        outfile.close()

        params["inFile"] = self.cmbOdmPath.text()

        Module = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(self.project.opalspath, "opalsLineModeler.exe"),
                                                 QpalsProject=self.project)

        paramlist = []
        for param in params.keys():
            paramlist.append(QpalsParameter.QpalsParameter(param, params[param], None, None, None, None, None))
        Module.params = paramlist
        #print "running module. writing outfile to %s" % params["outFile"]
        moduleOut = Module.run(show=0)
        #print moduleOut
        self.iface.addVectorLayer(params["outFile"], os.path.basename("Modelled Lines"), "ogr")

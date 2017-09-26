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

from PyQt4 import QtGui
from qgis.core import *
from qgis.gui import *
from qgis.gui import QgsMapLayerComboBox, QgsMapLayerProxyModel

import os
import ogr
import tempfile
from .. import QpalsModuleBase, QpalsParameter
from ..qt_extensions import QpalsDropTextbox

class QpalsQuickLM:

    def __init__(self, project, layerlist, iface):
        self.ui = None
        self.project = project
        self.layerlist = layerlist
        self.iface = iface
        self.createUi()

    def createUi(self):
        self.selectedChkBox = QtGui.QCheckBox("Use selected lines only")
        self.selectedChkBox.setCheckState(2)
        self.cmbLineLayer = QgsMapLayerComboBox()
        self.cmbLineLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.cmbOdmPath =QpalsDropTextbox.QpalsDropTextbox(layerlist=self.layerlist, filterrex=".*\.odm$")
        self.runBtn = QtGui.QPushButton("Run")
        self.runBtn.clicked.connect(self.runLM)
        self.ui = QtGui.QWidget()
        self.fl = QtGui.QFormLayout()
        self.ui.setLayout(self.fl)
        self.fl.addRow(QtGui.QLabel("Line layer:"), self.cmbLineLayer)
        self.fl.addRow(QtGui.QLabel("Point cloud:"), self.cmbOdmPath)
        self.fl.addRow(self.selectedChkBox)
        self.fl.addRow(self.runBtn)

    def runLM(self):
        params = {}
        lt_params = {}
        layer = self.cmbLineLayer.currentLayer()
        if self.selectedChkBox.checkState() == 2:
            infile = tempfile.NamedTemporaryFile(delete=False)
            lt_params["inFile"] = infile.name + ".shp"
            infile.close()
            QgsVectorFileWriter.writeAsVectorFormat(layer, lt_params["inFile"],
                                                    "utf-8", layer.crs(), "ESRI Shapefile", 1)  # 1 for selected only
        else:
            lt_params["inFile"] = layer.source()

        cleanedfile = tempfile.NamedTemporaryFile(delete=False)
        params["approxFile"] = cleanedfile.name + ".shp"
        lt_params["outFile"] = params["approxFile"]
        lt_params["method"] = "clean"
        cleanedfile.close()

        lineTopology = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(self.project.opalspath, "opalsLineTopology.exe"),
                                                 QpalsProject=self.project)

        lt_paramlist = []
        for param in lt_params.iterkeys():
            lt_paramlist.append(QpalsParameter.QpalsParameter(param, lt_params[param], None, None, None, None, None))
        lineTopology.params = lt_paramlist
        moduleOut = lineTopology.run(show=0)
        print moduleOut

        outfile = tempfile.NamedTemporaryFile(delete=False)
        params["outFile"] = outfile.name + ".shp"
        outfile.close()



        params["inFile"] = self.cmbOdmPath.text()

        Module = QpalsModuleBase.QpalsModuleBase(execName=os.path.join(self.project.opalspath, "opalsLineModeler.exe"),
                                                 QpalsProject=self.project)

        paramlist = []
        for param in params.iterkeys():
            paramlist.append(QpalsParameter.QpalsParameter(param, params[param], None, None, None, None, None))
        Module.params = paramlist
        print "running module. writing outfile to %s" % params["outFile"]
        moduleOut = Module.run(show=0)
        print moduleOut
        self.iface.addVectorLayer(params["outFile"], os.path.basename("Modelled Lines"), "ogr")

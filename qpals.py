"""
/***************************************************************************
Name			 	 : qpals lidar tools
Description          : integrates the opals software as a qgis plugin
Date                 : 04/Oct/15 
copyright            : (C) 2015 by Lukas Winiwarter/TU Wien
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from qpalsDialog import qpalsDialog
from opalsLayer import opalsLayer
from visualize import visualize

from modules.AddInfo.ModuleAddInfo import ModuleAddInfo
from modules.Algebra.ModuleAlgebra import ModuleAlgebra
from modules.Bounds.ModuleBounds import ModuleBounds
from modules.Cell.ModuleCell import ModuleCell
from modules.Contouring.ModuleContouring import ModuleContouring
from modules.Convolution.ModuleConvolution import ModuleConvolution
from modules.Diff.ModuleDiff import ModuleDiff
from modules.DirectGeoref.ModuleDirectGeoref import ModuleDirectGeoref
from modules.EchoRatio.ModuleEchoRatio import ModuleEchoRatio
from modules.Export.ModuleExport import ModuleExport
from modules.Fullwave.ModuleFullwave import ModuleFullwave
from modules.GeorefApprox.ModuleGeorefApprox import ModuleGeorefApprox
from modules.Grid.ModuleGrid import ModuleGrid
from modules.GridFeature.ModuleGridFeature import ModuleGridFeature
from modules.Histo.ModuleHisto import ModuleHisto
from modules.ICP.ModuleICP import ModuleICP
from modules.Import.ModuleImport import ModuleImport
from modules.Info.ModuleInfo import ModuleInfo
from modules.LSM.ModuleLSM import ModuleLSM
from modules.Morph.ModuleMorph import ModuleMorph
from modules.Normals.ModuleNormals import ModuleNormals
from modules.Openness.ModuleOpenness import ModuleOpenness
from modules.Overlap.ModuleOverlap import ModuleOverlap
from modules.PointStats.ModulePointStats import ModulePointStats
from modules.RadioCal.ModuleRadioCal import ModuleRadioCal
from modules.Rasterize.ModuleRasterize import ModuleRasterize
from modules.RobFilter.ModuleRobFilter import ModuleRobFilter
from modules.Shade.ModuleShade import ModuleShade
from modules.Simplify.ModuleSimplify import ModuleSimplify
from modules.StatFilter.ModuleStatFilter import ModuleStatFilter
from modules.TIN.ModuleTIN import ModuleTIN
from modules.ZColor.ModuleZColor import ModuleZColor


class qpals: 

  def __init__(self, iface):
    # Save reference to the QGIS interface
    self.iface = iface

  def __del__(self):
      import os
      import glob

      files = glob.glob(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\log\*')
      files += glob.glob(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\tmp\*')
      for f in files:
        os.remove(f)

  def showModuleSelector(self):
    from test.moduleSelector import moduleSelector
    modSel = moduleSelector(None)
    result = modSel.exec_()

  def initGui(self):  
    # Create action that will start plugin configuration
    # self.action = QAction(QIcon(":/plugins/qpals/icon.png"), \
    #     "qpals", self.iface.mainWindow())
    # # connect the action to the run method
    # QObject.connect(self.action, SIGNAL("activated()"), self.run)
    #
    # # Add toolbar button and menu item
    # self.iface.addToolBarIcon(self.action)
    # self.iface.addPluginToMenu("&qpals", self.action)
    self.menu = QMenu(self.iface.mainWindow())
    self.menu.setObjectName("qpalsMenu")
    self.menu.setTitle("qpals")
    self.action = QAction(QIcon(":/plugins/qpals/icon.png"), "Plot an odm", self.iface.mainWindow())
    self.action.setObjectName("startQpals")
    self.action.setWhatsThis("Starts the qpals main screen")
    self.action.setStatusTip("Start qpals")
    QObject.connect(self.action, SIGNAL("triggered()"), self.run)
    self.menu.addAction(self.action)

    self.menuItemImport = QAction(QIcon(":/plugins/qpals/icon.png"), "Import data...", self.iface.mainWindow())
    self.menuItemImport.setObjectName("menuImport")
    self.menuItemImport.setWhatsThis("Import a laser scanning file (las,...)")
    self.menuItemImport.setStatusTip("opalsImport")
    QObject.connect(self.menuItemImport, SIGNAL("triggered()"), self.loadDialogImport)
    self.menu.addAction(self.menuItemImport)

    # ------- next module -------

    self.menuItemModuleSelector = QAction(QIcon("icon.png"), "Module Selector", self.iface.mainWindow())
    self.menuItemModuleSelector.setObjectName("menuModSel")
    self.menuItemModuleSelector.setWhatsThis("Select a module from a list")
    self.menuItemModuleSelector.setStatusTip("Select module from list")
    QObject.connect(self.menuItemModuleSelector, SIGNAL("triggered()"), self.showModuleSelector)
    self.menu.addAction(self.menuItemModuleSelector)

#------- next module -------

    self.menuItemAddInfo = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsAddInfo...", self.iface.mainWindow())
    self.menuItemAddInfo.setObjectName("menuAddInfo")
    self.menuItemAddInfo.setWhatsThis("AddInfo")
    self.menuItemAddInfo.setStatusTip("opalsAddInfo")
    QObject.connect(self.menuItemAddInfo, SIGNAL("triggered()"), self.loadDialogAddInfo)
    self.menu.addAction(self.menuItemAddInfo)
#------- next module -------

    self.menuItemAlgebra = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsAlgebra...", self.iface.mainWindow())
    self.menuItemAlgebra.setObjectName("menuAlgebra")
    self.menuItemAlgebra.setWhatsThis("Algebra")
    self.menuItemAlgebra.setStatusTip("opalsAlgebra")
    QObject.connect(self.menuItemAlgebra, SIGNAL("triggered()"), self.loadDialogAlgebra)
    self.menu.addAction(self.menuItemAlgebra)
#------- next module -------

    self.menuItemBounds = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsBounds...", self.iface.mainWindow())
    self.menuItemBounds.setObjectName("menuBounds")
    self.menuItemBounds.setWhatsThis("Bounds")
    self.menuItemBounds.setStatusTip("opalsBounds")
    QObject.connect(self.menuItemBounds, SIGNAL("triggered()"), self.loadDialogBounds)
    self.menu.addAction(self.menuItemBounds)
#------- next module -------

    self.menuItemCell = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsCell...", self.iface.mainWindow())
    self.menuItemCell.setObjectName("menuCell")
    self.menuItemCell.setWhatsThis("Cell")
    self.menuItemCell.setStatusTip("opalsCell")
    QObject.connect(self.menuItemCell, SIGNAL("triggered()"), self.loadDialogCell)
    self.menu.addAction(self.menuItemCell)
#------- next module -------

    self.menuItemContouring = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsContouring...", self.iface.mainWindow())
    self.menuItemContouring.setObjectName("menuContouring")
    self.menuItemContouring.setWhatsThis("Contouring")
    self.menuItemContouring.setStatusTip("opalsContouring")
    QObject.connect(self.menuItemContouring, SIGNAL("triggered()"), self.loadDialogContouring)
    self.menu.addAction(self.menuItemContouring)
#------- next module -------

    self.menuItemConvolution = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsConvolution...", self.iface.mainWindow())
    self.menuItemConvolution.setObjectName("menuConvolution")
    self.menuItemConvolution.setWhatsThis("Convolution")
    self.menuItemConvolution.setStatusTip("opalsConvolution")
    QObject.connect(self.menuItemConvolution, SIGNAL("triggered()"), self.loadDialogConvolution)
    self.menu.addAction(self.menuItemConvolution)
#------- next module -------

    self.menuItemDiff = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsDiff...", self.iface.mainWindow())
    self.menuItemDiff.setObjectName("menuDiff")
    self.menuItemDiff.setWhatsThis("Diff")
    self.menuItemDiff.setStatusTip("opalsDiff")
    QObject.connect(self.menuItemDiff, SIGNAL("triggered()"), self.loadDialogDiff)
    self.menu.addAction(self.menuItemDiff)
#------- next module -------

    self.menuItemDirectGeoref = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsDirectGeoref...", self.iface.mainWindow())
    self.menuItemDirectGeoref.setObjectName("menuDirectGeoref")
    self.menuItemDirectGeoref.setWhatsThis("DirectGeoref")
    self.menuItemDirectGeoref.setStatusTip("opalsDirectGeoref")
    QObject.connect(self.menuItemDirectGeoref, SIGNAL("triggered()"), self.loadDialogDirectGeoref)
    self.menu.addAction(self.menuItemDirectGeoref)
#------- next module -------

    self.menuItemEchoRatio = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsEchoRatio...", self.iface.mainWindow())
    self.menuItemEchoRatio.setObjectName("menuEchoRatio")
    self.menuItemEchoRatio.setWhatsThis("EchoRatio")
    self.menuItemEchoRatio.setStatusTip("opalsEchoRatio")
    QObject.connect(self.menuItemEchoRatio, SIGNAL("triggered()"), self.loadDialogEchoRatio)
    self.menu.addAction(self.menuItemEchoRatio)
#------- next module -------

    self.menuItemExport = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsExport...", self.iface.mainWindow())
    self.menuItemExport.setObjectName("menuExport")
    self.menuItemExport.setWhatsThis("Export")
    self.menuItemExport.setStatusTip("opalsExport")
    QObject.connect(self.menuItemExport, SIGNAL("triggered()"), self.loadDialogExport)
    self.menu.addAction(self.menuItemExport)
#------- next module -------

    self.menuItemFullwave = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsFullwave...", self.iface.mainWindow())
    self.menuItemFullwave.setObjectName("menuFullwave")
    self.menuItemFullwave.setWhatsThis("Fullwave")
    self.menuItemFullwave.setStatusTip("opalsFullwave")
    QObject.connect(self.menuItemFullwave, SIGNAL("triggered()"), self.loadDialogFullwave)
    self.menu.addAction(self.menuItemFullwave)
#------- next module -------

    self.menuItemGeorefApprox = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsGeorefApprox...", self.iface.mainWindow())
    self.menuItemGeorefApprox.setObjectName("menuGeorefApprox")
    self.menuItemGeorefApprox.setWhatsThis("GeorefApprox")
    self.menuItemGeorefApprox.setStatusTip("opalsGeorefApprox")
    QObject.connect(self.menuItemGeorefApprox, SIGNAL("triggered()"), self.loadDialogGeorefApprox)
    self.menu.addAction(self.menuItemGeorefApprox)
#------- next module -------

    self.menuItemGrid = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsGrid...", self.iface.mainWindow())
    self.menuItemGrid.setObjectName("menuGrid")
    self.menuItemGrid.setWhatsThis("Grid")
    self.menuItemGrid.setStatusTip("opalsGrid")
    QObject.connect(self.menuItemGrid, SIGNAL("triggered()"), self.loadDialogGrid)
    self.menu.addAction(self.menuItemGrid)
#------- next module -------

    self.menuItemGridFeature = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsGridFeature...", self.iface.mainWindow())
    self.menuItemGridFeature.setObjectName("menuGridFeature")
    self.menuItemGridFeature.setWhatsThis("GridFeature")
    self.menuItemGridFeature.setStatusTip("opalsGridFeature")
    QObject.connect(self.menuItemGridFeature, SIGNAL("triggered()"), self.loadDialogGridFeature)
    self.menu.addAction(self.menuItemGridFeature)
#------- next module -------

    self.menuItemHisto = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsHisto...", self.iface.mainWindow())
    self.menuItemHisto.setObjectName("menuHisto")
    self.menuItemHisto.setWhatsThis("Histo")
    self.menuItemHisto.setStatusTip("opalsHisto")
    QObject.connect(self.menuItemHisto, SIGNAL("triggered()"), self.loadDialogHisto)
    self.menu.addAction(self.menuItemHisto)
#------- next module -------

    self.menuItemICP = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsICP...", self.iface.mainWindow())
    self.menuItemICP.setObjectName("menuICP")
    self.menuItemICP.setWhatsThis("ICP")
    self.menuItemICP.setStatusTip("opalsICP")
    QObject.connect(self.menuItemICP, SIGNAL("triggered()"), self.loadDialogICP)
    self.menu.addAction(self.menuItemICP)

#------- next module -------

    self.menuItemInfo = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsInfo...", self.iface.mainWindow())
    self.menuItemInfo.setObjectName("menuInfo")
    self.menuItemInfo.setWhatsThis("Info")
    self.menuItemInfo.setStatusTip("opalsInfo")
    QObject.connect(self.menuItemInfo, SIGNAL("triggered()"), self.loadDialogInfo)
    self.menu.addAction(self.menuItemInfo)
#------- next module -------

    self.menuItemLSM = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsLSM...", self.iface.mainWindow())
    self.menuItemLSM.setObjectName("menuLSM")
    self.menuItemLSM.setWhatsThis("LSM")
    self.menuItemLSM.setStatusTip("opalsLSM")
    QObject.connect(self.menuItemLSM, SIGNAL("triggered()"), self.loadDialogLSM)
    self.menu.addAction(self.menuItemLSM)
#------- next module -------

    self.menuItemMorph = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsMorph...", self.iface.mainWindow())
    self.menuItemMorph.setObjectName("menuMorph")
    self.menuItemMorph.setWhatsThis("Morph")
    self.menuItemMorph.setStatusTip("opalsMorph")
    QObject.connect(self.menuItemMorph, SIGNAL("triggered()"), self.loadDialogMorph)
    self.menu.addAction(self.menuItemMorph)
#------- next module -------

    self.menuItemNormals = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsNormals...", self.iface.mainWindow())
    self.menuItemNormals.setObjectName("menuNormals")
    self.menuItemNormals.setWhatsThis("Normals")
    self.menuItemNormals.setStatusTip("opalsNormals")
    QObject.connect(self.menuItemNormals, SIGNAL("triggered()"), self.loadDialogNormals)
    self.menu.addAction(self.menuItemNormals)
#------- next module -------

    self.menuItemOpenness = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsOpenness...", self.iface.mainWindow())
    self.menuItemOpenness.setObjectName("menuOpenness")
    self.menuItemOpenness.setWhatsThis("Openness")
    self.menuItemOpenness.setStatusTip("opalsOpenness")
    QObject.connect(self.menuItemOpenness, SIGNAL("triggered()"), self.loadDialogOpenness)
    self.menu.addAction(self.menuItemOpenness)
#------- next module -------

    self.menuItemOverlap = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsOverlap...", self.iface.mainWindow())
    self.menuItemOverlap.setObjectName("menuOverlap")
    self.menuItemOverlap.setWhatsThis("Overlap")
    self.menuItemOverlap.setStatusTip("opalsOverlap")
    QObject.connect(self.menuItemOverlap, SIGNAL("triggered()"), self.loadDialogOverlap)
    self.menu.addAction(self.menuItemOverlap)
#------- next module -------

    self.menuItemPointStats = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsPointStats...", self.iface.mainWindow())
    self.menuItemPointStats.setObjectName("menuPointStats")
    self.menuItemPointStats.setWhatsThis("PointStats")
    self.menuItemPointStats.setStatusTip("opalsPointStats")
    QObject.connect(self.menuItemPointStats, SIGNAL("triggered()"), self.loadDialogPointStats)
    self.menu.addAction(self.menuItemPointStats)
#------- next module -------

    self.menuItemRadioCal = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsRadioCal...", self.iface.mainWindow())
    self.menuItemRadioCal.setObjectName("menuRadioCal")
    self.menuItemRadioCal.setWhatsThis("RadioCal")
    self.menuItemRadioCal.setStatusTip("opalsRadioCal")
    QObject.connect(self.menuItemRadioCal, SIGNAL("triggered()"), self.loadDialogRadioCal)
    self.menu.addAction(self.menuItemRadioCal)
#------- next module -------

    self.menuItemRasterize = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsRasterize...", self.iface.mainWindow())
    self.menuItemRasterize.setObjectName("menuRasterize")
    self.menuItemRasterize.setWhatsThis("Rasterize")
    self.menuItemRasterize.setStatusTip("opalsRasterize")
    QObject.connect(self.menuItemRasterize, SIGNAL("triggered()"), self.loadDialogRasterize)
    self.menu.addAction(self.menuItemRasterize)
#------- next module -------

    self.menuItemRobFilter = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsRobFilter...", self.iface.mainWindow())
    self.menuItemRobFilter.setObjectName("menuRobFilter")
    self.menuItemRobFilter.setWhatsThis("RobFilter")
    self.menuItemRobFilter.setStatusTip("opalsRobFilter")
    QObject.connect(self.menuItemRobFilter, SIGNAL("triggered()"), self.loadDialogRobFilter)
    self.menu.addAction(self.menuItemRobFilter)
#------- next module -------

    self.menuItemShade = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsShade...", self.iface.mainWindow())
    self.menuItemShade.setObjectName("menuShade")
    self.menuItemShade.setWhatsThis("Shade")
    self.menuItemShade.setStatusTip("opalsShade")
    QObject.connect(self.menuItemShade, SIGNAL("triggered()"), self.loadDialogShade)
    self.menu.addAction(self.menuItemShade)
#------- next module -------

    self.menuItemSimplify = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsSimplify...", self.iface.mainWindow())
    self.menuItemSimplify.setObjectName("menuSimplify")
    self.menuItemSimplify.setWhatsThis("Simplify")
    self.menuItemSimplify.setStatusTip("opalsSimplify")
    QObject.connect(self.menuItemSimplify, SIGNAL("triggered()"), self.loadDialogSimplify)
    self.menu.addAction(self.menuItemSimplify)
#------- next module -------

    self.menuItemStatFilter = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsStatFilter...", self.iface.mainWindow())
    self.menuItemStatFilter.setObjectName("menuStatFilter")
    self.menuItemStatFilter.setWhatsThis("StatFilter")
    self.menuItemStatFilter.setStatusTip("opalsStatFilter")
    QObject.connect(self.menuItemStatFilter, SIGNAL("triggered()"), self.loadDialogStatFilter)
    self.menu.addAction(self.menuItemStatFilter)
#------- next module -------

    self.menuItemTIN = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsTIN...", self.iface.mainWindow())
    self.menuItemTIN.setObjectName("menuTIN")
    self.menuItemTIN.setWhatsThis("TIN")
    self.menuItemTIN.setStatusTip("opalsTIN")
    QObject.connect(self.menuItemTIN, SIGNAL("triggered()"), self.loadDialogTIN)
    self.menu.addAction(self.menuItemTIN)
#------- next module -------

    self.menuItemZColor = QAction(QIcon(":/plugins/qpals/icon.png"), "opalsZColor...", self.iface.mainWindow())
    self.menuItemZColor.setObjectName("menuZColor")
    self.menuItemZColor.setWhatsThis("ZColor")
    self.menuItemZColor.setStatusTip("opalsZColor")
    QObject.connect(self.menuItemZColor, SIGNAL("triggered()"), self.loadDialogZColor)
    self.menu.addAction(self.menuItemZColor)

    menuBar = self.iface.mainWindow().menuBar()
    menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)

    a = QAction( u"opalsBounds", self.iface.legendInterface() )
    b = QAction( u"opalsInfo", self.iface.legendInterface() )
    c = QAction( u"opalsHisto", self.iface.legendInterface() )
    self.iface.legendInterface().addLegendLayerAction( a, u"qpals", u"qpals1", QgsMapLayer.PluginLayer, True )
    self.iface.legendInterface().addLegendLayerAction( b, u"qpals", u"qpals1", QgsMapLayer.PluginLayer, True )
    self.iface.legendInterface().addLegendLayerAction( c, u"qpals", u"qpals1", QgsMapLayer.PluginLayer, True )

    QObject.connect(a, SIGNAL("triggered()"), self.run_a)

  def unload(self):
    # Remove the plugin menu item and icon
    # self.iface.removePluginMenu("&qpals",self.action)
    # self.iface.removeToolBarIcon(self.action)
    self.menu.deleteLater()

  # run method that performs all the real work
  def run(self): 
    # create and show the dialog 
    dlg = qpalsDialog() 
    # show the dialog
    dlg.show()
    result = dlg.exec_() 
    # See if OK was pressed
    if result == 1:
      self.iface.messageBar().pushMessage("opals Vis", dlg.getFileName(), level=QgsMessageBar.INFO)
      type = dlg.getVisType()
      if type == "zcolor":
        visualize.show_as_zcolor(dlg.getFileName())
      elif type == "mbr":
        visualize.show_as_oriented_rectange(dlg.getFileName())
      elif type == "alpha":
        visualize.show_as_alphashape(dlg.getFileName())
      elif type == "convexhull":
        visualize.show_as_convexhull(dlg.getFileName())
      elif type == "boundingbox":
        visualize.show_as_boundingbox(dlg.getFileName())

  def run_a(self):
    # create and show the dialog
    dlg = ModuleBounds()
    # show the dialog
    dlg.show()
    result = dlg.exec_()
    if result == 1:
        resDict = dlg.getValues()
        for key in resDict.keys():
            self.iface.messageBar().pushMessage("opals -%s"%key, str(resDict[key]), level=QgsMessageBar.INFO)


  def loadDialogImport(self):
    dlg = ModuleImport()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      ImportInst = dlg.getModule()
      if True:
      #try:
        ImportInst.run().wait()
        self.iface.messageBar().pushMessage("opals import ended", level=QgsMessageBar.SUCCESS)
      #except:
      #  self.iface.messageBar().pushMessage("opals import failed", level=QgsMessageBar.CRITICAL)
      #visualize.show_as_boundingbox(ImportInst.get_inFile().replace("las", "odm"))
      #newlayer = opalsLayer(name=ImportInst.get_inFile())
      #QgsMapLayerRegistry.instance().addMapLayer(newlayer)



#------- next module -------

  def loadDialogAddInfo(self):
    dlg = ModuleAddInfo()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      AddInfoInst = dlg.getModule()
      try:
        AddInfoInst.run()
        self.iface.messageBar().pushMessage("opals AddInfo ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals AddInfo failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogAlgebra(self):
    dlg = ModuleAlgebra()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      AlgebraInst = dlg.getModule()
      try:
        AlgebraInst.run()
        self.iface.messageBar().pushMessage("opals Algebra ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Algebra failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogBounds(self):
    dlg = ModuleBounds()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      BoundsInst = dlg.getModule()
      try:
        BoundsInst.run()
        self.iface.messageBar().pushMessage("opals Bounds ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Bounds failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogCell(self):
    dlg = ModuleCell()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      CellInst = dlg.getModule()
      try:
        CellInst.run()
        self.iface.messageBar().pushMessage("opals Cell ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Cell failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogContouring(self):
    dlg = ModuleContouring()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      ContouringInst = dlg.getModule()
      try:
        ContouringInst.run()
        self.iface.messageBar().pushMessage("opals Contouring ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Contouring failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogConvolution(self):
    dlg = ModuleConvolution()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      ConvolutionInst = dlg.getModule()
      try:
        ConvolutionInst.run()
        self.iface.messageBar().pushMessage("opals Convolution ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Convolution failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogDiff(self):
    dlg = ModuleDiff()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      DiffInst = dlg.getModule()
      try:
        DiffInst.run()
        self.iface.messageBar().pushMessage("opals Diff ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Diff failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogDirectGeoref(self):
    dlg = ModuleDirectGeoref()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      DirectGeorefInst = dlg.getModule()
      try:
        DirectGeorefInst.run()
        self.iface.messageBar().pushMessage("opals DirectGeoref ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals DirectGeoref failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogEchoRatio(self):
    dlg = ModuleEchoRatio()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      EchoRatioInst = dlg.getModule()
      try:
        EchoRatioInst.run()
        self.iface.messageBar().pushMessage("opals EchoRatio ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals EchoRatio failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogExport(self):
    dlg = ModuleExport()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      ExportInst = dlg.getModule()
      try:
        ExportInst.run()
        self.iface.messageBar().pushMessage("opals Export ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Export failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogFullwave(self):
    dlg = ModuleFullwave()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      FullwaveInst = dlg.getModule()
      try:
        FullwaveInst.run()
        self.iface.messageBar().pushMessage("opals Fullwave ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Fullwave failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogGeorefApprox(self):
    dlg = ModuleGeorefApprox()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      GeorefApproxInst = dlg.getModule()
      try:
        GeorefApproxInst.run()
        self.iface.messageBar().pushMessage("opals GeorefApprox ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals GeorefApprox failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogGrid(self):
    dlg = ModuleGrid()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      GridInst = dlg.getModule()
      try:
        GridInst.run()
        self.iface.messageBar().pushMessage("opals Grid ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Grid failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogGridFeature(self):
    dlg = ModuleGridFeature()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      GridFeatureInst = dlg.getModule()
      try:
        GridFeatureInst.run()
        self.iface.messageBar().pushMessage("opals GridFeature ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals GridFeature failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogHisto(self):
    dlg = ModuleHisto()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      HistoInst = dlg.getModule()
      try:
        HistoInst.run()
        self.iface.messageBar().pushMessage("opals Histo ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Histo failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogICP(self):
    dlg = ModuleICP()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      ICPInst = dlg.getModule()
      try:
        ICPInst.run()
        self.iface.messageBar().pushMessage("opals ICP ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals ICP failed", level=QgsMessageBar.CRITICAL)


#------- next module -------

  def loadDialogInfo(self):
    dlg = ModuleInfo()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      InfoInst = dlg.getModule()
      try:
        InfoInst.run()
        self.iface.messageBar().pushMessage("opals Info ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Info failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogLSM(self):
    dlg = ModuleLSM()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      LSMInst = dlg.getModule()
      try:
        LSMInst.run()
        self.iface.messageBar().pushMessage("opals LSM ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals LSM failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogMorph(self):
    dlg = ModuleMorph()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      MorphInst = dlg.getModule()
      try:
        MorphInst.run()
        self.iface.messageBar().pushMessage("opals Morph ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Morph failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogNormals(self):
    dlg = ModuleNormals()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      NormalsInst = dlg.getModule()
      try:
        NormalsInst.run()
        self.iface.messageBar().pushMessage("opals Normals ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Normals failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogOpenness(self):
    dlg = ModuleOpenness()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      OpennessInst = dlg.getModule()
      try:
        OpennessInst.run()
        self.iface.messageBar().pushMessage("opals Openness ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Openness failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogOverlap(self):
    dlg = ModuleOverlap()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      OverlapInst = dlg.getModule()
      try:
        OverlapInst.run()
        self.iface.messageBar().pushMessage("opals Overlap ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Overlap failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogPointStats(self):
    dlg = ModulePointStats()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      PointStatsInst = dlg.getModule()
      try:
        PointStatsInst.run()
        self.iface.messageBar().pushMessage("opals PointStats ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals PointStats failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogRadioCal(self):
    dlg = ModuleRadioCal()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      RadioCalInst = dlg.getModule()
      try:
        RadioCalInst.run()
        self.iface.messageBar().pushMessage("opals RadioCal ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals RadioCal failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogRasterize(self):
    dlg = ModuleRasterize()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      RasterizeInst = dlg.getModule()
      try:
        RasterizeInst.run()
        self.iface.messageBar().pushMessage("opals Rasterize ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Rasterize failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogRobFilter(self):
    dlg = ModuleRobFilter()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      RobFilterInst = dlg.getModule()
      try:
        RobFilterInst.run()
        self.iface.messageBar().pushMessage("opals RobFilter ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals RobFilter failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogShade(self):
    dlg = ModuleShade()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      ShadeInst = dlg.getModule()
      try:
        ShadeInst.run()
        self.iface.messageBar().pushMessage("opals Shade ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Shade failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogSimplify(self):
    dlg = ModuleSimplify()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      SimplifyInst = dlg.getModule()
      try:
        SimplifyInst.run()
        self.iface.messageBar().pushMessage("opals Simplify ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals Simplify failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogStatFilter(self):
    dlg = ModuleStatFilter()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      StatFilterInst = dlg.getModule()
      try:
        StatFilterInst.run()
        self.iface.messageBar().pushMessage("opals StatFilter ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals StatFilter failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogTIN(self):
    dlg = ModuleTIN()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      TINInst = dlg.getModule()
      try:
        TINInst.run()
        self.iface.messageBar().pushMessage("opals TIN ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals TIN failed", level=QgsMessageBar.CRITICAL)

#------- next module -------

  def loadDialogZColor(self):
    dlg = ModuleZColor()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      ZColorInst = dlg.getModule()
      try:
        ZColorInst.run()
        self.iface.messageBar().pushMessage("opals ZColor ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals ZColor failed", level=QgsMessageBar.CRITICAL)

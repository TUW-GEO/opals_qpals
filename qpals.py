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
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from qpalsDialog import qpalsDialog
from opalsLayer import opalsLayer

class qpals: 

  def __init__(self, iface):
    # Save reference to the QGIS interface
    self.iface = iface

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
    self.action = QAction(QIcon(":/plugins/qpals/icon.png"), "Start QPALS", self.iface.mainWindow())
    self.action.setObjectName("startQpals")
    self.action.setWhatsThis("Starts the qpals main screen")
    self.action.setStatusTip("Start qpals")
    QObject.connect(self.action, SIGNAL("triggered()"), self.run)
    self.menu.addAction(self.action)

    menuBar = self.iface.mainWindow().menuBar()
    menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)

    a = QAction( u"opalsInfo", self.iface.legendInterface() )
    b = QAction( u"opalsExport", self.iface.legendInterface() )
    c = QAction( u"opalsHisto", self.iface.legendInterface() )
    self.iface.legendInterface().addLegendLayerAction( a, u"qpals", u"qpals1", QgsMapLayer.PluginLayer, True )
    self.iface.legendInterface().addLegendLayerAction( b, u"qpals", u"qpals1", QgsMapLayer.PluginLayer, True )
    self.iface.legendInterface().addLegendLayerAction( c, u"qpals", u"qpals1", QgsMapLayer.PluginLayer, True )


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
      testlayer = opalsLayer()
      QgsMapLayerRegistry.instance().addMapLayer(testlayer)
      pass 

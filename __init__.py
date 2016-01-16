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
 This script initializes the plugin, making it known to QGIS.
"""

def name(): 
  return "qpals lidar tools" 
def description():
  return "integrates the opals software as a qgis plugin"
def version(): 
  return "Version 0.1" 
def qgisMinimumVersion():
  return "1.8"
def classFactory(iface): 
  # load qpals class from file qpals
  from qpals import qpals 
  return qpals(iface)

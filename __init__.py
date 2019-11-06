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
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
import importlib
import sys, os


def name(): 
    return "qpals"


def description():
    return "integrates the opals software as a qgis plugin"


def version(): 
    return "Version 2.0"


def qgisMinimumVersion():
    return "2.99"


def classFactory(iface):
    # check requirements
    for package in ['matplotlib', 'vispy', 'scipy']:
        try:
            importlib.import_module(package)
        except:
            msg = QMessageBox()
            msg.setText("A package that is required for qpals could not be found")
            msg.setInformativeText("Qpals requires the package '%s'. Press 'OK' to attempt installation (might take some time)." % package)
            msg.setWindowTitle("qpals missing libraries")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ret = msg.exec_()
            if ret == QMessageBox.Ok:
                #    import pip
                exe = sys.executable
                python_exe = os.path.join(os.path.split(exe)[0], "python-qgis.bat")
                import subprocess
                rc = subprocess.call([python_exe, '-m', 'pip', 'install', package])
                msg = QMessageBox()
                msg.setText("Package installation")
                msg.setWindowTitle("qpals package installation")
                msg.setStandardButtons(QMessageBox.Ok)
                if rc == 0:
                    msg.setInformativeText("Package installation succeeded")
                else:
                    msg.setInformativeText("Package installation failed. Please try manual installation. Not all features of qpals will be available.")
                ret = msg.exec_()

    # load qpals class from file qpals
    from .pyqpals import qpals
    return qpals.qpals(iface)

class deactivatedQpals:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        pass

    def unload(self):
        pass

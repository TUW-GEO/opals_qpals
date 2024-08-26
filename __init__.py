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
import importlib, site
import sys, os, glob

from qgis.core import QgsMessageLog, Qgis

def name(): 
    return "qpals"


def description():
    return "integrates the opals software as a qgis plugin"


def version(): 
    return "Version 2.0"


def qgisMinimumVersion():
    return "2.99"

def check_packages(packages):
    installed_packages = []
    missing_packages = []
    for package in packages:
        try:
            importlib.import_module(package)
            installed_packages.append(package)
        except:
            missing_packages.append(package)
    return installed_packages, missing_packages


def classFactory(iface):
    # check requirements
    QgsMessageLog.logMessage('check requirements', 'qpals', level=Qgis.Info)

    packages = ['matplotlib', 'vispy', 'scipy', 'semantic_version']
    _, missing_packages = check_packages(packages)

    QgsMessageLog.logMessage(f'missing packages={missing_packages}', 'qpals', level=Qgis.Info)

    if missing_packages:
        msg = QMessageBox()
        msg.setText("Packages that are required for qpals could not be found")
        msg.setInformativeText(f"Qpals requires packages {', '.join(missing_packages)}. Press 'OK' to attempt installation (might take some time).")
        msg.setWindowTitle("qpals missing libraries")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ret = msg.exec_()
        if ret == QMessageBox.Ok:
            #    import pip
            exe = sys.executable
            files = glob.glob(os.path.join(os.path.split(exe)[0], "python-qgis*.bat"))
            installation_ok = False
            if len(files) == 1:
                python_exe = files[0]
                import subprocess
                rc = subprocess.call([python_exe, '-m', 'pip', 'install'] + missing_packages)
                msg = QMessageBox()
                msg.setText("Package installation")
                msg.setWindowTitle("qpals package installation")
                msg.setStandardButtons(QMessageBox.Ok)
                if rc == 0:
                    _, missing_packages = check_packages(missing_packages)
                    QgsMessageLog.logMessage(f'missing packages after installation={missing_packages}', 'qpals', level=Qgis.Warning)
                    if missing_packages:
                        site.main()     # importing doesn't work if user site directory didn't exist before. So try re-initializing
                        _, missing_packages = check_packages(missing_packages)
                        QgsMessageLog.logMessage(f'missing packages after site.main()={missing_packages}', 'qpals',
                                                 level=Qgis.Warning)
                        if missing_packages:
                            msg.setInformativeText("Package installation succeeded but importing failed. Try to restart QGIS")

                    if not missing_packages:
                        installation_ok = True
                else:
                    msg.setInformativeText("Package installation failed. Please try manual installation. Not all features of qpals will be available.")
            else:
                    msg.setInformativeText("Package installation failed (Unable to locate qgis python startup script). Please try manual installation. Not all features of qpals will be available.")
            if not installation_ok:
                ret = msg.exec_()
            else:
                QgsMessageLog.logMessage(f'packages installed successful', 'qpals',
                                         level=Qgis.Info)

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

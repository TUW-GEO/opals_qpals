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

plugin_name = "qpals-default"   # just default value in case reading metadata file fails

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


def logMessage(message, level=Qgis.Info):
    global plugin_name
    QgsMessageLog.logMessage(message, plugin_name, level=level)

def classFactory(iface):
    global plugin_name

    # load plugin from metadata.txt
    metadata_file = os.path.join(os.path.dirname(__file__), "metadata.txt")
    try:
        with open(metadata_file) as f:
            for line in f:
                if line.strip().startswith('name='):
                    plugin_name = line.split("=")[1].strip()
                    logMessage(f"plugin name extracted: {plugin_name}")
                    break
    except Exception as e:
        logMessage(f"Exception occurred while reading metadata.txt: {e}", level=Qgis.Critical)
        pass

    # check requirements
    logMessage('check requirements', level=Qgis.Info)

    packages = ['matplotlib', 'vispy', 'scipy', 'semantic_version']
    _, missing_packages = check_packages(packages)

    logMessage(f'missing packages={missing_packages}', level=Qgis.Info)

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
            if os.name == 'nt':
                files = glob.glob(os.path.join(os.path.split(exe)[0], "python-qgis*.bat"))
            else:
                files = [exe]   # under linux the system python version is used
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
                    logMessage(f'missing packages after installation={missing_packages}', level=Qgis.Warning)
                    if missing_packages:
                        site.main()     # importing doesn't work if user site directory didn't exist before. So try re-initializing
                        _, missing_packages = check_packages(missing_packages)
                        logMessage(f'missing packages after site.main()={missing_packages}', level=Qgis.Warning)
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
                logMessage(f'packages installed successful', level=Qgis.Info)

    # load qpals class from file qpals
    from .pyqpals import qpals
    return qpals.qpals(iface, plugin_name)

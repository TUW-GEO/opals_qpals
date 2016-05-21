"""
/***************************************************************************
Name			 	 : qpalsListWidgetItem
Description          : supplies an enhanced list widget for pyqt
Date                 : 2016-05-21
copyright            : (C) 2016 by Lukas Winiwarter/TU Wien
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

from PyQt4 import QtCore, QtGui
import subprocess
from xml.dom import minidom

class QpalsModuleBase():

    def __init__(self, execName):
        self.params = {}
        self.execName = execName

    def load(self):
        proc = subprocess.Popen([self.execName, '--options'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=r"C:\Users\Lukas\Desktop")
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception('Call failed:\n %s' % stdout)
        dom = minidom.parseString(stderr)
        specOptsNode = dom.getElementsByTagName('Specific')[0]
        specOpts = specOptsNode.getElementsByTagName('Parameter')
        for opt in specOpts:
            values = opt.getElementsByTagName('Val')
            self.params[opt.attributes['Name'].value] = ";".join([x.firstChild.nodeValue for x in values])
        print self.params

    def getParamUi(self):
        form = QtGui.QFormLayout()
        for key in self.params.iterkeys():
            l1 = QtGui.QLabel(key)
            e1 = QtGui.QLineEdit()
            form.addRow(l1, e1)

    def run(self):
        pass
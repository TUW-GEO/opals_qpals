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
        self.params = []
        self.execName = execName
        self.loaded=False

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
            self.params.append({'name': opt.attributes['Name'].value , 'val': ";".join([x.firstChild.nodeValue for x in values]) if values else "" })
        self.loaded = True

    def getParamUi(self):
        if not self.loaded:
            self.load()
        form = QtGui.QFormLayout()
        for param in self.params:
            l1 = QtGui.QLabel(param['name'])
            param['field'] = QtGui.QLineEdit(param['val'])
            param['field'].textChanged.connect(self.updateVals)
            param['field'].editingFinished.connect(self.validate)
            form.addRow(l1, param['field'])
        return form

    def updateVals(self, string):
        for param in self.params:
            if string == param['field'].text():
                param['val'] = param['field'].text()

    def validate(self):
        pass

    def run(self):
        pass

    def reset(self):
        self.params = []
        self.load()

class QpalsRunBatch():

    def __init__(self):
        self.command = ""

    def getParamUi(self):
        form = QtGui.QFormLayout()

        l1 = QtGui.QLabel("Command")
        e1 = QtGui.QLineEdit()
        l2 = QtGui.QLabel("Working directory")
        e2 = QtGui.QLineEdit()

        form.addRow(l1, e1)
        form.addRow(l2, e2)

        return form

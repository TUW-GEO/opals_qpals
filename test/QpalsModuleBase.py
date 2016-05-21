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

    def load(self, params = None):
        info = subprocess.STARTUPINFO()
        info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 0 # HIDE
        callparams = [self.execName, '--options']
        if params:
            callparams = callparams + [1] + params
        proc = subprocess.Popen(callparams, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                cwd=r"C:\Users\Lukas\Desktop", startupinfo=info)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception('Call failed:\n %s' % stdout)
        dom = minidom.parseString(stderr)
        specOptsNode = dom.getElementsByTagName('Specific')[0]
        specOpts = specOptsNode.getElementsByTagName('Parameter')
        for opt in specOpts:
            values = opt.getElementsByTagName('Val')
            print values
            if values:
                if len(values) > 1:
                    valString = ""
                    for val in values:
                        valString += val.firstChild.nodeValue+";"
                    valString = valString[:-1]
                else:
                    if values[0].firstChild:
                        valString = values[0].firstChild.nodeValue
                    else:
                        valString = ""
            else:
                valString = ""
            self.params.append({'name': opt.attributes['Name'].value, 'val': valString, 'opt': opt.attributes['Opt'].value})
        self.loaded = True

    def getParamUi(self):
        if not self.loaded:
            self.load()
        form = QtGui.QFormLayout()
        for param in self.params:
            l1 = QtGui.QLabel(param['name'])
            param['field'] = QtGui.QLineEdit(param['val'])
            if param['opt'] == 'mandatory':
                param['field'].setStyleSheet("background-color: rgb(255,240,230);")
            param['field'].textChanged.connect(self.updateVals)
            param['field'].editingFinished.connect(self.validate)
            form.addRow(l1, param['field'])
        return form

    def updateVals(self, string):
        for param in self.params:
            if string == param['field'].text():
                param['val'] = param['field'].text()

    def validate(self):
        allmandatoryset = True
        paramlist = []
        for param in self.params:
            if param['opt'] == 'mandatory' and not param['val']:
                allmandatoryset = False
            paramlist.append('-' + param['name'])
            for item in param['val'].split(";"):
                paramlist.append(item)
        if allmandatoryset:
            self.load(paramlist)

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
        self.e1 = QtGui.QLineEdit()
        l2 = QtGui.QLabel("Working directory")
        self.e2 = QtGui.QLineEdit()

        form.addRow(l1, self.e1)
        form.addRow(l2, self.e2)

        return form

    def reset(self):
        self.e1 = ""
        self.e2 = ""


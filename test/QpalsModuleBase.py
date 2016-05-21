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

WaitIcon = QtGui.QIcon(r"C:\Users\Lukas\.qgis2\python\plugins\qpals\wait_icon.png")
WaitIconMandatory = QtGui.QIcon(r"C:\Users\Lukas\.qgis2\python\plugins\qpals\wait_icon_mandatory.png")
ErrorIcon = QtGui.QIcon(r"C:\Users\Lukas\.qgis2\python\plugins\qpals\error_icon.png")

def parseXML(xml):
    dom = minidom.parseString(xml)
    elements = []
    specOptsNode = dom.getElementsByTagName('Specific')[0]
    specOpts = specOptsNode.getElementsByTagName('Parameter')
    for opt in specOpts:
        values = opt.getElementsByTagName('Val')
        if values:
            if len(values) > 1:
                valString = ""
                for val in values:
                    valString += val.firstChild.nodeValue + ";"
                valString = valString[:-1]
            else:
                if values[0].firstChild:
                    valString = values[0].firstChild.nodeValue
                else:
                    valString = ""
        else:
            valString = ""
        elements.append({'name': opt.attributes['Name'].value, 'val': valString,
                        'opt': opt.attributes['Opt'].value})
    return elements

class QpalsModuleBase():

    def __init__(self, execName):
        self.params = []
        self.execName = execName
        self.loaded=False

    def load(self):
        info = subprocess.STARTUPINFO()
        info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 0 # HIDE
        proc = subprocess.Popen([self.execName, '--options'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                cwd=r"C:\Users\Lukas\Desktop", startupinfo=info)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception('Call failed:\n %s' % stdout)
        self.params = parseXML(stderr)

        self.loaded = True

    def getParamUi(self):
        if not self.loaded:
            self.load()
        form = QtGui.QFormLayout()
        for param in self.params:
            l1 = QtGui.QLabel(param['name'])
            param['field'] = QtGui.QLineEdit(param['val'])
            param['icon'] = QtGui.QToolButton()
            param['icon'].setToolTip(param['opt'])
            param['icon'].setIcon(WaitIcon)
            param['icon'].setStyleSheet("border-style: none;")
            if param['opt'] == 'mandatory':
                param['icon'].setIcon(WaitIconMandatory)
            param['field'].textChanged.connect(self.updateVals)
            param['field'].editingFinished.connect(self.validate)

            l2 = QtGui.QHBoxLayout()
            l2.addWidget(param['field'], stretch=1)
            l2.addWidget(param['icon'])
            form.addRow(l1, l2)
        return form

    def updateVals(self, string):
        for param in self.params:
            if string == param['field'].text():
                param['val'] = param['field'].text()

    def validate(self):
        allmandatoryset = True
        paramlist = []
        for param in self.params:
            if param['opt'] == 'mandatory':
                param['field'].setToolTip('')
                param['field'].setStyleSheet('')
                param['icon'].setIcon(WaitIconMandatory)
                if not param['val']:
                    allmandatoryset = False
            else:
                param['field'].setStyleSheet('')
                param['field'].setToolTip("")
                param['icon'].setIcon(WaitIcon)
            if param['val']:
                paramlist.append('-' + param['name'])
                for item in param['val'].split(";"):
                    paramlist.append(item)
        if allmandatoryset:
            info = subprocess.STARTUPINFO()
            info.dwFlags = subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = 0  # HIDE
            callparams = [self.execName, '--options', '1'] + paramlist
            proc = subprocess.Popen(callparams, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    cwd=r"C:\Users\Lukas\Desktop", startupinfo=info)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                if "Error in parameter" in stdout:
                    errortext = stdout.split("Error in parameter ")[1].split("\n")[0]
                    errormodule = errortext.split(":")[0]
                    errortext = ":".join(errortext.split(":")[1:])
                    print errormodule, errortext
                    for param in self.params:
                        if param['name'] == errormodule:
                            param['field'].setToolTip(errortext)
                            param['icon'].setIcon(ErrorIcon)
                            param['field'].setStyleSheet('background-color: rgb(255,140,140);')
                            break
                else:
                    raise Exception('Call failed:\n %s' % stdout)
            else:
                parsedXML = parseXML(stderr)
                for param in self.params:
                    for parsedParam in parsedXML:
                        if param['name'] == parsedParam['name']:
                            param['field'].setText(parsedParam['val'])
                            break

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

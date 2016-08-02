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
import os
import threading
from xml.dom import minidom

import QpalsParamMsgBtn
import QTextComboBox

IconPath = r"C:\Users\Lukas\.qgis2\python\plugins\qpals\\"

WaitIcon = QtGui.QIcon(IconPath + "wait_icon.png")
WaitIconMandatory = QtGui.QIcon(IconPath + "wait_icon_mandatory.png")
ErrorIcon = QtGui.QIcon(IconPath + "error_icon.png")

qtwhite = QtGui.QColor(255,255,255)
qtsoftred = QtGui.QColor(255,140,140)
qtsoftgreen = QtGui.QColor(140,255,140)

def parseXML(xml):
    dom = minidom.parseString(xml)
    elements = []
    specOptsNode = dom.getElementsByTagName('Specific')[0]
    specOpts = specOptsNode.getElementsByTagName('Parameter')
    for opt in specOpts:
        values = opt.getElementsByTagName('Val')
        choices = opt.getElementsByTagName('Choice')
        choiceList = []
        valString = ""
        if values:
            if len(values) > 1:
                for val in values:
                    valString += val.firstChild.nodeValue + ";"
                valString = valString[:-1]
            else:
                if values[0].firstChild:
                    valString = values[0].firstChild.nodeValue
        if choices:
            for choice in choices:
                choiceList.append(choice.getAttribute("Val"))
        elements.append({'name': opt.attributes['Name'].value, 'val': valString,
                        'opt': opt.attributes['Opt'].value, 'desc': opt.attributes['Desc'].value,
                         'longdesc': opt.attributes['LongDesc'].value, 'choices': choiceList,
                         'type': opt.attributes['Type'].value})
    return elements

class ModuleLoadWorker(QtCore.QObject):
    def __init__(self, module):
        QtCore.QObject.__init__(self)
        self.module = module
        self.killed = False

    def run(self):
        ret = None
        try:
            print "loading"
            self.module.paramClass.load()
            print "loaded"
            if not self.killed:
                self.progress.emit(100)
                ret = (self.module, "42",)
        except Exception as e:
            self.error.emit(e, str(e), self.module)
        self.finished.emit(ret)

    def kill(self):
        self.killed = True

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, basestring, object)
    progress = QtCore.pyqtSignal(float)


class ModuleValidateWorker(QtCore.QObject):
    def __init__(self, module):
        QtCore.QObject.__init__(self)
        self.module = module
        self.killed = False

    def run(self):
        ret = None
        try:
            self.module.validate()
            if not self.killed:
                self.progress.emit(100)
                ret = (self.module,)
        except Exception as e:
            self.error.emit(e, str(e), self.module)
        self.finished.emit(ret)

    def kill(self):
        self.killed = True

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, basestring, object)
    progress = QtCore.pyqtSignal(float)



class ModuleRunWorker(QtCore.QObject):
    def __init__(self, module):
        QtCore.QObject.__init__(self)
        self.module = module
        self.killed = False

    def run(self):
        ret = None
        try:
            self.module.paramClass.run()
            if not self.killed:
                self.progress.emit(100)
                ret = (self.module, "42",)
        except Exception as e:
            self.error.emit(e, str(e), self.module)
        self.finished.emit(ret)

    def kill(self):
        self.killed = True

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, basestring, object)
    progress = QtCore.pyqtSignal(float)

class QpalsModuleBase():
    def __init__(self, execName, tmpDir=r"C:\Users\Lukas\Desktop\\", listitem=None):
        self.params = []
        self.execName = execName
        self.tmpDir = tmpDir
        self.loaded = False
        self.view = False
        self.revalidate=False
        self.listitem = listitem
        self.currentlyvalidating = False
        self.validatethread = None
        self.validateworker = None
        self.lastpath = tmpDir

    def call(self, show=0, *args):
        info = subprocess.STARTUPINFO()
        info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = show  # 0=HIDE
        print "CALL: ", [self.execName] + list(args)
        proc = subprocess.Popen([self.execName] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE, cwd=self.tmpDir, startupinfo=info)
        proc.stdin.close()
        stdout, stderr = proc.communicate()
        return {'stdout': stdout,
                'stderr': stderr,
                'returncode': proc.returncode}

    def load(self):
        calld = self.call(0, '--options')
        if calld['returncode'] != 0:
            raise Exception('Call failed:\n %s' % calld['stdout'])
        self.params = parseXML(calld['stderr'])
        self.loaded = True

    def makefilebrowser(self, param):
        def showpathbrowser():
            filename = QtGui.QFileDialog.getSaveFileName(None, caption='Select file for %s'%param,
                                                          directory=self.lastpath,
                                                         options=QtGui.QFileDialog.DontConfirmOverwrite)
            if filename:
                for par in self.params:
                    if par['name'] == param:
                        par['field'].setText(filename)
                print filename
                print param
                print par['name']
                self.lastpath = os.path.dirname(filename)
                self.updateVals(filename)
                self.validate()
        return showpathbrowser

    def getParamUi(self):
        if not self.loaded:
            self.load()
        form = QtGui.QFormLayout()
        for param in self.params:
            l1 = QtGui.QLabel(param['name'])

            if len(param['choices']) == 0:
                param['field'] = QtGui.QLineEdit(param['val'])
                param['field'].textChanged.connect(self.updateVals)
                param['field'].editingFinished.connect(self.validate)

            else:
                param['field'] = QTextComboBox.QTextComboBox()
                for choice in param['choices']:
                    param['field'].addItem(choice)
                # 'QString' is necessary so that the text and not the index will be passed as parameter
                param['field'].currentIndexChanged['QString'].connect(self.updateVals)

            if "path" in param['type'].lower():
                param['browse'] = QtGui.QToolButton()
                param['browse'].setText("...")
                param['browse'].clicked.connect(self.makefilebrowser(param['name']))
                param['field'].setAcceptDrops(True)
                #param['field'].

            param['icon'] = QpalsParamMsgBtn.QpalsParamMsgBtn(param)
            param['icon'].setToolTip(param['opt'])
            param['icon'].setIcon(WaitIcon)
            param['icon'].setStyleSheet("border-style: none;")
            if param['opt'] == 'mandatory':
                param['icon'].setIcon(WaitIconMandatory)

            l2 = QtGui.QHBoxLayout()
            l2.addWidget(param['field'], stretch=1)
            if 'browse' in param:
                l2.addWidget(param['browse'])
            l2.addWidget(param['icon'])
            form.addRow(l1, l2)
        return form

    def updateVals(self, string):
        for param in self.params:
            if string == param['field'].text():
                if param['val'] != param['field'].text():
                    self.revalidate = True
                    param['val'] = param['field'].text()

    def validate_async(self):
        print "val_async> ",
        if not self.currentlyvalidating and self.revalidate:
            print "ok >",
            self.currentlyvalidating = True
            worker = ModuleValidateWorker(self)
            # start the worker in a new thread
            thread = QtCore.QThread()
            worker.moveToThread(thread)
            worker.error.connect(self.validateError)
            worker.finished.connect(self.validateFinished)
            thread.started.connect(worker.run)
            thread.start()
            self.validatethread = thread
            self.validateworker = worker

    def validateError(self, e, exception_string, module):
        print('Worker thread raised an exception: {}\n'.format(exception_string))
        #module.setIcon(self.errorIcon)

    def validateFinished(self, module):
        print "validate finished> ",
        self.validateworker.deleteLater()
        self.validatethread.quit()
        self.validatethread.wait()
        self.validatethread.deleteLater()
        self.currentlyvalidating = False
        print "validate done"


    def validate(self):
        if not self.revalidate:
            return
        self.revalidate = False
        allmandatoryset = True
        paramlist = []
        self.listitem.setBackgroundColor(qtwhite)
        self.listitem.setToolTip("")
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
                    paramlist.append(item.strip('"'))
        if allmandatoryset:
            self.listitem.setToolTip("All mandatory parameters set and validated.")
            calld = self.call(0, '--options', '1', *paramlist)
            valid = True
            if calld['returncode'] != 0:
                valid = False
                errormodule = ""
                if "Error in parameter" in calld['stdout']:
                    errortext = calld['stdout'].split("Error in parameter ")[1].split("\n")[0]
                    errormodule = errortext.split(":")[0]
                    errortext = ":".join(errortext.split(":")[1:])
                    print errormodule, errortext

                elif "Ambiguities while matching value" in calld['stdout']:
                    errortext = calld['stdout'].split("ERROR 0001: std::exception: ")[1].split("\n")[0]
                    msg = QtGui.QMessageBox()
                    msg.setIcon(QtGui.QMessageBox.Question)
                    msg.setText(errortext.split(".")[0])
                    msg.setInformativeText(".".join(errortext.split(".")[1:]))
                    msg.setWindowTitle("Ambiguities while setting parameter values")
                    msg.setStandardButtons(QtGui.QMessageBox.Ok)
                    msg.exec_()
                elif "ERROR 1000: the argument " in calld['stdout']:
                    errortext = calld['stdout'].split("ERROR 1000:")[1].split("\n")[0]
                    errormodule = errortext.split("for option '")[1].split("' is invalid")[0]

                else:
                    errortext = "Unknown error."
                    raise Exception('Call failed:\n %s' % calld['stdout'])
                if errormodule:
                    for param in self.params:
                        if param['name'] == errormodule:
                            param['field'].setToolTip(errortext)
                            param['icon'].setIcon(ErrorIcon)
                            param['field'].setStyleSheet('background-color: rgb(255,140,140);')
                            break
                self.listitem.setBackgroundColor(qtsoftred)
                self.listitem.setToolTip(errortext)
            else:
                self.listitem.setBackgroundColor(qtsoftgreen)
                parsedXML = parseXML(calld['stderr'])
                for param in self.params:
                    for parsedParam in parsedXML:
                        if param['name'] == parsedParam['name']:
                            param['field'].setText(parsedParam['val'])
                            break
            return valid

    def run(self):
        print "running module!"
        paramlist = []
        for param in self.params:
            if param['val']:
                paramlist.append('-' + param['name'])
                for item in param['val'].split(";"):
                    paramlist.append(item.strip('"'))
        result = self.call(1, *paramlist)
        print result


    def reset(self):
        self.params = []
        self.load()


class QpalsRunBatch():

    def __init__(self):
        self.command = ""
        self.loaded = True  # Always loaded

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

    def validate(self):
        pass

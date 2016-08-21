"""
/***************************************************************************
Name			 	 : qpalsModuleBase
Description          : base class and functions for all modules
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
import os, shlex
import copy
from xml.dom import minidom

import QpalsParamMsgBtn
import QTextComboBox
import QpalsDropTextbox
import QpalsParameter

IconPath = r"C:\Users\Lukas\.qgis2\python\plugins\qpals\\"

WaitIcon = QtGui.QIcon(IconPath + "wait_icon.png")
WaitIconMandatory = QtGui.QIcon(IconPath + "wait_icon_mandatory.png")
ErrorIcon = QtGui.QIcon(IconPath + "error_icon.png")

qtwhite = QtGui.QColor(255,255,255)
qtsoftred = QtGui.QColor(255,140,140)
qtsoftgreen = QtGui.QColor(140,255,140)

def parseXML(xml):
    dom = minidom.parseString(xml)
    outd = dict()
    for type in ['Specific', 'Global', 'Common']:
        elements = []
        specOptsNode = dom.getElementsByTagName(type)[0]
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
            elements.append(QpalsParameter.QpalsParameter(opt.attributes['Name'].value, valString, choiceList,
                                                          opt.attributes['Type'].value, opt.attributes['Opt'].value,
                                                          opt.attributes['Desc'].value,
                                                          opt.attributes['LongDesc'].value))
        outd[type] = elements
    return outd

class ModuleLoadWorker(QtCore.QObject):
    def __init__(self, module):
        QtCore.QObject.__init__(self)
        self.module = module
        self.killed = False

    def run(self):
        ret = None
        try:
            #print "loading"
            self.module.paramClass.load()
            #print "loaded"
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
                ret = (self.module, "42")
        except Exception as e:
            self.error.emit(e, str(e), self.module)
        self.finished.emit(ret)

    def kill(self):
        self.killed = True

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, basestring, object)
    progress = QtCore.pyqtSignal(float)

class QpalsModuleBase():
    def __init__(self, execName, QpalsProject, layerlist=None, listitem=None, visualize=False):
        self.params = []
        self.layerlist = layerlist
        self.project = QpalsProject
        self.execName = execName
        self.loaded = False
        self.view = False
        self.revalidate=False
        self.listitem = listitem
        self.currentlyvalidating = False
        self.validatethread = None
        self.validateworker = None
        self.lastpath = self.project.tempdir
        self.visualize = visualize
        self.outf = None
        self.globals = []
        self.common = []

    @staticmethod
    def fromCallString(string, project, layerlist):
        args = shlex.split(string)
        execName = os.path.join(project.opalspath, args[0])
        args.remove(args[0])
        for i in range(len(args)):  # Values with a space in between are supported by opals w/out quotes
            curarg = args[i]
            nextarg = args[i+1] if len(args) > i+1 else "-"
            if not curarg.startswith("-") and not nextarg.startswith("-"):
                args[i] = curarg + " " + nextarg
                args.remove(nextarg)
            if len(args) <= i+1:
                break
        args.append("--options")
        print args
        # call
        info = subprocess.STARTUPINFO()
        info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 0  # 0=HIDE
        proc = subprocess.Popen([execName] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE, cwd=project.workdir, startupinfo=info)
        proc.stdin.close()
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception('Call failed:\n %s' % stdout)
        xml_parsed = parseXML(stderr)
        newModuleBase = QpalsModuleBase(execName, project, layerlist)
        newModuleBase.load()
        for param in newModuleBase.params:
            print param.val
        newModuleBase.getParamUi()
        for param in newModuleBase.params:
            print param.field
        newModuleBase.params = QpalsParameter.mergeParamLists(newModuleBase.params, xml_parsed['Specific'])
        newModuleBase.globals = QpalsParameter.mergeParamLists(newModuleBase.globals, xml_parsed['Global'])
        newModuleBase.common = QpalsParameter.mergeParamLists(newModuleBase.common, xml_parsed['Common'])
        return newModuleBase

    def call(self, show=0, *args):
        info = subprocess.STARTUPINFO()
        info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = show  # 0=HIDE
        proc = subprocess.Popen([self.execName] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE, cwd=self.project.workdir, startupinfo=info)
        proc.stdin.close()
        stdout, stderr = proc.communicate()
        return {'stdout': stdout,
                'stderr': stderr,
                'returncode': proc.returncode}

    def load(self):
        calld = self.call(0, '--options')
        if calld['returncode'] != 0:
            raise Exception('Call failed:\n %s' % calld['stdout'])
        xml_parsed = parseXML(calld['stderr'])
        self.params = xml_parsed['Specific']
        self.globals = xml_parsed['Global']
        self.common = xml_parsed['Common']
        self.loaded = True

    def makefilebrowser(self, param):
        def showpathbrowser():
            filename = QtGui.QFileDialog.getSaveFileName(None, caption='Select file for %s'%param,
                                                          directory=self.lastpath,
                                                         options=QtGui.QFileDialog.DontConfirmOverwrite)
            if filename:
                for par in self.params:
                    if par.name == param:
                        par.field.setText(filename)
                self.lastpath = os.path.dirname(filename)
                self.updateVals(filename)
                self.validate()
        return showpathbrowser

    def getGlobalCommonParamsWindow(self, parent=None):
        window = QtGui.QDialog(parent)
        window.setWindowTitle("Global and common parameters")
        scrollarea = QtGui.QScrollArea()
        form = QtGui.QFormLayout()
        form.addRow(QtGui.QLabel("Common Parameters:"))
        for param in self.common:
            (l1, l2) = self.getUIOneliner(param, parent=parent, global_common=True)
            form.addRow(l1, l2)
        form.addRow(QtGui.QLabel("Global Parameters:"))
        for param in self.globals:
            (l1, l2) = self.getUIOneliner(param, parent=parent, global_common=True)
            form.addRow(l1, l2)
        closebtn = QtGui.QPushButton("Close")
        closebtn.clicked.connect(lambda: self.closeGlobalCommonParamsWindow(window))
        groupbox = QtGui.QGroupBox()
        groupbox.setLayout(form)
        scrollarea.setWidget(groupbox)
        window.setFixedHeight(600)
        window.setFixedWidth(600)
        scrollbox = QtGui.QVBoxLayout()
        scrollbox.addWidget(scrollarea)
        scrollbox.addWidget(closebtn)
        window.setLayout(scrollbox)
        return window

    def closeGlobalCommonParamsWindow(self, window):
        window.hide()
        for param in self.common:
            if param.use4proj.isChecked():
                self.project.common[param.name] = param.val
            else:
                if param.name in self.project.common:
                    del self.project.common[param.name]
        for param in self.globals:
            if param.use4proj.isChecked():
                self.project.globals[param.name] = param.val
            else:
                if param.name in self.project.globals:
                    del self.project.globals[param.name]

    def getUIOneliner(self, param, parent=None, global_common=False):
        l1 = QtGui.QLabel(param.name)
        if True: #len(param.choices) == 0:
            # TODO fix this?
            if "path" in param.type.lower():
                param.field = QpalsDropTextbox.QpalsDropTextbox(self.layerlist, param.val)
                if global_common:
                    param.field.textChanged.connect(self.updateCommonGlobals)
                else:
                    param.field.textChanged.connect(self.updateVals)
                param.field.editingFinished.connect(self.validate)

                param.browse = QtGui.QToolButton()
                param.browse.setText("...")
                param.browse.clicked.connect(self.makefilebrowser(param.name))
            else:
                param.field = QtGui.QLineEdit(param.val)
                if global_common:
                    param.field.textChanged.connect(self.updateCommonGlobals)
                else:
                    param.field.textChanged.connect(self.updateVals)
                param.field.editingFinished.connect(self.validate)

        else:
            param.field = QTextComboBox.QTextComboBox()
            for choice in param.choices:
                param.field.addItem(choice)
            # 'QString' is necessary so that the text and not the index will be passed as parameter
            if global_common:
                param.field.currentIndexChanged['QString'].connect(self.updateCommonGlobals)
            else:
                param.field.currentIndexChanged['QString'].connect(self.updateVals)

        if param.val:
            param.field.setText(param.val)

        param.icon = QpalsParamMsgBtn.QpalsParamMsgBtn(param, parent)
        param.icon.setToolTip(param.opt)
        param.icon.setIcon(WaitIcon)
        param.icon.setStyleSheet("border-style: none;")
        if param.opt == 'mandatory':
            param.icon.setIcon(WaitIconMandatory)
        l2 = QtGui.QHBoxLayout()
        l2.addWidget(param.field, stretch=1)
        if param.browse is not None:
            l2.addWidget(param.browse)
        l2.addWidget(param.icon)
        if global_common:
            param.use4proj = QtGui.QCheckBox("project setting")
            if param.name in self.project.common or param.name in self.project.globals:
                param.use4proj.setChecked(True)
                param.field.setText((self.project.globals_common())[param.name])
                param.field.setStyleSheet('background-color: rgb(200,255,200);')
            else:
                param.use4proj.setChecked(False)
                if param.changed:
                    param.field.setStyleSheet('background-color: rgb(200,255,200);')
            l2.addWidget(param.use4proj)

        return (l1, l2)


    def getParamUi(self, parent=None):
        if not self.loaded:
            self.load()
        form = QtGui.QFormLayout()
        for param in self.params:
            (l1, l2) = self.getUIOneliner(param, parent=parent)
            form.addRow(l1, l2)
        return form

    def updateCommonGlobals(self, string):
        for param in self.common:
            if param.field and string == param.field.text():
                if param.val != param.field.text():
                    self.revalidate = True
                    param.val = param.field.text()
                    param.changed = True
                    param.field.setStyleSheet('background-color: rgb(200,255,200);')

        for param in self.globals:
            if param.field and string == param.field.text():
                if param.val != param.field.text():
                    self.revalidate = True
                    param.val = param.field.text()
                    param.changed = True
                    param.field.setStyleSheet('background-color: rgb(200,255,200);')

    def updateVals(self, string):
        for param in self.params:
            print "name", param.name, "field", param.field
            if string == param.field.text():
                if param.val != param.field.text():
                    self.revalidate = True
                    if os.path.isabs(param.field.text()):
                        try:  # check if path is in working dir - use relative paths
                            relpath = os.path.relpath(os.path.normpath(param.field.text()), os.path.normpath(self.project.workdir))
                            if not relpath.startswith(".."):
                                param.field.setText(relpath)
                        except:  # file on different drive or other problem - use full path
                            pass
                    param.val = param.field.text()


    def validate_async(self):
        #print "val_async> ",
        if not self.currentlyvalidating and self.revalidate:
            #print "ok >",
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
        #print "validate finished> ",
        self.validateworker.deleteLater()
        self.validatethread.quit()
        self.validatethread.wait()
        self.validatethread.deleteLater()
        self.currentlyvalidating = False
        #print "validate done"


    def validate(self):
        if not self.revalidate:
            return
        self.revalidate = False
        allmandatoryset = True
        paramlist = []
        self.listitem.setBackgroundColor(qtwhite)
        self.listitem.setToolTip("")
        for param in self.params:
            if param.opt == 'mandatory':
                param.field.setToolTip('')
                param.field.setStyleSheet('')
                param.icon.setIcon(WaitIconMandatory)
                if not param.val:
                    allmandatoryset = False
            else:
                param.field.setStyleSheet('')
                param.field.setToolTip("")
                param.icon.setIcon(WaitIcon)
            if param.val:
                paramlist.append('-' + param.name)
                for item in param.val.split(";"):
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
                        if param.name == errormodule:
                            param.field.setToolTip(errortext)
                            param.icon.setIcon(ErrorIcon)
                            param.field.setStyleSheet('background-color: rgb(255,140,140);')
                            break
                self.listitem.setBackgroundColor(qtsoftred)
                self.listitem.setToolTip(errortext)
            else:
                self.listitem.setBackgroundColor(qtsoftgreen)
                parsedXML = parseXML(calld['stderr'])['Specific']
                for param in self.params:
                    for parsedParam in parsedXML:
                        if param.name == parsedParam.name:
                            param.field.setText(parsedParam.val)
                            break
            return valid

    def run(self, show=1, onlytext=False):
        paramlist = []
        for param in self.params:
            if param.val:
                paramlist.append('-' + param.name)
                for item in param.val.split(";"):
                    paramlist.append(item.strip('"'))
            if param.name == 'outFile':
                self.outf = param.val
        globcommon_set = []
        for param in self.globals:
            if param.val and param.changed:
                paramlist.append('-' + param.name)
                globcommon_set.append(param.name)
                for item in param.val.split(";"):
                    paramlist.append(item.strip('"'))
        for param in self.common:
            if param.val and param.changed:
                paramlist.append('-' + param.name)
                globcommon_set.append(param.name)
                for item in param.val.split(";"):
                    paramlist.append(item.strip('"'))
        project_globcomm = self.project.globals_common()
        for key in project_globcomm:
            if key not in globcommon_set:
                paramlist.append('-' + key)
                for item in project_globcomm[key].split(";"):
                    paramlist.append(item.strip('"'))
        if onlytext:
            return os.path.basename(self.execName) + " " + " ".join(paramlist)
        result = self.call(show, *paramlist)
        return result

    def reset(self):
        self.params = []
        self.visualize = False
        self.load()

    def __str__(self):
        return self.run(onlytext=True)


class QpalsRunBatch():
    revalidate = False
    visualize = False
    def __init__(self, t1="", t2=""):
        self.command = ""
        self.loaded = True  # Always loaded
        self.t1 = t1
        self.t2 = t2

    def getParamUi(self, parent=None):
        form = QtGui.QFormLayout()

        l1 = QtGui.QLabel("Command")
        self.e1 = QtGui.QLineEdit(self.t1)
        l2 = QtGui.QLabel("Working directory")
        self.e2 = QtGui.QLineEdit(self.t2)

        self.e1.editingFinished.connect(self.updateVals)
        self.e2.editingFinished.connect(self.updateVals)
        form.addRow(l1, self.e1)
        form.addRow(l2, self.e2)

        return form

    def updateVals(self):
        self.t1 = self.e1.text()
        self.t2 = self.e2.text()

    def reset(self):
        self.e1.setText("")
        self.t1 = ""
        self.e2.setText("")
        self.t2 = ""

    def validate(self):
        pass

    def run(self):
        if os.path.exists(self.t2) and os.path.isdir(self.t2):
            os.chdir(self.t2)
        os.system(self.t1)

    def __deepcopy__(self, memo={}):
        new = QpalsRunBatch()
        new.t1 = self.t1
        new.t2 = self.t2
        return new

    def __str__(self):
        return "cd %s /D\r\n%s"%(self.t2, self.t1)
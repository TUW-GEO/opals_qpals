"""
/***************************************************************************
Name			 	 : qpalsModuleBase
Description          : base class and functions for all modules
Date                 : 2016-05-21
copyright            : (C) 2016 by Lukas Winiwarter/GEO @ TU Wien
email                : lukas.winiwarter@geo.tuwien.ac.at
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
from __future__ import print_function
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import os
import shlex
import subprocess
import re
from xml.dom import minidom

from qgis.PyQt import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtCore import pyqtSlot

from .qt_extensions import QTextComboBox, QpalsDropTextbox, QCollapsibleGroupBox, QpalsParamBtns, QMultiSelectComboBox
from . import QpalsParameter
from .modules.QpalsAttributeMan import getAttributeInformation

IconPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "media")

WaitIcon = QtGui.QIcon(os.path.join(IconPath, "wait_icon.png"))
WaitIconMandatory = QtGui.QIcon(os.path.join(IconPath, "wait_icon_mandatory.png"))
ErrorIcon = QtGui.QIcon(os.path.join(IconPath, "error_icon.png"))

qtwhite = QtGui.QColor(255, 255, 255)
qtsoftred = QtGui.QColor(255, 140, 140)
qtsoftgreen = QtGui.QColor(140, 255, 140)


def get_percentage(s):
    t = re.compile(r"(\d+)%")
    match = t.search(s)
    if match:
        return match.group(1)
    return 100


def getTagContent(xml_tag):
    return xml_tag.firstChild.nodeValue


def parseXML(xml):
    xml = xml.decode('utf-8').encode('ascii', errors='ignore')
    try:
        dom = minidom.parseString(xml)
    except:
        raise Exception('Error: xml string (%s characters) could not be parsed \n %s' % (len(xml), str(xml)))
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
                    try:
                        for val in values:
                            valString += val.firstChild.nodeValue + ";"
                        valString = valString[:-1]
                    except:
                        valString = ""
                else:
                    if values[0].firstChild:
                        valString = values[0].firstChild.nodeValue
            if choices:
                for choice in choices:
                    choiceList.append(getTagContent(choice))
            #print(f"name={opt.attributes['Name'].value} type={opt.attributes['Type'].value}")
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
            self.module.paramClass.load()
            if not self.killed:
                self.progress.emit(100)
                ret = (self.module, "42",)
        except Exception as e:
            self.error.emit(e, str(e), self.module)
        self.finished.emit(ret)

    def kill(self):
        self.killed = True

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, str, object)
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
    error = QtCore.pyqtSignal(Exception, str, object)
    progress = QtCore.pyqtSignal(float)


class ModuleRunWorker(QtCore.QObject):
    def __init__(self, module):
        QtCore.QObject.__init__(self)
        self.module = module
        self.killed = [False]

    def run(self):
        ret_dict={
            'stdout': "",
            'stderr': "",
            'returncode': 1
        }
        try:
            ret_dict = self.module.paramClass.run(statusSignal=self.status, killSignal=self.killed)
            if not self.killed[0]:
                self.progress.emit(100)
        except Exception as e:
            self.error.emit(e, str(e), self.module)
            # fix_print_with_import
            #print(("Error:", str(e)))
        ret = (ret_dict, "", self.module)
        self.finished.emit(ret)

    @pyqtSlot()
    def stop(self):
        self.killed[0] = True

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, str, object)
    progress = QtCore.pyqtSignal(float)
    status = QtCore.pyqtSignal(str)


class ModuleBaseRunWorker(QtCore.QObject):
    def __init__(self, module):
        QtCore.QObject.__init__(self)
        self.module = module
        self.killed = [False]

    def run(self):
        ret_dict={
            'stdout': "",
            'stderr': "",
            'returncode': 1
        }
        try:
            ret_dict = self.module.run(statusSignal=self.status, killSignal=self.killed)
            if not self.killed[0]:
                self.progress.emit(100)
        except Exception as e:
            self.error.emit(e, str(e), self.module)
            # fix_print_with_import
            #print(("Error:", str(e)))
        ret = (ret_dict, "", self.module)
        self.finished.emit(ret)

    @pyqtSlot()
    def stop(self):
        self.killed[0] = True

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, str, object)
    progress = QtCore.pyqtSignal(float)
    status = QtCore.pyqtSignal(str)



class QpalsModuleBase(object):
    def __init__(self, execName, QpalsProject, layerlist=None, listitem=None, visualize=False):
        self.params = []
        self.layerlist = layerlist
        self.project = QpalsProject
        self.execName = execName
        self.loaded = False
        self.view = False
        self.revalidate = False
        self.listitem = listitem
        self.currentlyvalidating = False
        self.validatethread = None
        self.validateworker = None
        self.runthread = None
        self.runworker = None
        self.afterRun = None
        self.onErr = None
        self.lastpath = self.project.tempdir
        self.visualize = visualize
        self.outf = None
        self.globals = []
        self.common = []
        self.progressbar = None
        self.runbtn = None

    def updateBar(self, message):
        out_lines = ["Stage 0: Initializing"] + [item for item in re.split("[\n\r\b]", message) if item]
        curr_stage = [stage for stage in out_lines if "Stage" in stage][-1]
        percentage = out_lines[-1]
        if r"%" in percentage:
            perc = get_percentage(percentage)
            self.progressbar.setValue(int(perc))
            self.progressbar.setFormat(curr_stage + " - %p%")

    def errorBar(self, message):
        self.progressbar.setValue(100)
        self.progressbar.setFormat("Error: %s" % message)
        print(("error:", message))

    @classmethod
    def fromCallString(cls, string, project, layerlist):
        args = shlex.split(string)
        execName = os.path.join(project.opalspath, args[0])
        args.remove(args[0])
        # for i in range(len(args)):  # Values with a space in between are supported by opals w/out quotes
        #     curarg = args[i]
        #     nextarg = args[i + 1] if len(args) > i + 1 else "-"
        #     if not curarg.startswith("-") and not nextarg.startswith("-"):
        #         args[i] = curarg + " " + nextarg
        #         args.remove(nextarg)
        #     if len(args) <= i + 1:
        #         break
        args.append("--options")
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
        newModuleBase = cls(execName, project, layerlist)
        newModuleBase.load()
        newModuleBase.getParamUi()
        newModuleBase.params = QpalsParameter.mergeParamLists(newModuleBase.params, xml_parsed['Specific'])
        newModuleBase.globals = QpalsParameter.mergeParamLists(newModuleBase.globals, xml_parsed['Global'])
        newModuleBase.common = QpalsParameter.mergeParamLists(newModuleBase.common, xml_parsed['Common'])
        return newModuleBase

    @classmethod
    def createGroupBox(cls, module_name, box_header, project, params, param_show_list):
        box = QtWidgets.QGroupBox(box_header)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(box)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        status = QtWidgets.QListWidgetItem("hidden status")
        mod = cls(execName=os.path.join(project.opalspath, module_name + ".exe"),
                  QpalsProject=project)
        mod.listitem = status
        mod.load()
        for p in mod.params:
            if p.name in params:
                p.val = params[p.name]
                p.changed = True
        ui = mod.getFilteredParamUi(filter=param_show_list)
        advancedBox = QCollapsibleGroupBox.QCollapsibleGroupBox("Advanced options")
        advancedBox.setChecked(False)
        ui.addRow(advancedBox)
        advancedLa = mod.getFilteredParamUi(notfilter=param_show_list)
        advancedBox.setLayout(advancedLa)
        runbar = QtWidgets.QHBoxLayout()
        runprogress = QtWidgets.QProgressBar()
        mod.progressbar = runprogress
        mod.runbtn = QtWidgets.QPushButton("Run module")
        mod.runbtn.clicked.connect(mod.run_async_self)
        runbar.addWidget(runprogress)
        runbar.addWidget(mod.runbtn)
        ui.addRow(runbar)
        box.setLayout(ui)
        height = box.minimumSizeHint().height()
        scroll.setFixedHeight(height + 10)

        return mod, scroll

    def getParam(self, paramname):
        for param in self.params:
            if param.name.lower() == paramname.lower():
                return param
        return None

    def setParam(self, paramname, val):
        for param in self.params:
            if param.name.lower() == paramname.lower():
                param.field.setText(val)
                self.updateVals(val)
                break

    def call(self, show=0, statusSignal=None, killSignal=None, *args):
        info = subprocess.STARTUPINFO()
        info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = show  # 0=HIDE
        # print( " ".join([self.execName] + list(args)) )
        my_env = os.environ.copy()
        opalsroot = os.path.realpath(os.path.join(self.project.opalspath, ".."))
        my_env["GDAL_DRIVER_PATH"] = ""  # clear gdal driver paths, since this messes with some opals modules
        my_env["PATH"] = self.project.PATH
        my_env["PYTHONPATH"] = str(opalsroot)
        my_env["PYTHONHOME"] = ""
        my_env["GDAL_DATA"] = str(os.path.join(opalsroot, "addons", "crs"))
        my_env["PROJ_LIB"] = my_env["GDAL_DATA"]

        proc = subprocess.Popen([self.execName] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE, cwd=self.project.workdir, startupinfo=info, env=my_env)
        #print(my_env)
        proc.stderr.flush()
        proc.stdin.close()
        if statusSignal is None:
            stdout, stderr = proc.communicate()
            stdout = stdout.decode()
        else:
            stdout = ""
            killflag = False
            while proc.poll() is None:
                QtWidgets.QApplication.processEvents()
                if killSignal[0] and not killflag:
                    proc.kill()
                    killflag = True
                    statusSignal.emit("Stopped Execution.")
                    return
                currstdout = proc.stdout.read(1)  # read byte for byte while it is running
                stdout += currstdout.decode()
                if stdout[-1] in ["\n", "\b"]:
                    statusSignal.emit(stdout)
            currstdout = proc.stdout.read()  # read the rest once the process is finished
            stdout += currstdout.decode()
            statusSignal.emit(stdout)
            stderr = "\n".join([bytes.decode() for bytes in proc.stderr.readlines()])

        return {'stdout': stdout,
                'stderr': stderr,
                'returncode': proc.returncode}

    def load(self):
        calld = self.call(0, None, None, '--options')
        if calld['returncode'] != 0:
            raise Exception('Call failed:\n %s' % calld['stdout'])
        xml_parsed = parseXML(calld['stderr'])
        self.params = xml_parsed['Specific']
        self.globals = xml_parsed['Global']
        self.common = xml_parsed['Common']
        self.loaded = True

    def makefilebrowser(self, param):
        def showpathbrowser():
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(None, caption='Select file for %s' % param,
                                                         directory=self.lastpath,
                                                         options=QtWidgets.QFileDialog.DontConfirmOverwrite)
            if filename:
                if isinstance(filename, tuple):
                    filename = filename[0]
                for par in self.params:
                    if par.name == param:
                        par.field.setText(filename)
                self.lastpath = os.path.dirname(filename)
                self.updateVals(filename)
                self.validate()

        return showpathbrowser

    def getGlobalCommonParamsWindow(self, parent=None):
        window = QtWidgets.QDialog()
        window.setWindowTitle("Global and common parameters")
        scrollarea = QtWidgets.QScrollArea()
        form = QtWidgets.QFormLayout()
        form.addRow(QtWidgets.QLabel("Common Parameters:"))
        for param in self.common:
            (l1, l2) = self.getUIOneliner(param, global_common=True)
            form.addRow(l1, l2)
        form.addRow(QtWidgets.QLabel("Global Parameters:"))
        for param in self.globals:
            (l1, l2) = self.getUIOneliner(param, global_common=True)
            form.addRow(l1, l2)
        closebtn = QtWidgets.QPushButton("Close")
        closebtn.clicked.connect(lambda: self.closeGlobalCommonParamsWindow(window))
        groupbox = QtWidgets.QGroupBox()
        groupbox.setLayout(form)
        scrollarea.setWidget(groupbox)
        window.setFixedHeight(600)
        window.setFixedWidth(600)
        scrollbox = QtWidgets.QVBoxLayout()
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
        l1 = QtWidgets.QLabel(param.name)
        if len(param.choices) == 0:
            if "path" in param.type.lower() or 'VectorOrRasterFile' in param.type:
                param.field = QpalsDropTextbox.QpalsDropTextbox(self.layerlist, param.val)
                param.field.setMinimumContentsLength(20)
                param.field.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLength)
                if global_common:
                    param.field.textChanged.connect(self.updateCommonGlobals)
                else:
                    param.field.textChanged.connect(self.updateVals)
                param.field.editingFinished.connect(self.validate)

                param.browse = QtWidgets.QToolButton()
                param.browse.setText("...")
                param.browse.clicked.connect(self.makefilebrowser(param.name))
                if "infile" in param.name.lower():
                    param.field.editingFinished.connect(self.inFileUpdated)

            elif "attribute" in param.name.lower():
                param.field = QTextComboBox.QTextComboBox()
                param.field.setEditable(True)
                param.field.setText(param.val)
                if global_common:
                    param.field.editTextChanged.connect(self.updateCommonGlobals)
                else:
                    param.field.editTextChanged.connect(self.updateVals)

            else:
                param.field = QtWidgets.QLineEdit(param.val)
                if global_common:
                    param.field.textChanged.connect(self.updateCommonGlobals)
                else:
                    param.field.textChanged.connect(self.updateVals)
                param.field.editingFinished.connect(self.validate)
        else:
            isMultiSel = param.type.startswith("Vector")
            if isMultiSel:
                #print(f"name={param.name} type={param.type} val={param.val}")
                param.field = QMultiSelectComboBox.QMultiSelectComboBox()
            else:
                param.field = QTextComboBox.QTextComboBox()
            for choice in param.choices:
                param.field.addItem(choice)
            param.field.setText(param.val)
            if isMultiSel:
                if global_common:
                    param.field.checkedItemsChanged.connect(self.updateCommonGlobals)
                else:
                    param.field.checkedItemsChanged.connect(self.updateVals)
            else:
                # 'QString' is necessary so that the text and not the index will be passed as parameter
                if global_common:
                    param.field.activated['QString'].connect(self.updateCommonGlobals)
                else:
                    param.field.activated['QString'].connect(self.updateVals)

        param.icon = QpalsParamBtns.QpalsParamMsgBtn(param, parent)
        param.icon.setToolTip(param.opt)
        param.icon.setIcon(WaitIcon)
        param.icon.setStyleSheet("border-style: none;")
        if param.opt == 'mandatory':
            param.icon.setIcon(WaitIconMandatory)
        l2 = QtWidgets.QHBoxLayout()
        param.changedIcon = QpalsParamBtns.QpalsLockIconBtn(param)
        l2.addWidget(param.changedIcon)
        l2.addWidget(param.field, stretch=1)
        if param.browse is not None:
            l2.addWidget(param.browse)
        l2.addWidget(param.icon)
        if global_common:
            param.use4proj = QtWidgets.QCheckBox("project setting")
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

    def inFileUpdated(self):
        attrp = None
        attri = None
        for param in self.params:
            if param.name.lower() == "attribute":
                attrp = param
            if param.name.lower() == "infile":
                attri = param
        if attrp and attri:
            attrp.field.clear()
            attrp.field.addItems(["X", "Y", "Z"])
            attrp.field.setCurrentIndex(2)
            try:
                attrs, entries = getAttributeInformation(attri.val, self.project)
                if attrs:
                    for attr in attrs:
                        attrp.field.addItem(attr[0])
                attrp.field.setCurrentIndex(2)
            except Exception as e:
                self.project.iface.messageBar().pushMessage(
                    'Something went wrong! See the message log for more information.',
                    duration=3)
                import traceback
                traceback.print_exc()

    def getParamUi(self, parent=None):
        if not self.loaded:
            self.load()
        form = QtWidgets.QFormLayout()
        for param in self.params:
            (l1, l2) = self.getUIOneliner(param, parent=parent)
            form.addRow(l1, l2)
        return form

    def getFilteredParamUi(self, parent=None, filter=[], notfilter=[]):
        if not self.loaded:
            self.load()
        form = QtWidgets.QFormLayout()
        for param in self.params:
            if (len(filter) > 0 and re.match(r"(?=(" + '|'.join(filter) + '))', param.name)) or \
                    (len(notfilter) > 0 and not re.match(r"(?=(" + '|'.join(notfilter) + '))', param.name)):
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
                    param.changedIcon.setIcon(QpalsParamBtns.lockedIcon)
                    param.field.setStyleSheet('background-color: rgb(200,255,200);')

        for param in self.globals:
            if param.field and string == param.field.text():
                if param.val != param.field.text():
                    self.revalidate = True
                    param.val = param.field.text()
                    param.changed = True
                    param.changedIcon.setIcon(QpalsParamBtns.lockedIcon)
                    param.field.setStyleSheet('background-color: rgb(200,255,200);')

    def updateVals(self, string):
        if isinstance(string, list):
            string = ";".join(string)
        #print(f"updateVals={string}")
        for param in self.params:
            if string == param.field.text():
                #print(f"string={string}  param.field.text()={param.field.text()}")
                if param.val != param.field.text():
                    self.revalidate = True
                    param.changed = True
                    param.changedIcon.setIcon(QpalsParamBtns.lockedIcon)
                    if os.path.isabs(param.field.text()):
                        try:  # check if path is in working dir - use relative paths
                            relpath = os.path.relpath(os.path.normpath(param.field.text()),
                                                      os.path.normpath(self.project.workdir))
                            if not relpath.startswith(".."):
                                param.field.setText(relpath)
                        except:  # file on different drive or other problem - use full path
                            pass
                    param.val = param.field.text()
                    #print(f"name={param.name} has changed to val={param}")

    def validate_async(self):
        # print "val_async> ",
        if not self.currentlyvalidating and self.revalidate:
            # print "ok >",
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
        # module.setIcon(self.errorIcon)

    def validateFinished(self, module):
        # print "validate finished> ",
        self.validateworker.deleteLater()
        self.validatethread.quit()
        self.validatethread.wait()
        self.validatethread.deleteLater()
        self.currentlyvalidating = False
        # print "validate done"

    def validate(self):
        if not self.revalidate:
            return
        self.revalidate = False
        allmandatoryset = True
        paramlist = []
        self.listitem.setBackground(qtwhite)
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
            calld = self.call(0, None, None, '--options', '1', *paramlist)
            valid = True
            if calld['returncode'] != 0:
                valid = False
                self.parseErrorMessage(calld)
            else:
                self.listitem.setBackground(qtsoftgreen)
                parsedXML = parseXML(calld['stderr'])['Specific']
                for param in self.params:
                    for parsedParam in parsedXML:
                        if param.name == parsedParam.name and not param.changed:
                            param.field.setText(parsedParam.val)
                            break
            return valid

    def parseErrorMessage(self, calld):
        errormodule = ""
        if "Apply values to option" in calld['stdout']:
            print(calld['stdout'])
            reMessage = re.compile("(?P<message>ERROR.*)Scope stack", re.DOTALL)
            reParameter = re.compile("Apply values to option\s+(?P<param>\w+)\.")
            maMsg = reMessage.search(calld['stdout'])
            maParam = reParameter.search(calld['stdout'])
            if maMsg and maParam:
                errortext = maMsg.group("message").strip()
                errormodule = maParam.group("param")
            else:
                print(f"Cannot parse message: {calld['stdout']}")
        elif "Error in parameter" in calld['stdout']:
            errortext = calld['stdout'].split("Error in parameter ")[1].split("\n")[0]
            errormodule = errortext.split(":")[0]
            errortext = ":".join(errortext.split(":")[1:])
            # print errormodule, errortext
        elif "Ambiguities while matching value" in calld['stdout']:
            errortext = calld['stdout'].split("ERROR 0001: std::exception: ")[1].split("\n")[0]
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Question)
            msg.setText(errortext.split(".")[0])
            msg.setInformativeText(".".join(errortext.split(".")[1:]))
            msg.setWindowTitle("Ambiguities while setting parameter values")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()
        elif "ERROR 1000: the argument " in calld['stdout']:
            errortext = calld['stdout'].split("ERROR 1000:")[1].split("\n")[0]
            errormodule = errortext.split("for option '")[1].split("' is invalid")[0]
        elif "Applying parsed value to option " in calld['stdout']:
            errortext = calld['stdout']
            errormodule = errortext.split("Applying parsed value to option")[1].split()[0]
        elif "Return number too large to be stored with this point record format." in calld['stdout']:
            errortext = calld['stdout']
            errormodule = 'oFormat'
        elif "Validation failed for" in calld['stdout']:
            errortext = calld['stdout']
            errormodule = errortext.split("Validation failed for ")[1].split()[0]
        else:
            errortext = "Unknown error."
            raise Exception('Call failed:\n %s' % calld['stdout'])
        if len(errortext) > 500:
            errortext = "(%s more characters)..." % (len(errortext) - 500) + errortext[-500:]
            errortext += "\nRun the module and look at the log for more details."
        if errormodule:
            for param in self.params:
                if param.name == errormodule:
                    param.field.setToolTip(errortext)
                    param.icon.setIcon(ErrorIcon)
                    param.field.setStyleSheet('background-color: rgb(255,140,140);')
                    break
        self.listitem.setBackground(qtsoftred)
        self.listitem.setToolTip(errortext)

    def run(self, show=0, onlytext=False, statusSignal=None, killSignal=None):
        paramlist = []
        for param in self.params:
            if param.val:
                paramlist.append('-' + param.name)
                for item in param.val.split(";"):
                    paramlist.append(item.strip('"'))
            elif param.flag_mode:
                paramlist.append('-' + param.name)
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
        result = self.call(show, statusSignal, killSignal, *paramlist)
        return result

    def reset(self):
        self.params = []
        self.visualize = False
        self.load()

    def __str__(self):
        return self.run(onlytext=True)

    def run_async(self, on_finish=None, on_error=None, status=None, abort_signal=None, run_now=True):
        worker = ModuleBaseRunWorker(self)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        if on_error:
            worker.error.connect(on_error)
        if on_finish:
            worker.finished.connect(on_finish)
        if status:
            worker.status.connect(status)
        if abort_signal:
            abort_signal.connect(worker.stop)
        worker.finished.connect(thread.quit)
        thread.started.connect(worker.run)
        if run_now:
            thread.start()
        return thread, worker

    def run_async_self(self, on_error=None, abort_signal=None):
        status = self.updateBar
        on_finish = self.run_async_finished
        on_error = self.errorBar
        if self.onErr:
            on_error = self.onErr
        self.runbtn.setText("running")
        self.runbtn.setEnabled(False)
        self.runthread, self.runworker = self.run_async(status=status,
                                                        on_finish=on_finish,
                                                        on_error=on_error,
                                                        abort_signal=abort_signal)

    def run_async_finished(self, ret):
        calld, msg, mod = ret
        if calld['returncode'] != 0:
             self.parseErrorMessage(calld)
             self.progressbar.setFormat("Error: " + msg)
        else:
            if self.runbtn:
                self.runbtn.setText("done")
                self.runbtn.setEnabled(True)
                self.progressbar.setFormat("%p%")
                self.progressbar.setValue(100)
            if self.afterRun:
                self.afterRun()


class QpalsRunBatch(object):
    revalidate = False
    visualize = False

    def __init__(self, t1="", t2=""):
        self.command = ""
        self.loaded = True  # Always loaded
        self.t1 = t1
        self.t2 = t2

    def getParamUi(self, parent=None):
        form = QtWidgets.QFormLayout()

        l1 = QtWidgets.QLabel("Command")
        self.e1 = QtWidgets.QLineEdit(self.t1)
        l2 = QtWidgets.QLabel("Working directory")
        self.e2 = QtWidgets.QLineEdit(self.t2)

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

    def run(self, **kwargs):
        if os.path.exists(self.t2) and os.path.isdir(self.t2):
            os.chdir(self.t2)
        rc = os.system(self.t1)
        return {'returncode': rc,
                'stdout': "",
                'stderr': "",
                }


    def parseErrorMessage(self, calld):
         print(calld)

    def __deepcopy__(self, memo={}):
        new = QpalsRunBatch()
        new.t1 = self.t1
        new.t2 = self.t2
        return new

    def __str__(self):
        if os.path.isdir(self.t2):
            return "cd %s /D\r\n%s" % (self.t2, self.t1)
        else:
            return self.t1

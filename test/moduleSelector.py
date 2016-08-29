"""
/***************************************************************************
Name			 	 : moduleSelector
Description          : UI class for displaying a module selector
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
from QpalsListWidgetItem import QpalsListWidgetItem
from QpalsModuleBase import QpalsModuleBase, QpalsRunBatch, ModuleLoadWorker, ModuleRunWorker
import QpalsShowFile
import glob, os


qtwhite = QtGui.QColor(255,255,255)
qtsoftred = QtGui.QColor(255,140,140)


class moduleSelector(QtGui.QDialog):

    IconPath = r"C:\Users\Lukas\.qgis2\python\plugins\qpals\\"
    opalsIcon = QtGui.QIcon(IconPath + "icon.png")
    cmdIcon = QtGui.QIcon(IconPath + "cmd_icon.png")
    loadingIcon = QtGui.QIcon(IconPath + "spinner_icon.png")
    errorIcon = QtGui.QIcon(IconPath + "error_icon.png")
    checkIcon = QtGui.QIcon(IconPath + "checkIcon.png")

    def getModulesAvailiable(self):
        for opalsexe in glob.glob(os.path.join(self.project.opalspath , "opals*.exe")):
            self.modulesAvailiable.append({'name': os.path.basename(opalsexe).split(".exe")[0],
                                           'icon': self.opalsIcon,
                                           'class': QpalsModuleBase(opalsexe,self.project, layerlist=self.layerlist)})
        self.modulesAvailiable.append({'name': "User-defined cmd", 'icon': self.cmdIcon, 'class': QpalsRunBatch()})


    def __init__(self, iface, layerlist, project):
        super(moduleSelector, self).__init__(None)#, QtCore.Qt.WindowStaysOnTopHint)
        self.project = project
        self.iface = iface
        self.layerlist = layerlist
        self.curmodule=None
        self.modulesAvailiable = []

        self.getModulesAvailiable()
        self.initUi()
        self.resize(1200, 600)
        self.workerrunning = False
        self.threads = []
        self.workers = []
        self.runningRunList = False
        self.currentruncount = 0

        self.runModuleSelected = None

    def initUi(self):

        groupSelect = QtGui.QGroupBox()
        self.moduleList = QtGui.QListWidget()
        for moduleDict in self.modulesAvailiable:
            module = QpalsListWidgetItem(moduleDict)
            module.paramClass.listitem = module
            self.moduleList.addItem(module)
        self.moduleList.itemClicked.connect(self.loadModuleAsync)

        filterBox = QtGui.QHBoxLayout()
        filterBox.addWidget(QtGui.QLabel("Filter:"))
        self.filterText = QtGui.QLineEdit()
        self.filterText.textChanged.connect(self.filterModuleList)
        filterBox.addWidget(self.filterText, stretch=1)
        filterClear = QtGui.QPushButton()
        filterClear.setText("X")
        filterClear.setMaximumWidth(20)
        filterClear.pressed.connect(self.clearFilterText)
        filterBox.addWidget(filterClear)
        self.loadAllBtn = QtGui.QPushButton()
        self.loadAllBtn.setText("load all")
        self.loadAllBtn.pressed.connect(self.loadAllModules)
        filterBox.addWidget(self.loadAllBtn)

        groupSelect.setTitle("Module Selector")
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.moduleList, stretch=1)
        vbox.addLayout(filterBox)
        groupSelect.setLayout(vbox)

        self.moduleparamLayout = QtGui.QVBoxLayout()

        self.moduleparamBox = QtGui.QGroupBox()
        self.moduleparamBox.setTitle("Module parameters")
        self.moduleparamBox.setLayout(self.moduleparamLayout)

        rungroup = QtGui.QGroupBox()
        rungroup.setTitle("Run list")
        self.runListWidget = QtGui.QListWidget()
        #self.runListWidget.currentItemChanged.connect(self.loadModuleAsync)
        self.runListWidget.itemClicked.connect(self.loadModuleAsync)
        self.runListWidget.setDragEnabled(True)
        self.runListWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

        runAllBtn = QtGui.QPushButton()
        runAllBtn.setText("Run")
        runAllBtn.clicked.connect(self.runRunList)

        runDelZone = QpalsDeleteLabel("Drop here to remove")
        runDelZone.setAcceptDrops(True)

        runvbox = QtGui.QVBoxLayout()
        runvbox.addWidget(self.runListWidget, stretch=1)
        runhbox = QtGui.QHBoxLayout()
        runhbox.addWidget(runDelZone)
        runhbox.addWidget(runAllBtn)
        runvbox.addLayout(runhbox)
        saveloadbox = QtGui.QHBoxLayout()
        savbtn = QtGui.QPushButton("Save .bat")
        loadbtn = QtGui.QPushButton("Load .bat")
        savbtn.clicked.connect(self.saveRunList)
        loadbtn.clicked.connect(self.loadRunList)
        saveloadbox.addWidget(savbtn)
        saveloadbox.addWidget(loadbtn)

        self.pbar = QtGui.QProgressBar()
        self.pbar.setValue(100)
        runvbox.addWidget(self.pbar)
        runvbox.addLayout(saveloadbox)
        rungroup.setLayout(runvbox)

        grpBoxContainer = QtGui.QHBoxLayout()
        grpBoxContainer.addWidget(groupSelect)
        grpBoxContainer.addWidget(self.moduleparamBox, stretch=1)
        grpBoxContainer.addWidget(rungroup)

        lowerhbox = QtGui.QHBoxLayout()

        overallBox = QtGui.QVBoxLayout()
        overallBox.addLayout(grpBoxContainer)
        overallBox.addLayout(lowerhbox)

        self.main_widget = QtGui.QWidget()
        self.main_widget.setLayout(overallBox)
        self.setLayout(overallBox)
        self.setWindowTitle('qpals')

    def filterModuleList(self, text):
        self.moduleList.clear()
        for moduleDict in self.modulesAvailiable:
            if text.lower() in moduleDict['name'].lower():
                module = QpalsListWidgetItem(moduleDict)
                module.paramClass.listitem = module
                self.moduleList.addItem(module)

    def startWorker(self, module):
        #https://snorfalorpagus.net/blog/2013/12/07/multithreading-in-qgis-python-plugins/
        if self.workerrunning:
            return
        self.workerrunning = True
        worker = ModuleLoadWorker(module)
        module.setIcon(self.loadingIcon)
        self.moduleList.setEnabled(False)
        # start the worker in a new thread
        thread = QtCore.QThread(self)
        worker.moveToThread(thread)
        worker.finished.connect(self.workerFinished)
        worker.error.connect(self.workerError)
        thread.started.connect(worker.run)
        thread.start()
        self.thread = thread
        self.worker = worker

    def workerFinished(self, ret):
        # clean up the worker and thread
        self.worker.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()
        if ret is not None:
            # report the result
            module, code = ret
            module.setIcon(module.icon)
            self.loadModule(module)
        else:
            # notify the user that something went wrong
            self.iface.messageBar().pushMessage('Something went wrong! See the message log for more information.', duration=3)
        self.workerrunning = False
        self.moduleList.setEnabled(True)

    def workerError(self, e, exception_string, module):
        print('Worker thread raised an exception: {}\n'.format(exception_string))
        module.setIcon(self.errorIcon)
        self.workerrunning = False

    def loadModuleAsync(self, module):
        self.moduleList.clearSelection()
        self.runListWidget.clearSelection()
        self.runModuleSelected = module
        if module and isinstance(module.paramClass, QpalsModuleBase):
            if module.paramClass.loaded:
                self.loadModule(module)
                self.viewbox.setChecked(module.paramClass.visualize)
            else:
                self.startWorker(module)
        else:
            self.loadModule(module)  # display "select a module"

    def loadModule(self, module):
        if module:  # can happen if it gets filtered away
            form = QtGui.QVBoxLayout()
            self.moduleparamBox.setTitle("Parameters for " + module.text())
            parameterform = module.paramClass.getParamUi(parent=self)
            form.addLayout(parameterform, stretch=1)
            # reset / run / add to list / add to view
            resetbar = QtGui.QHBoxLayout()
            resetbtn = QtGui.QPushButton("Reset")
            resetbtn.clicked.connect(lambda: self.resetModule(module))
            runbtn = QtGui.QPushButton("Run now")
            runbtn.clicked.connect(lambda: self.runModuleAsync(module))
            addbtn = QtGui.QPushButton("Add to run list >")
            addbtn.clicked.connect(self.addToRunList)
            if "opals" in module.text():
                self.viewbox = QtGui.QCheckBox("Add result to canvas")
                self.viewbox.clicked.connect(self.viewboxChanged)
                self.commonbtn = QtGui.QPushButton("Common and Global parameters")
                self.commonwin = module.paramClass.getGlobalCommonParamsWindow(parent=self)
                self.commonbtn.clicked.connect(self.commonwin.show)
                form.addWidget(self.commonbtn)
            #viewbox.stateChanged.connect(module.paramClass.view = viewbox.isChecked())
            resetbar.addStretch(1)
            resetbar.addWidget(resetbtn)
            resetbar.addWidget(runbtn)
            resetbar.addWidget(addbtn)
            if "opals" in module.text():
                resetbar.addWidget(self.viewbox)
            #resetbar.addWidget(commonbtn)
            #resetbar.addWidget(globalbtn)
            form.addLayout(resetbar)
            module.paramClass.revalidate = True
            module.paramClass.validate()
            self.curmodule = module
        else:
            form = QtGui.QHBoxLayout()
            l1 = QtGui.QLabel("No module selected...")
            form.addWidget(l1)
            self.moduleparamBox.setTitle("Module Parameters")

        self.clearLayout(self.moduleparamLayout)
        self.moduleparamLayout.addLayout(form)

    def resetModule(self, module):
        module.paramClass.reset()
        module.setBackgroundColor(qtwhite)
        self.clearLayout(self.moduleparamLayout)
        self.loadModule(module)

    def clearFilterText(self):
        self.filterText.setText("")

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def loadAllModules(self):
        for module_id in range(self.moduleList.count()-1):
            module = self.moduleList.item(module_id)
            try:
                module.paramClass.load()
            except Exception as e:
                print e
        self.loadAllBtn.hide()

    def viewboxChanged(self):
        self.curmodule.paramClass.visualize = self.viewbox.isChecked()

    def addToRunList(self):
        import copy
        modulecopy = copy.deepcopy(self.curmodule)
        self.runListWidget.addItem(modulecopy)
        modulecopy.paramClass.revalidate = True
        self.resetModule(self.curmodule)

    def runModuleAsync(self, module):
        worker = ModuleRunWorker(module)
        thread = QtCore.QThread(self)
        worker.moveToThread(thread)
        worker.finished.connect(self.runModuleWorkerFinished)
        worker.error.connect(self.runModuleWorkerError)
        thread.started.connect(worker.run)
        thread.start()
        self.threads.append(thread)
        self.workers.append(worker)

    def runModuleWorkerFinished(self, ret):
        module, code = ret
        moduleClass = module.paramClass
        if moduleClass.visualize and moduleClass.outf:
            if not os.path.isabs(moduleClass.outf):
                moduleClass.outf = os.path.join(self.project.tempdir, moduleClass.outf).replace("\\", "/")
            showfile = QpalsShowFile.QpalsShowFile(self.project.iface, self.layerlist, self.project)
            showfile.load(infile_s=[moduleClass.outf])
        if self.runningRunList == True:
            module.setIcon(self.checkIcon)
            self.currentruncount += 1
            self.runRunList()

    def runModuleWorkerError(self, e, message, module):
        pass

    def runRunList(self):
        self.runningRunList = True
        self.pbar.setValue(int(100*self.currentruncount/self.runListWidget.count()))
        if self.runListWidget.count() > self.currentruncount:
            self.runModuleAsync(self.runListWidget.item(self.currentruncount))
        else:
            self.runningRunList = False
            self.currentruncount = 0

    def saveRunList(self):
        saveTo = QtGui.QFileDialog.getSaveFileName(None, caption='Save to file')
        if True:
            f = open(saveTo, 'w')
            f.write("rem BATCH FILE CREATED WITH QPALS\r\n")
            for i in range(self.runListWidget.count()):
                item = self.runListWidget.item(i)
                module = item.paramClass
                f.write(str(module) + "\r\n")
            f.close()

    def loadRunList(self):
        loadFrom = QtGui.QFileDialog.getOpenFileName(None, caption='Load from file')
        f = open(loadFrom, 'r')
        lines = f.readlines()
        skipnext = False
        for i in range(len(lines)):
            try:
                if not skipnext:
                    line = lines[i]
                    nextline = lines[i+1] if len(lines) > i+1 else ""
                    if line[0:3].lower() == "rem" or line.startswith("::"):
                        module = None
                    elif line.startswith("opals"):
                        ModuleBase = QpalsModuleBase.fromCallString(line, self.project, self.layerlist)
                        module = QpalsListWidgetItem({'name': line.split()[0].split(".exe")[0],
                                                   'icon': self.opalsIcon,
                                                   'class': ModuleBase})
                        ModuleBase.listitem = module
                    else:
                        if line.startswith("cd ") and not (nextline.startswith("rem")
                                                    or nextline.startswith("::")
                                                    or nextline.startswith("opals")):
                            chdir = line[3:].strip().strip("/D")
                            call = nextline.strip()
                            skipnext = True
                        else:
                            chdir = ""
                            call = line.strip()
                        module = QpalsListWidgetItem({'name': "User-defined cmd", 'icon': self.cmdIcon,
                                                      'class': QpalsRunBatch(call, chdir)})
                    if module:
                        self.runListWidget.addItem(module)
            except Exception as e:
                print e

class QpalsDeleteLabel(QtGui.QLabel):

    def __init__(self, *args, **kwargs):
        super(QpalsDeleteLabel, self).__init__(*args, **kwargs)

    def dragEnterEvent(self, e):
        self.setText("Release to delete module")
        e.accept()

    def dragLeaveEvent(self, *args, **kwargs):
        self.setText("Drop here to remove")

    def dropEvent(self, e):
        self.setText("Drop here to remove")
        e.accept()
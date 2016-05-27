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
from QpalsModuleBase import QpalsModuleBase, QpalsRunBatch, ModuleWorker
import glob, os

class moduleSelector(QtGui.QDialog):

    opalsPath = r"D:\01_opals\01_nightly\opals\\"
    opalsPath = r"D:\01_Opals\02_Installations\02_nightly\opals\\"

    opalsIcon = QtGui.QIcon(r"C:\Users\lwiniwar\.qgis2\python\plugins\qpals\icon.png")
    cmdIcon = QtGui.QIcon(r"C:\Users\Lukas\.qgis2\python\plugins\qpals\cmd_icon.png")
    loadingIcon = QtGui.QIcon(r"C:\Users\Lukas\.qgis2\python\plugins\qpals\spinner_icon.png")

    def getModulesAvailiable(self):
        for opalsexe in glob.glob(self.opalsPath + "opals*.exe"):
            self.modulesAvailiable.append({'name': os.path.basename(opalsexe).split(".exe")[0],
                                           'icon': self.opalsIcon,
                                           'class': QpalsModuleBase(opalsexe)})
        self.modulesAvailiable.append({'name': "User-defined cmd", 'icon': self.cmdIcon, 'class': QpalsRunBatch()})


    def __init__(self, iface, *args):
        super(moduleSelector, self).__init__(*args)
        self.iface = iface
        self.curmodel=None
        self.modulesAvailiable = []

        self.getModulesAvailiable()
        self.initUi()
        self.resize(800,600)
        self.workerrunning = False


    def initUi(self):

        groupSelect = QtGui.QGroupBox()
        self.moduleList = QtGui.QListWidget()
        for moduleDict in self.modulesAvailiable:
            module = QpalsListWidgetItem(moduleDict)
            self.moduleList.addItem(module)
        self.moduleList.currentItemChanged.connect(self.loadModuleAsync)

        filterBox = QtGui.QHBoxLayout()
        filterBox.addWidget(QtGui.QLabel("Filter:"))
        self.filterText = QtGui.QLineEdit()
        self.filterText.textChanged.connect(self.filterModuleList)
        filterBox.addWidget(self.filterText, stretch=100)
        filterClear = QtGui.QPushButton()
        filterClear.setText("X")
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

        runvbox = QtGui.QVBoxLayout()
        runvbox.addWidget(self.runListWidget, stretch=1)
        rungroup.setLayout(runvbox)

        grpBoxContainer = QtGui.QHBoxLayout()
        grpBoxContainer.addWidget(groupSelect)
        grpBoxContainer.addWidget(self.moduleparamBox, stretch=1)
        grpBoxContainer.addWidget(rungroup)

        lowerhbox = QtGui.QHBoxLayout()
        exitBtn = QtGui.QPushButton("Exit")
        exitBtn.clicked.connect(self.close)
        lowerhbox.addStretch(1)
        lowerhbox.addWidget(exitBtn)

        overallBox = QtGui.QVBoxLayout()
        overallBox.addLayout(grpBoxContainer)
        overallBox.addLayout(lowerhbox)
        self.setLayout(overallBox)
        self.setWindowTitle('qpals')

    def filterModuleList(self, text):
        self.moduleList.clear()
        for moduleDict in self.modulesAvailiable:
            if text.lower() in moduleDict['name'].lower():
                module = QpalsListWidgetItem(moduleDict)
                self.moduleList.addItem(module)

    def startWorker(self, module):
        #https://snorfalorpagus.net/blog/2013/12/07/multithreading-in-qgis-python-plugins/
        if self.workerrunning:
            return
        self.workerrunning = True
        worker = ModuleWorker(module)
        messageBar = self.iface.messageBar().createMessage('Doing something time consuming...', )
        progressBar = QtGui.QProgressBar()
        progressBar.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        cancelButton = QtGui.QPushButton()
        cancelButton.setText('Cancel')
        cancelButton.clicked.connect(worker.kill)
        messageBar.layout().addWidget(progressBar)
        messageBar.layout().addWidget(cancelButton)
        self.iface.messageBar().pushWidget(messageBar, self.iface.messageBar().INFO)
        self.messageBar = messageBar

        # start the worker in a new thread
        thread = QtCore.QThread(self)
        worker.moveToThread(thread)
        worker.finished.connect(self.workerFinished)
        worker.error.connect(self.workerError)
        worker.progress.connect(progressBar.setValue)
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
        # remove widget from message bar
        self.iface.messageBar().popWidget(self.messageBar)
        if ret is not None:
            # report the result
            module, code = ret
            self.loadModule(module)
        else:
            # notify the user that something went wrong
            self.iface.messageBar().pushMessage('Something went wrong! See the message log for more information.', duration=3)
        self.workerrunning = False

    def workerError(self, e, exception_string):
        print('Worker thread raised an exception: {}\n'.format(exception_string))
        self.workerrunning = False

    def loadModuleAsync(self, module):
        if module.paramClass.loaded:
            self.loadModule(module)
        else:
            self.startWorker(module)

    def loadModule(self, module):
        if module:  # can happen if it gets filtered away
            form = QtGui.QVBoxLayout()
            self.moduleparamBox.setTitle("Parameters for " + module.text())
            module.setIcon(self.loadingIcon)
            parameterform = module.paramClass.getParamUi()
            module.setIcon(module.icon)
            form.addLayout(parameterform, stretch=1)
            # reset / run / add to list / add to view
            resetbar = QtGui.QHBoxLayout()
            resetbtn = QtGui.QPushButton("Reset")
            resetbtn.clicked.connect(lambda: self.resetModule(module))
            runbtn = QtGui.QPushButton("Run now")
            addbtn = QtGui.QPushButton("Add to run list >")
            addbtn.clicked.connect(self.addToRunList)
            viewbox = QtGui.QCheckBox("Add result to canvas")
            resetbar.addStretch(1)
            resetbar.addWidget(resetbtn)
            resetbar.addWidget(runbtn)
            resetbar.addWidget(addbtn)
            resetbar.addWidget(viewbox)
            form.addLayout(resetbar)
            self.curmodel = module
        else:
            form = QtGui.QHBoxLayout()
            l1 = QtGui.QLabel("No module selected...")
            form.addWidget(l1)
            self.moduleparamBox.setTitle("Module Parameters")

        print "clearing layout"
        self.clearLayout(self.moduleparamLayout)
        print "adding layout"
        print form
        self.moduleparamLayout.addLayout(form)
        print "layout added"

    def resetModule(self, module):
        module.paramClass.reset()
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

    def addToRunList(self):
        print self.curmodel
        self.runListWidget.addItem(self.curmodel)
        self.moduleList.removeItemWidget(self.curmodel)
        for module in self.modulesAvailiable:
            if module['name'] == self.curmodel.name:
                replacementModel = module
                break
        newModule = QpalsListWidgetItem(replacementModel)
        self.moduleList.addItem(newModule)
        self.loadModule(newModule)
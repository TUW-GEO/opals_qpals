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

class moduleSelector(QtGui.QDialog):

    def __init__(self):
        super(moduleSelector, self).__init__()
        self.initUi()

    def initUi(self):
        opalsIcon = QtGui.QIcon("icon.png")
        groupSelect = QtGui.QGroupBox()
        optionsList = QtGui.QListWidget()
        for moduleName in ["opalsAlgebra", "opalsAddInfo", "opalsInfo", "opalsHisto", "User-defined cmd"]:
            module = QtGui.QListWidgetItem(opalsIcon, moduleName)
            optionsList.addItem(module)

        filterBox = QtGui.QHBoxLayout()
        filterBox.addWidget(QtGui.QLabel("Filter:"))
        filterText = QtGui.QLineEdit()
        filterBox.addWidget(filterText, stretch=1)
        filterClear = QtGui.QPushButton()
        filterClear.setText("X")
        filterBox.addWidget(filterClear)

        groupSelect.setTitle("Module Selector")
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(optionsList, stretch=1)
        vbox.addLayout(filterBox)
        groupSelect.setLayout(vbox)

        moduleparam = QtGui.QGroupBox()
        moduleparam.setTitle("Module parameters")

        runlist = QtGui.QGroupBox()
        runlist.setTitle("Run list")

        grpBoxContainer = QtGui.QHBoxLayout()
        grpBoxContainer.addWidget(groupSelect)
        grpBoxContainer.addWidget(moduleparam)
        grpBoxContainer.addWidget(runlist)

        lowerhbox = QtGui.QHBoxLayout()
        exitBtn = QtGui.QPushButton("Exit")
        lowerhbox.addStretch(1)
        lowerhbox.addWidget(exitBtn)

        overallBox = QtGui.QVBoxLayout()
        overallBox.addLayout(grpBoxContainer)
        overallBox.addLayout(lowerhbox)
        self.setLayout(overallBox)
        self.setWindowTitle('qpals')

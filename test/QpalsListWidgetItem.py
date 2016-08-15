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
from QpalsModuleBase import QpalsModuleBase

class QpalsListWidgetItem(QtGui.QListWidgetItem):

    def __init__(self, defdict):
        self.name = defdict['name']
        self.icon = defdict['icon']
        self.paramClass = defdict['class']
        super(QpalsListWidgetItem, self).__init__(self.icon, self.name)

    def __deepcopy__(self, memo={}):
        import copy
        defdict = dict()
        defdict['name'] = self.name
        defdict['icon'] = self.icon
        defdict['class'] = QpalsModuleBase(self.paramClass.execName, self.paramClass.project, self.paramClass.layerlist)
        defdict['class'].params = copy.deepcopy(self.paramClass.params)
        defdict['class'].globals = copy.deepcopy(self.paramClass.globals)
        defdict['class'].common = copy.deepcopy(self.paramClass.common)
        defdict['class'].loaded = self.paramClass.loaded
        defdict['class'].visualize = self.paramClass.visualize
        dup = QpalsListWidgetItem(defdict=defdict)
        dup.paramClass.listitem = dup
        dup.setBackgroundColor(self.backgroundColor())
        dup.setToolTip(self.toolTip())
        return dup
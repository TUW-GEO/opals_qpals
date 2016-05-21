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

class QpalsListWidgetItem(QtGui.QListWidgetItem):

    def __init__(self, defdict):
        self.name = defdict['name']
        self.icon = defdict['icon']
        self.paramClass = defdict['class']
        super(QpalsListWidgetItem, self).__init__(self.icon, self.name)
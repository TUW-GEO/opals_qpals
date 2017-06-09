"""
/***************************************************************************
Name			 	 : qpalsLog
Description          : Managing Project settings for qpals
Date                 : 2017-06-09
copyright            : (C) 2017 by Lukas Winiwarter/TU Wien
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

from PyQt4 import QtCore, QtGui, QtWebKit

from qgis.core import *
from qgis.gui import *


from QpalsShowFile import QpalsShowFile
import QpalsDropTextbox


class QpalsLog:
    def __init__(self, iface=None, logpaths=[r"C:\Users\lwiniwar\AppData\Local\Temp\opalsLog.xml", r"D:\01_Opals\02_Installations\opalsLog.xml"]):
        self.iface = iface
        self.logpaths = logpaths
        self.ui = self.getUI()


    def getUI(self):
        self.ui = QtGui.QDialog()
        self.ui.resize(1200, 600)
        self.ui.setWindowTitle("Qpals Log")
        lo = QtGui.QFormLayout()
        vb = QtGui.QVBoxLayout()
        self.htmlwindow = QtWebKit.QWebView()
        #self.htmlwindow.setReadOnly(True)
        self.comLogSelect = QtGui.QComboBox()
        self.lblLogSelect = QtGui.QLabel("Select logfile:")
        lo.addRow(self.lblLogSelect, self.comLogSelect)
        vb.addLayout(lo,0)
        vb.addWidget(self.htmlwindow,1)
        self.ui.setLayout(vb)

        self.htmlwindow.setHtml('<h1 style="position:absolute;text-align:center;top:50%">Select a logfile from above</h1>')
        self.comLogSelect.currentIndexChanged.connect(self.comLogChanged)
        for logpath in self.logpaths:
            self.comLogSelect.addItem(logpath)
        return self.ui

    def comLogChanged(self):
        curitem = self.comLogSelect.currentText()
        url = QtCore.QUrl("file:///%s" % str(curitem))
        # from PyQt4 import QtXmlPatterns
        # url2 = QtCore.QUrl("file:///%s" % str(curitem))
        # query = QtXmlPatterns.QXmlQuery(QtXmlPatterns.QXmlQuery.XSLT20)
        # query.setFocus(url2)
        # query.setQuery(url)
        # html = query.evaluateToString()
        # print query, html
        # print "Using %s as focus and %s as query" % (url2, url)
        # self.htmlwindow.setHtml(html)

        self.htmlwindow.load(url)
        #print self.htmlwindow.settings().testAttribute(QtWebKit.QWebSettings.JavascriptEnabled)
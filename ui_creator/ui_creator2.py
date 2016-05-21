# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from opalsParam import opalsParam
import glob, os
from time import strftime

class ui_creator(object):
    def __init__(self, args):
        self.infile = args[0]
        self.outfile = args[1]
        self.moduleName = ""
        self.paramList = []

    def run(self):
        soup = BeautifulSoup(open(self.infile), 'html.parser')
        div = soup.find_all('div', 'title')[0]  # First div with class="title"
        self.moduleName = div.string.split("Module ")[1]
        tab = soup.find_all('table', 'params')[0]
        for row in tab.find_all('tr'):
            tds = row.find_all('td')
            name = tds[0].string
            attr = ''.join(tds[1].strings) # since there are tags inside
            attrdet = attr.split('\n')
            typedef = remarks = desc = extradesc = ""
            for det in attrdet:
                if det.find('Type:') > 0:
                    typedef = det[(det.find('Type:')+5):]
                elif det.find('Remarks:') >0:
                    remarks = det[(det.find('Remarks:')+8):]
                elif det.find('Description:') >0:
                    desc = det[(det.find('Description:')+12):]
                else:
                    extradesc = det
            param = opalsParam(name, typedef, remarks, desc, extradesc)
            self.paramList.append(param)


    def __repr__(self):
        str = "opals User Interface creator object\n"
        str += "\tModule Name: %s\n"%self.moduleName
        str += "\tInput file: %s\n" % self.infile
        for param in self.paramList:
            str += param.__repr__() + '\n'
        return str

    def getAsQt(self):
        outtext = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Dialog</class>
 <widget class="QDialog" name="Dialog">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>400</width>
    <height>%s</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>qpals %s</string>
  </property>
  <widget class="QDialogButtonBox" name="buttonBox">
   <property name="geometry">
    <rect>
     <x>50</x>
     <y>%s</y>
     <width>341</width>
     <height>32</height>
    </rect>
   </property>
   <property name="orientation">
    <enum>Qt::Horizontal</enum>
   </property>
   <property name="standardButtons">
    <set>QDialogButtonBox::Cancel|QDialogButtonBox::Ok</set>
   </property>
  </widget>"""%(len(self.paramList)*25+80,self.moduleName, len(self.paramList)*25+40)
        paramCount = 0
        for param in self.paramList:
            widget = param.getAsWidget(label_id=paramCount, field_name="txt"+param.name[1:], y_pos=10+paramCount*25)
            outtext += "\n" + widget
            paramCount += 1
        outtext += "\n </widget></ui>"
        return outtext

    def writePyFile(self, className, outPath, outName):
        setupUi = """
# -*- coding: utf-8 -*-
\"\"\"
/***************************************************************************
Name			 	 : %(module_name)s
Description          : UI code an opals module
Date                 : %(today)s
copyright            : (C) 2015-16 by Lukas Winiwarter/TU Wien
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
\"\"\"
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
import os

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_%(module_name)s(object):
    def __init__(self):
        self.lastpath = os.getenv('HOME')

    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(400, %(dialog_height)s)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(50, %(box_y)s, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
"""%{   'today':         strftime("%Y-%m-%d"),
        'module_name':   "Module"+self.moduleName,
        'dialog_height': len(self.paramList)*25+80,
        'box_y':         len(self.paramList)*25+40
        }

        retranslateUi = """
        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "qpals %(module_name)s", None))
        """%{'module_name': self.moduleName}

        getVals = """
    def getValues(self):
        return { """

        setVals = """
    def setValues(self, valdict):"""

        buttonDef = ""
        paramCount = 0
        for param in self.paramList:
            [setupUiString, retranslateUiString, buttonDefString, getValsString, setValsString] = param.getPythonCode(label_id=paramCount,
                                                                                      field_name=param.name[1:],
                                                                                      y_pos=10+paramCount*25)
            setupUi += "\n" + setupUiString
            retranslateUi += "\n" + retranslateUiString
            buttonDef += "\n" + buttonDefString
            getVals += "\n" + getValsString + ","
            setVals  += "\n" + setValsString

            paramCount += 1

        getVals = getVals[:-1] + " }" # Get rid of trailing ",", add }
        outtext = setupUi + "\n" + retranslateUi + "\n" + buttonDef + "\n" + getVals + "\n" + setVals
        with open(outPath + outName+".py", 'w') as f:
            f.write(outtext)

    def writeShellModule(self, className, outPath, outName):
        code = """\"\"\"
/***************************************************************************
Name			 	 : %(module_name)s
Description          : shell access class for an opals module
Date                 : %(today)s
copyright            : (C) 2015 by Lukas Winiwarter/TU Wien
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
 \"\"\"
import subprocess
import os
from bs4 import BeautifulSoup
from .. import Module, Parameter


class %(name)s(Module.Module):
    def __init__(self, execpath=None, cwd=None, logpath=None):
        self.executable = execpath if execpath else r"C:\Program Files (x86)\opals\opals\Opals%(name)s"
        self.cwd = cwd if cwd else r"C:\Users\Lukas\.qgis2\python\plugins\qpals\log"
        self.logpath = logpath if logpath else r"C:\Users\Lukas\.qgis2\python\plugins\qpals\log\opalsLog.xml"
        self.params = {%(allinit)s}
"""% {'allinit': ','.join([param.getInitClause() for param in self.paramList]),
        'name': className.split("Module")[1],
      'today':         strftime("%Y-%m-%d"),
        'module_name':   "Module"+self.moduleName}

        for param in self.paramList:
            getter_setter = param.getGetterSetter()
            code += getter_setter

        code += """
"""
        with open(outPath + outName+".py", 'w') as f:
            f.write(code)
            
    def writeWrapperClass(self, className, outPath, outName):
        text = """\"\"\"
/***************************************************************************
Name			 	 : %(module_name)s
Description          : UI wrapper class for an opals module
Date                 : %(today)s
copyright            : (C) 2015 by Lukas Winiwarter/TU Wien
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
 \"\"\"

from PyQt4 import QtCore, QtGui
from %(className)s import %(className)s
import %(opalsName)s


# create the dialog for qpals
class %(outName)s(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = %(className)s ()
        self.ui.setupUi(self)

    def getValues(self):
         return self.ui.getValues()

    def getModule(self):
        instance = %(opalsName)s.%(opalsName)s()
        instance.set_params(self.getValues())
        return instance
    """%{
            'className': className,
            'opalsName': className.split("Module")[1],
            'outName': outName,
            'today':         strftime("%Y-%m-%d"),
        'module_name':   "Module"+self.moduleName
        }
        with open(outPath + outName+".py", 'w') as f:
            f.write(text)

    def writeMenuEntryCode(self, className, outPath, outName):
        importCode = "from modules.%(modName)s.Module%(modName)s import Module%(modName)s"%{'modName' : className.split("Module")[1]}

        menuItemCode = """
    self.menuItem%(modName)s = QAction(QIcon(":/plugins/qpals/icon.png"), "opals%(modName)s...", self.iface.mainWindow())
    self.menuItem%(modName)s.setObjectName("menu%(modName)s")
    self.menuItem%(modName)s.setWhatsThis("%(modName)s")
    self.menuItem%(modName)s.setStatusTip("opals%(modName)s")
    QObject.connect(self.menuItem%(modName)s, SIGNAL("triggered()"), self.loadDialog%(modName)s)
    self.menu.addAction(self.menuItem%(modName)s)"""%{'modName' : className.split("Module")[1]}

        loadDialogCode = """
  def loadDialog%(modName)s(self):
    dlg = Module%(modName)s()
    dlg.show()
    result = dlg.exec_()
    if result == 1:
      %(modName)sInst = dlg.getModule()
      try:
        %(modName)sInst.run()
        self.iface.messageBar().pushMessage("opals %(modName)s ended", level=QgsMessageBar.SUCCESS)
      except:
        self.iface.messageBar().pushMessage("opals %(modName)s failed", level=QgsMessageBar.CRITICAL)
        """%{'modName' : className.split("Module")[1]}

        with open(outPath + outName+"_imp.py", 'a') as f:
            f.write(importCode + '\n')
        with open(outPath + outName+"_menuItem.py", 'a') as f:
            f.write('\n# ------- next module -------\n')
            f.write(menuItemCode)
        with open(outPath + outName+"_loadDialog.py", 'a') as f:
            f.write('\n# ------- next module -------\n')
            f.write(loadDialogCode)

if __name__ == "__main__":
    modules = []
    for file in glob.glob(r'C:\Program Files (x86)\opals\doc\html\Module*.html'):
        print "Processing ", file
        if file in [r'C:\Program Files (x86)\opals\doc\html\ModuleDeleter_8hpp_source.html',
                    r'C:\Program Files (x86)\opals\doc\html\ModuleExecutables_8hpp_source.html']:
            continue # gehoert nicht zu den "normalen" modulen - wuerde Fehler werfen
        args = [file,
                r'C:\Users\Lukas\.qgis2\python\plugins\qpals\modules\%s\\'%file.split('.html')[0].split('Module')[1]] #sys.argv
        if not os.path.exists(args[1]):
            os.makedirs(args[1])
        open(args[1]+'\__init__.py', 'a').close()

        name = args[0].split('\\')[-1].replace('.html', '')
        outUI = args[1] + name + '.ui'
        outPyQt = args[1] + 'Ui_' + name + '.py'
        outPyPath = args[1]
        ui_creator_inst = ui_creator(args = args)
        ui_creator_inst.run()
        print ui_creator_inst
        modules.append(ui_creator_inst.moduleName)
        #continue
        with open(outUI, 'w') as f:
            f.write(ui_creator_inst.getAsQt())
        ui_creator_inst.writePyFile(className=name, outPath=outPyPath, outName='Ui_'+name)
        print "Writing Ui pyFile to %s"%('Ui_'+name)
        ui_creator_inst.writeWrapperClass(className='Ui_' + name, outPath=outPyPath, outName=name)
        print "Writing wrapper class to %s"%(name)
        ui_creator_inst.writeShellModule(className=name, outPath=outPyPath, outName=name.split("Module")[1])
        print "Writing shell module to %s"%(name.split("Module")[1])
        # delete files before uncommenting
        #ui_creator_inst.writeMenuEntryCode(className=name,
        #                                   outPath="C:\Users\Lukas\.qgis2\python\plugins\qpals\\",
        #                                   outName="menuentries")

    #
    with open(r'C:\Users\Lukas\.qgis2\python\plugins\qpals\modules\__init__.py', 'w') as f:
        for module in modules:
            f.write("\nimport %(name)s.%(name)s"%{'name':module.strip()})
        f.write("\nmoddict = {")
        for module in modules[:-1]:
            f.write("\n'%(name)s': %(name)s.%(name)s.%(name)s(),"%{'name': module.strip()})
        # last one closing bracket
        f.write("\n'%(name)s': %(name)s.%(name)s.%(name)s()}"%{'name': modules[-1].strip()})
        f.write("""
def getFromName(Name):
    return moddict[Name]""")
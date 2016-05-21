# -*- coding: utf-8 -*-

def opals2qt(opalsType):
    trans = {#Module Bounds
             "opals::Path":             "QLineEdit+Path",
             "opals::String":           "QLineEdit",
             "double":                  "QLineEdit",
             "unsigned int":            "QSpinBox",
             "opals::GridLimit":        "QLineEdit",
             "opals::ResamplingMethod": "QLineEdit",
             "opals::BoundaryType":     ["QComboBox", ["ConvexHull",
                                                       "MinimumRectangle",
                                                       "AlphaShape"]],
            #Module Import
             "opals::TrafPars3dAffine": "QLineEdit",
             "bool":                    "QCheckBox",
             "int":                     "QSpinBox",
             "opals::BeamInfo":         ["QComboBox", ["BeamVector",
                                                       "BeamVectorSCS",
                                                       "Range",
                                                       "ScanAngle"]],
            #Module Info
             "opals::DataSetStats":     "QLabel" #disabled
             }
    qtname = trans[opalsType] if opalsType in trans else "QLineEdit"
    return qtname

# opals data types
class opalsDT:
    String = ['String']
    Path = ['Path']
    GridLimit = ['double', 'double', 'double', 'double']
    Double = ['double']
    ResamplingMethod = ['choice', ['weightedAverage', 'simpleAverage', 'nearesNeighbour', 'bilinear', 'bicubic']]
    dic = {
        'opals::Path'  : Path,
        'opals::String': String,
        'opals::GridLimit': GridLimit,
        'double': Double,
        'opals::ResamplingMethod': ResamplingMethod
    }

def parseType(type):
    if type.find('opals::Array') > 0:
        arr = (type.split('<')[1][0:-1]).split(',')
        type = ",".join([arr[0] for i in range (int(arr[1]))])
    if type.find('opals::Vector') > 0:
        vec = type.split('<')[1][0:-1]
        type = vec
    return opals2qt(type.strip())

class opalsParam(object):

    def __init__(self, name, typedef, remarks, desc, extradesc):
        self.name = name
        self.typedef = typedef
        self.remarks = remarks
        self.desc = desc
        self.extradesc = extradesc
        self.qtType = parseType(typedef)

    def __repr__(self, doExtraDef = False, doQtType = True):
        type = self.qtType if doQtType else self.typedef
        if not doExtraDef:
            return "%s\n\tType: %s\n\tRemarks: %s\n\tDescription: %s"%(self.name,
                                                                   type,
                                                                   self.remarks,
                                                                   self.desc)
        else:
            return "%s\n\tType: %s\n\tRemarks: %s\n\tDescription: %s"%(self.name,
                                                                   type,
                                                                   self.remarks,
                                                                   (self.desc+"\n"+self.extradesc))

    def getAsWidget(self, label_id, field_name, y_pos, x_label=10, x_field=190):
        style = ""
        widget = ""
        text = """
  <widget class="QLabel" name="label_%s">
   <property name="geometry">
    <rect>
     <x>%d</x>
     <y>%d</y>
     <width>181</width>
     <height>16</height>
    </rect>
   </property>
    <property name="toolTip">
    <string>%s</string>
   </property>
   <property name="text">
    <string>%s:</string>
   </property>
  </widget>"""%(label_id, x_label, y_pos, self.desc, self.name)



        if self.remarks.strip() == "mandatory":
            style = """<property name="styleSheet">
    <string notr="true">background-color: rgb(255, 255, 127);</string>
   </property>"""

        if self.qtType == "QLineEdit":
            widget = """
  <widget class="QLineEdit" name="%s">
   <property name="geometry">
    <rect>
     <x>%d</x>
     <y>%d</y>
     <width>191</width>
     <height>20</height>
    </rect>
   </property>
   %s
  </widget>
"""%(field_name, x_field, y_pos, style)

        elif self.qtType == "QLineEdit+Path":
            widget = """
  <widget class="QLineEdit" name="%s">
   <property name="geometry">
    <rect>
     <x>%d</x>
     <y>%d</y>
     <width>191</width>
     <height>20</height>
    </rect>
   </property>
   %s
  </widget>
  <widget class="QPushButton" name="browse_%s">
   <property name="geometry">
    <rect>
     <x>%s</x>
     <y>%s</y>
     <width>20</width>
     <height>19</height>
    </rect>
   </property>
   <property name="toolTip">
    <string>open file browser</string>
   </property>
   <property name="text">
    <string>...</string>
   </property>
  </widget>
"""%(field_name, x_field, y_pos, style, field_name, (x_field+170), y_pos)


        elif "QComboBox" in self.qtType:
            widget = """
  <widget class="QComboBox" name="comboBox">
   <property name="geometry">
    <rect>
     <x>%s</x>
     <y>%s</y>
     <width>191</width>
     <height>22</height>
    </rect>
   </property>
   <property name="editable">
    <bool>false</bool>
   </property>
   <property name="currentIndex">
    <number>0</number>
   </property>"""%(x_field, y_pos)

        elif "QCheckBox" in self.qtType:
            widget = """
            <widget class="QCheckBox" name="checkBox">
   <property name="geometry">
    <rect>
     <x>%s</x>
     <y>%s</y>
     <width>70</width>
     <height>17</height>
    </rect>
   </property>
   <property name="text">
    <string>True</string>
   </property>
   <property name="iconSize">
    <size>
     <width>16</width>
     <height>16</height>
    </size>
   </property>
  </widget>
            """%(x_field, y_pos)
            for line in self.qtType[1]:
                widget += """
   <item>
    <property name="text">
     <string>%s</string>
    </property>
   </item>"""%line
            widget += "</widget>"
        elif self.qtType == "QSpinBox":
            widget = """
            <widget class="QSpinBox" name="spinBox">
   <property name="geometry">
    <rect>
     <x>%s</x>
     <y>%s</y>
     <width>191</width>
     <height>21</height>
    </rect>
   </property>
   <property name="suffix">
    <string/>
   </property>
   <property name="maximum">
    <number>999999999</number>
   </property>
  </widget>
            """%(x_field, y_pos)

        return text + widget

    def getPythonCode(self, label_id, field_name, y_pos, x_label=10, x_field=190):
        getValsString = ""
        setValsString = ""
        setupUiString = """
        self.label_%(label_id)s = QtGui.QLabel(Dialog)
        self.label_%(label_id)s.setGeometry(QtCore.QRect(%(x_pos)s, %(y_pos)s, 100, 10))
        self.label_%(label_id)s.setObjectName(_fromUtf8("lblId%(label_id)s"))\n"""%{
            'label_id': label_id,
            'x_pos':    x_label,
            'y_pos':    y_pos
            }
        retranslateUiString = """
        self.label_%(label_id)s.setToolTip(_translate("Dialog", "%(desc)s", None))
        self.label_%(label_id)s.setText(_translate("Dialog", "%(name)s", None))\n"""%{
            'label_id': label_id,
            'desc':     self.desc,
            'name':     self.name
        }
        buttonDefString = ""

        if self.qtType == "QLineEdit":
            setupUiString += """
        self.%(field_name)s = QtGui.QLineEdit(Dialog)
        self.%(field_name)s.setGeometry(QtCore.QRect(%(x_pos)s, %(y_pos)s, 190, 20))
        self.%(field_name)s.setObjectName(_fromUtf8("%(field_name)s"))\n"""%{
                'field_name':   field_name,
                'x_pos':        x_field,
                'y_pos':        y_pos
            }
            retranslateUiString += ""
            getValsString += "        '%(name)s': self.%(field_name)s.text()"%{
                'name': self.name[1:],
                'field_name': field_name
            }
            setValsString += "        self.%(field_name)s.setText(valdict['%(name)s'])"%{
                'name': self.name[1:],
                'field_name': field_name
            }

        elif self.qtType == "QLineEdit+Path":
            setupUiString += """
        self.%(field_name)s = QtGui.QLineEdit(Dialog)
        self.%(field_name)s.setGeometry(QtCore.QRect(%(x_pos)s, %(y_pos)s, 170, 20))
        self.%(field_name)s.setObjectName(_fromUtf8("%(field_name)s"))

        self.com%(field_name)s = QtGui.QPushButton(Dialog)
        self.com%(field_name)s.setGeometry(QtCore.QRect(%(x_posB)s, %(y_pos)s, 20, 20))
        self.com%(field_name)s.setObjectName(_fromUtf8("com%(field_name)s"))\n"""%{
                'field_name':   field_name,
                'x_pos':        x_field,
                'x_posB':       x_field+170,
                'y_pos':        y_pos
            }
            retranslateUiString += """
        self.com%(field_name)s.setToolTip(_translate("Dialog", "open file browser", None))
        self.com%(field_name)s.setText(_translate("Dialog", "...", None))
        self.com%(field_name)s.clicked.connect(self.com%(field_name)s_clicked)\n"""%{
                'field_name':   field_name,
            }
            buttonDefString += """
    def com%(field_name)s_clicked(self):
        filename= QtGui.QFileDialog.getOpenFileNames(None, 'File for %(field_name)s', self.lastpath) # 0x4 for no confirmation on overwrite
        if filename:
            self.lastpath = os.path.dirname(filename[0])
        self.%(field_name)s.setText(_fromUtf8(", ".join(filename)))\n"""%{
                'field_name':field_name}
            getValsString += "        '%(name)s': self.%(field_name)s.text()"%{
                'name': self.name[1:],
                'field_name': field_name
            }
            setValsString += "        self.%(field_name)s.setText(valdict['%(name)s'])"%{
                'name': self.name[1:],
                'field_name': field_name
            }

        elif self.qtType == "QCheckBox":
            setupUiString += """
        self.%(field_name)s = QtGui.QCheckBox(Dialog)
        self.%(field_name)s.setGeometry(QtCore.QRect(%(x_pos)s, %(y_pos)s, 190, 16))
        self.%(field_name)s.setIconSize(QtCore.QSize(16, 16))
        self.%(field_name)s.setObjectName(_fromUtf8("checkBox"))\n"""%{
                'field_name': field_name,
                'x_pos':        x_field,
                'y_pos':        y_pos
            }
            retranslateUiString += """
        self.%(field_name)s.setText(_translate("Dialog", "True", None))\n"""%{
                'field_name': field_name}
            getValsString += "        '%(name)s': 1 if self.%(field_name)s.isChecked() else 0"%{
                'name': self.name[1:],
                'field_name': field_name
            }
            setValsString += "        self.%(field_name)s.setChecked(valdict['%(name)s'])"%{
                'name': self.name[1:],
                'field_name': field_name
            }

        elif self.qtType == "QSpinBox":
            setupUiString += """
        self.%(field_name)s = QtGui.QSpinBox(Dialog)
        self.%(field_name)s.setGeometry(QtCore.QRect(%(x_pos)s, %(y_pos)s, 190, 20))
        self.%(field_name)s.setSuffix(_fromUtf8(""))
        self.%(field_name)s.setMaximum(1000000000)
        #self.%(field_name)s.setProperty("value", 1)\n"""%{
                'field_name': field_name,
                'x_pos':        x_field,
                'y_pos':        y_pos}
            retranslateUiString += """

            """%{}
            getValsString += "        '%(name)s': self.%(field_name)s.value()"%{
                'name': self.name[1:],
                'field_name': field_name
            }
            setValsString += "        self.%(field_name)s.setValue(valdict['%(name)s'])"%{
                'name': self.name[1:],
                'field_name': field_name
            }

        elif "QComboBox" in self.qtType:
            setupUiString += """
        self.%(field_name)s = QtGui.QComboBox(Dialog)
        self.%(field_name)s.setGeometry(QtCore.QRect(%(x_pos)s, %(y_pos)s, 190, 20))
        self.%(field_name)s.setEditable(False)
        self.%(field_name)s.setObjectName(_fromUtf8("%(field_name)s"))\n"""%{
                'field_name': field_name,
                'x_pos':        x_field,
                'y_pos':        y_pos}

            count = 0
            for line in self.qtType[1]:
                setupUiString += "        self.%(field_name)s.addItem(_fromUtf8(\"\"))\n"%{'field_name': field_name}
                retranslateUiString += """
        self.%(field_name)s.setItemText(%(count)s, _translate("Dialog", "%(item_name)s", None))\n"""%{
                    'field_name':   field_name,
                    'item_name':    line,
                    'count':        count
                }
                count += 1
            retranslateUiString += """
        self.%(field_name)s.setCurrentIndex(0)\n"""%{'field_name': field_name}
            getValsString += "        '%(name)s': self.%(field_name)s.currentText()"%{
                'name': self.name[1:],
                'field_name': field_name
            }
            setValsString += """        idx = self.%(field_name)s.findText(valdict['%(name)s'], QtCore.Qt.MatchFixedString)
        if idx >=0: self.%(field_name)s.setCurrentIndex(idx)"""%{
                'name': self.name[1:],
                'field_name': field_name
            }

        if self.remarks.strip() == "mandatory":
            setupUiString += "        self.%(field_name)s.setStyleSheet(" \
                             "_fromUtf8(\"background-color: rgb(255, 255, 127);\"))\n"%{'field_name':field_name}
        if self.remarks.strip() == "estimable":
            setupUiString += "        self.%(field_name)s.setStyleSheet(" \
                             "_fromUtf8(\"background-color: rgb(150, 169, 243);\"))\n"%{'field_name':field_name}
        if self.remarks.strip() == "optional":
            setupUiString += "        self.%(field_name)s.setStyleSheet(" \
                             "_fromUtf8(\"background-color: rgb(156, 239, 154);\"))\n"%{'field_name':field_name}
        if "default" in self.remarks.strip():
            setupUiString += "        self.%(field_name)s.setStyleSheet(" \
                             "_fromUtf8(\"background-color: rgb(227, 224, 166);\"))\n"%{'field_name':field_name}



        return [setupUiString, retranslateUiString, buttonDefString, getValsString, setValsString]

    def getGetterSetter(self):
        getter = """
    def get_%(name)s(self):
        return self.params['%(name)s'].value\n"""%{'name': self.name[1:]} #get rid of - (-inFile)
        setter = """
    def set_%(name)s(self, val):
        self.params['%(name)s'].value = val\n"""%{'name': self.name[1:]} #get rid of - (-inFile)
        return getter+setter

    def getInitClause(self):
        return """
    '%(name)s': Parameter.Parameter()"""%{'name': self.name[1:]}
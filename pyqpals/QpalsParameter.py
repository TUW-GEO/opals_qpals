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

from builtins import range
from builtins import object
class QpalsParameter(object):

    changed = False
    use4proj = None
    field = None
    browse = None
    icon = None
    changedIcon = None

    def __init__(self, name, val, choices, type, opt, desc, longdesc, flag_mode=False):
        self.name = name
        self.choices = choices
        self.type = type
        self.val = val
        if longdesc and "estimation" in longdesc.lower():
            self.opt = "estimable"
        else:
            self.opt = opt
        self.desc = desc
        self.longdesc = longdesc
        self.flag_mode = flag_mode

    def __str__(self):
        return self.name + ": " + self.val

    def __deepcopy__(self, memodict={}):
        par = QpalsParameter(self.name, self.val, self.choices, self.type,
                             self.opt, self.desc, self.longdesc, self.flag_mode)
        return par

def mergeParamLists(baselist, overloadlist):
    for i in range(len(baselist)):
        baseitem = baselist[i]
        for overloaditem in overloadlist:
            if baseitem.name.lower() == overloaditem.name.lower():
                baselist[i].val = overloaditem.val
                break
    return baselist
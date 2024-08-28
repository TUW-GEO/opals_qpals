"""
/***************************************************************************
Name			 	 : get_attribute_types
Description          : Script to write existing pyDM attribute types to file
Date                 : 2017-08-08
copyright            : (C) 2017 by Lukas Winiwarter/TU Wien
email                : lukas.winiwarter@tuwien.ac.at
 ***************************************************************************/

/***************************************************************************
 *             WARNING  - THIS FILE IS NOT LICENSED UNDER THE GPL          *
 *            ====================================================         *
 *    Since the opals python interface is proprietary, it is not possible  *
 *    to get the availiable data types from the pyDM in qpals directly.    *
 *    This script will be called as an EXTERNAL PROCESS and write the file *
 *    "attribute_types.py" (licensed under the GPL).                       *
 *    License of "get_attribute_types.py": MIT License (see below).        *
 ***************************************************************************/
 

The MIT License (MIT)

Copyright (c) 2017 Lukas Winiwarter/TU Wien

Permission is hereby granted, free of charge, to any person obtaining a copy of this software* and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies 
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


* "this software" refers to the file "get_attribute_types.py" in this context.
"""

from builtins import str
import pyDM
import sys
import datetime
attrs = sorted([(str(name), pyDM.AddInfoLayout.getColumnType(str(name)))
                for name in pyDM.ColumnSemantic.names], key=lambda x: x[0])

# currently, no link exists between pyDM Data types and strings that may be used on the command line, so...
odm_data_types = {
    pyDM.ColumnType.int32  : "int32",
    pyDM.ColumnType.uint32 : "uint32",
    pyDM.ColumnType.int8   : "int8",
    pyDM.ColumnType.uint8  : "uint8",
    pyDM.ColumnType.int16  : "int16",
    pyDM.ColumnType.uint16 : "uint16",
    pyDM.ColumnType.float_ : "float",
    pyDM.ColumnType.double_: "double",
    pyDM.ColumnType.string : "string",
    pyDM.ColumnType.int64  : "int64",
    pyDM.ColumnType.cstr   : "cstr",
    pyDM.ColumnType.bool_  : "bool"
}

with open(sys.argv[1], 'w') as f:
    f.write("""\"\"\"
Automatically generated file from \n%s \non %s 
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
\"\"\" \n""" % (__file__.replace("\\", "/"),datetime.datetime.now().strftime("%Y-%m-%d")))
    f.write("odm_predef_attributes = {\n")
    for (attr, type) in attrs:
        if attr != "null":
            f.write("    '%s': '%s',\n" % (attr, odm_data_types[type]))
    f.write("}\nodm_data_types = [\n")
    for type in list(odm_data_types.values()):
        f.write("    '%s',\n" % type)
    f.write("]\n")

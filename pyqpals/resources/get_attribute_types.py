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
import sys
import datetime
import os


try:
    from opals import pyDM
except:
    # append opals-distro path in case pyDM import failed
    opals_distro_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'distro'))
    sys.path.append(opals_distro_folder)
    #now try to reimport
    from opals import pyDM


# currently, no link exists between pyDM Data types and strings that may be used on the command line, so...

attrs = sorted([(str(name), pyDM.AddInfoLayout.getColumnType(str(name)))
                for name in pyDM.ColumnSemantic.names], key=lambda x: x[0])

odm_data_types = {v : k.replace("_","") for k,v in pyDM.ColumnType.names.items()}

# construct file content
content_new = """\"\"\"
Automatically generated file by %s at %s 
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
\"\"\" \n""" % (os.path.split(__file__)[1], datetime.datetime.now().strftime("%Y-%m-%d"))
content_new += "odm_predef_attributes = {\n"
for (attr, type) in attrs:
    if attr != "null":
        content_new += "    '%s': '%s',\n" % (attr, odm_data_types[type])
content_new += "}\nodm_data_types = [\n"
for type in list(odm_data_types.values()):
    content_new += "    '%s',\n" % type
content_new += "]\n"

write_file = True
if os.path.exists(sys.argv[1]):
    with open(sys.argv[1]) as f:
        content_old = f.read()

    if content_old == content_new:
        print(f"{sys.argv[1]} is update to date")
        write_file = False

if write_file:
    print(f"Writing {sys.argv[1]}...", end="")
    with open(sys.argv[1], 'w') as f:
        f.write(content_new)
    print("done")

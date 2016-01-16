# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from StringIO import StringIO

import ui_creator._old.parameter


class ui_creator(object):
    def __init__(self, args):
        self.infile = args[0]
        self.outfile = args[1]
        self.paramList = []

    def run(self):
        #try:
            # This is neccessary due to the HTML containing Javascript.
        with open(self.infile, 'r') as content_file:
            content = content_file.read()
        headstart = content.find('<head>')
        headend = content.find('</head>')+7 # length of "<\head>"
        content = """<?xml version="1.1" ?>
<!DOCTYPE naughtyxml [
    <!ENTITY nbsp "&#0160;">
    <!ENTITY copy "&#0169;">
]> <html> """ +\
            content[166:headstart] + content[headend:]
        #print content
        content = StringIO(content)

        xml = ET.parse(content).getroot()
        # except SyntaxError:
        #     print "File %s could not be found or opened (Error 1). Exiting."%(self.infile)
        #     sys.exit(1)
        for tab in xml.iter('table'):
            if tab.get('class') == "params":
                for tr in tab.iter('tr'):
                    for td in tr.iter('td'):
                        print td.text
                    paramName = tr[0].text
                    paramOpts = tr[1][0].text
                    print tr[0].text, tr[1][0].text
                    paramDetails = []
                    for opt in paramOpts.split('<br/>'):
                        detailText = opt.split(": ")
                        paramDetails.append(detailText[1])
                    param = ui_creator.parameter.Parameter(paramName, paramDetails[0], paramDetails[1], paramDetails[2])
                    self.paramList.append(param)

    def __repr__(self):
        str = "opals User Interface creator object\n"
        str += "\tInput file: %s\n" % self.infile
        for param in self.paramList:
            str += param
        return str

if __name__ == "__main__":
    args = [r'C:\Program Files (x86)\opals\doc\html\ModuleDiff.html', r'C:\Users\Lukas\Documents\TU Wien\BacArbeit\01_Code\out_ui.ui'] #sys.argv
    ui_creator_inst = ui_creator(args = args)
    ui_creator_inst.run()
    print ui_creator_inst

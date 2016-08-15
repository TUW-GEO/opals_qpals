
from QpalsShowFile import QpalsShowFile


class QpalsProject:
    def __init__(self, tempdir, name, opalspath, vismethod=QpalsShowFile.METHOD_BOX, iface=None):
        self.tempdir = tempdir
        self.name = name
        self.opalspath = opalspath
        self.vismethod = vismethod
        self.iface = iface
        self.commons = dict()
        self.globals = dict()

    def getUI(self):
        pass

from QpalsShowFile import QpalsShowFile


class QpalsProject:
    def __init__(self, tempdir, name, opalspath, workdir, vismethod=QpalsShowFile.METHOD_BOX, iface=None):
        self.tempdir = tempdir
        self.workdir = workdir
        self.name = name
        self.opalspath = opalspath
        self.vismethod = vismethod
        self.iface = iface
        self.common = dict()
        self.globals = dict()


    def getUI(self):
        pass

    def globals_common(self):
        x = self.common.copy()
        x.update(self.globals)
        return x

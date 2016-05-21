import subprocess
from bs4 import BeautifulSoup
from qgis.core import *
from qgis.gui import *

class Module:
    def __init__(self):
        self.params = {}
        self.executable = ""
        self.logpath = ""
        self.cwd = ""

    def set_params(self, valdict):
        for key in valdict.iterkeys():
            self.params[key].value = valdict[key]

    def run(self):
        args = [self.executable]
        for key in self.params.iterkeys():
            val = self.params[key].get_value()
            if val:
                args.append("-" + str(key))
                args.append(str(val))
        args.append("-logFile")
        args.append(self.logpath)
        QgsMessageLog.logMessage(' '.join(args), 'qpals')
        return subprocess.Popen(args=args, cwd=self.cwd)

    def validate(self):
        return True

    def load_defaults(self):
        args = [self.executable, "-options"]
        ps = subprocess.Popen(args=args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = ps.communicate()
        if ps.returncode != 0:
            raise Exception('Call failed: %s' % stdout)
        soup = BeautifulSoup(stderr, 'html.parser')
        specifics = soup.find('Specific')
        for param in specifics.find_all('Parameter'):
            param_name = param["Name"]
            param_type = param["Type"]
            param_source = param["Src"]
            param_opt = param["Opt"]
            param_desc = param["Desc"]
            param_longdesc = param["LongDesc"]
            param_val = []
            for val in param.find_all('Val'):
                param_val.append(val.string)
            if param_val:  # empty if no information (not estimable, not set)
                self.params[param_name].value = param_val

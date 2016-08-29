from bs4 import BeautifulSoup
import re

class parse_log(object):

    def __init__(self, filename):
        self.filename = filename
        self.params = {}
        self.output = {}

    def run(self):
        soup = BeautifulSoup(open(self.filename), "html.parser")
        call1 = soup.find_all('module')[-1]  # Last Module call in file
        moduleName = call1.find('name')
        params = call1.find('parameters')
        for param in params.find_all('parameter'):
            attrs = param.attrs
            if attrs['value'] in ["<unspecified>", "", None]:
                attrs['value'] = "**"
            print "-%15s : %60s (%s)" % (attrs['name'], attrs['value'].strip(), attrs['src'])
            self.params[attrs['name']] = attrs['value'].strip()
        # data set statistics (import, info)
        ds = call1.find(text=re.compile(r'Data set statistic')).parent.parent.parent
        for info in ds.find_all('tr')[1:]:
            subinfo = info.find_all('td')
            name = subinfo[0].text
            if name == "Index statistics": break
            value = subinfo[1].text
            self.output[name] = value
            print "%15s:%29s" %(name,value)



if __name__ == '__main__':
    parse_log_inst = parse_log(r'C:\Users\Lukas\Documents\TU Wien\BacArbeit\opalsLog.xml')
    parse_log_inst.run()
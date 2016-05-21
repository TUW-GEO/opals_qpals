
class Parameter:
    def __init__(self, value=None,
                 source='default',
                 opt='estimable',
                 desc=None,
                 longdesc=None,
                 type=None):
        self.value = value
        self.source = source # Can be 'default', 'cfg' or 'interactive'
        self.opt = opt # Can be 'mandatory', 'default' or 'estimable'
        self.desc = desc
        self.longdesc = longdesc
        self.type = type

    def get_value(self):
        return self.value
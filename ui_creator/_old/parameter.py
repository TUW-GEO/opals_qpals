# -*- coding: utf-8 -*-


class Parameter(object):
    def __init__(self, name, type, remarks, description):
        self.name = name
        self.type = type
        self.remarks = remarks
        self.description = description

    def __repr__(self):
        return ("Parameter --- %s ---\n\tType: %s\n\tRemarks: %s\n\tDescription: %s"%(
            self.name, self.type, self.remarks, self.description))
from qgis.core import *
from qgis.gui import *


class QpalsVectorLayer(QgsVectorLayer):
    def __init__(self, *args, **kwargs):
        super(QpalsVectorLayer, self).__init__(*args, **kwargs)
from qgis.core import *
from qgis.gui import *


class QpalsRasterLayer(QgsRasterLayer):
    def __init__(self, *args, **kwargs):
        super(QpalsRasterLayer, self).__init__(*args, **kwargs)
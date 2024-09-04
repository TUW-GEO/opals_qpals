from qgis.gui import QgsCheckableComboBox
from qgis.PyQt.QtCore import pyqtSignal

class QMultiSelectComboBox(QgsCheckableComboBox):
    """with custom signal activated to handle QComboBox and QMultiSelectComboBox is similar manner"""
    activated = pyqtSignal(str, name="activated")

    def __init__(self, *args, **kwargs):
        super(QMultiSelectComboBox, self).__init__(*args, **kwargs)
        #self.textChanged = self.checkedItemsChanged  # not sure if this is still needed
        self.checkedItemsChanged.connect(self.changed)

    def changed(self,elems):
        self.activated.emit(";".join(elems))

    def text(self):
        items = self.checkedItems()
        return ";".join(items)

    def setText(self, QString):
        #print(f"QMultiSelectComboBox.setText - QString={QString}")
        values = QString.split(";")
        self.setCheckedItems(values)

from qgis.gui import QgsCheckableComboBox

class QMultiSelectComboBox(QgsCheckableComboBox):
    def __init__(self, *args, **kwargs):
        super(QMultiSelectComboBox, self).__init__(*args, **kwargs)
        self.textChanged = self.checkedItemsChanged  # not sure if this is still needed

    def text(self):
        items = self.checkedItems()
        return ";".join(items)

    def setText(self, QString):
        #print(f"QMultiSelectComboBox.setText - QString={QString}")
        values = QString.split(";")
        self.setCheckedItems(values)

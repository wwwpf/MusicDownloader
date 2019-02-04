from PyQt5.QtCore import (QAbstractTableModel, QModelIndex, QObject, Qt,
                          QVariant, pyqtSignal)


class Item(QObject):
    def __init__(self):
        super().__init__()

        self.selected = False   # 当前是否被选中


class TableModel(QAbstractTableModel):

    SECLECTION_INDEX = -1

    update_selection = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.items = []
        self.header = {}

        self.current_selected = 0

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.header[section]
        return QVariant()

    def rowCount(self, index=QModelIndex()):
        return len(self.items)

    def columnCount(self, index=QModelIndex()):
        return len(self.header)

    def get_items(self):
        return self.items

    def set_items(self, v):
        self.beginResetModel()
        self.items = v
        self.current_selected = 0
        self.endResetModel()

    def data(self, index, role):
        if (role == Qt.UserRole):
            row = index.row()
            return self.get_items()[row]
        return QVariant()

    def flip_selection(self, row):
        item = self.get_items()[row]
        self.current_selected += -1 if item.selected else 1
        item.selected = not item.selected
        # 更新 headerview 的复选框状态
        self.update_selection.emit()
        # 更新当前行
        begin = self.createIndex(row, 0)
        end = self.createIndex(row, self.columnCount(None))
        self.dataChanged.emit(begin, end)

    def is_all_selected(self):
        return self.rowCount(None) == self.current_selected

    def is_all_unselected(self):
        return 0 == self.current_selected

    def set_all(self, flag=True):
        for item in self.get_items():
            item.selected = flag
        self.current_selected = self.rowCount(None) if flag else 0
        if self.SECLECTION_INDEX >= 0:
            begin = self.createIndex(0, self.SECLECTION_INDEX)
            end = self.createIndex(self.rowCount(None), self.SECLECTION_INDEX)
            self.dataChanged.emit(begin, end)
            self.update_selection.emit()

    def select_all(self):
        self.set_all(True)

    def unselect_all(self):
        self.set_all(False)

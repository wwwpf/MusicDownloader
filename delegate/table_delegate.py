from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QStyledItemDelegate, QToolTip


class TableDelegate(QStyledItemDelegate):

    HOVER_BACKGROUND_COLOR = QColor(229, 243, 255)
    SELECTED_BACKGROUND_COLOR = QColor(204, 232, 255)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_row = -1

    def reset(self):
        self.hover_row = -1

    def set_hover_row(self, row):
        self.hover_row = row

    def paint_hover_row(self, painter, option, index):
        row = index.row()
        if row == self.hover_row:
            painter.fillRect(option.rect, self.HOVER_BACKGROUND_COLOR)
        item = index.data(Qt.UserRole)
        if item.selected:
            painter.fillRect(option.rect, self.SELECTED_BACKGROUND_COLOR)

    def paint(self, painter, option, index):
        self.paint_hover_row(painter, option, index)
        super().paint(painter, option, index)

    def need_show_tool_tip(self, event, index):
        return False

    def helpEvent(self, event, view, option, index):
        if self.need_show_tool_tip(event, index):
            QToolTip.showText(event.globalPos(), index.data(
                Qt.DisplayRole), None, QRect(), 1000)
            return True
        return False

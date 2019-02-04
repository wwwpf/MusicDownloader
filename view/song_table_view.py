from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyle

from delegate.song_table_delegate import SongDelegate
from model.song_model import SongModel
from utils import get_center_rect
from view.table_view import TableHeaderView, TableView


def get_check_state(state, flag):
    return (state
            & (~QStyle.State_On)
            & (~QStyle.State_Off)
            & (~QStyle.State_NoChange)) \
        | flag


class SongTableHeaderView(TableHeaderView):
    def __init__(self, orientation, model, parent=None):
        super().__init__(orientation, model, parent)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()
        if logicalIndex != SongModel.SECLECTION_INDEX:
            return

        self.selected_button.rect = get_center_rect(rect)
        if self.model.is_all_unselected():
            self.selected_button.state = get_check_state(
                self.selected_button.state, QStyle.State_Off)
        elif self.model.is_all_selected():
            self.selected_button.state = get_check_state(
                self.selected_button.state, QStyle.State_On)
        else:
            self.selected_button.state = get_check_state(
                self.selected_button.state, QStyle.State_NoChange)
        self.style().drawPrimitive(QStyle.PE_IndicatorCheckBox, self.selected_button, painter)

    def mousePressEvent(self, event):
        if self.selected_button.rect.contains(event.pos()):
            if self.model.is_all_selected():
                self.model.unselect_all()
            else:
                self.model.select_all()
        super().mousePressEvent(event)

    def update_section(self):
        '''立即刷新复选框
        '''
        self.headerDataChanged(
            Qt.Horizontal, SongModel.SECLECTION_INDEX, SongModel.SECLECTION_INDEX)


class SongTableView(TableView):
    def __init__(self, parent=None, download_manager=None, play_manager=None):
        super().__init__(parent)

        self.setItemDelegate(SongDelegate(parent, download_manager, play_manager))

    def reset(self):
        super().reset()
        self.itemDelegate().reset()

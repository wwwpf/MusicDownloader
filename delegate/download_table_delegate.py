from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QStyle, QStyleOptionProgressBar

from delegate.table_delegate import TableDelegate
from model.download_model import DownloadModel


class DownloadDelegate(TableDelegate):

    def __init__(self, parent=None, download_manager=None):
        super().__init__(parent)

        self.progress_bar = QStyleOptionProgressBar()
        self.progress_bar.minimum = 0
        self.progress_bar.maximum = 100
        self.progress_bar.textAlignment = Qt.AlignCenter
        self.progress_bar.textVisible = True

        self.download_manager = download_manager

    def paint(self, painter, option, index):
        col = index.column()
        if col == DownloadModel.PROGRESS_INDEX:
            progress = index.data(Qt.DisplayRole) * 100
            self.progress_bar.text = "%05.2f%%" % progress
            self.progress_bar.rect = option.rect
            self.progress_bar.progress = int(progress)
            QApplication.style().drawControl(QStyle.CE_ProgressBar, self.progress_bar, painter)
            return
        super().paint(painter, option, index)

    def need_show_tool_tip(self, event, index):
        col = index.column()
        if col == DownloadModel.SONG_INDEX:
            return True
        return False

import os

from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QHeaderView, QMainWindow, QMessageBox
from PyQt5.uic import loadUi

from config import (NETEASE_CLOUD_MUSIC, RESOURCE_PATH, SUPPORED_WEB_SITES,
                    ButtonConfig)
from manager.download_manager import DownloadManager
from manager.play_manager import PlayManager
from manager.search_manager import SearchManager
from model.download_model import DownloadModel
from model.song_model import SongModel
from resources.about_dialog import AboutDialog
from utils import get_screen_center_rect
from view.download_table_view import DownloadTableView
from view.song_table_view import SongTableHeaderView, SongTableView


class SpiderThread(QThread):

    finished = pyqtSignal()

    def __init__(self, fun, arg):
        super().__init__()

        self.fun = fun
        self.arg = arg

    def run(self):
        self.result, self.num = self.fun(self.arg)
        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = loadUi(os.path.join(RESOURCE_PATH, "mainwindow.ui"), self)

        self.download_item_model = DownloadModel()
        self.download_manager = DownloadManager(self.download_item_model)

        self.download_table_view = DownloadTableView(
            self.ui.download_tab, self.download_manager)
        self.download_table_view.setModel(self.download_item_model)
        self.download_table_view.horizontalHeader().setStretchLastSection(True)
        self.ui.download_grid_layout.addWidget(self.download_table_view, 0, 0)

        self.play_manager = PlayManager(self.ui.play_layout, parent)

        self.song_item_model = SongModel(self)
        self.song_table_view = SongTableView(
            self.ui.search_tab, self.download_manager, self.play_manager)
        self.song_table_view.setModel(self.song_item_model)

        song_header_view = SongTableHeaderView(
            Qt.Horizontal, self.song_table_view.model(), self.song_table_view)
        self.song_table_view.setHorizontalHeader(song_header_view)

        self.song_item_model.update_selection.connect(
            song_header_view.update_section)
        self.song_item_model.update_selection.connect(
            self.update_download_button)

        self.song_table_view.horizontalHeader().setSectionResizeMode(
            SongModel.SECLECTION_INDEX, QHeaderView.Fixed)
        self.song_table_view.setColumnWidth(SongModel.SECLECTION_INDEX, 35)
        self.song_table_view.setColumnWidth(SongModel.NAME_INDEX, 300)
        self.song_table_view.horizontalHeader().setStretchLastSection(True)
        self.ui.search_grid_layout.addWidget(self.song_table_view, 1, 0)

        self.ui.search_button.setIcon(ButtonConfig.SEARCH_ICON)

        self.search_manager = SearchManager(
            self.song_item_model, self.ui.page_layout, parent)

        self.ui.search_site_combobox.addItems(SUPPORED_WEB_SITES.keys())

        self.old_spider = None
        self.old_query = None
        self.old_playlist_id = None

    # pyqtSlot() 指明函数签名，防止两个插槽都收到信号
    @pyqtSlot()
    def on_about_triggered(self):
        a = AboutDialog(self)
        a.setWindowFlags(a.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        a.exec()

    def update_download_button(self):
        self.ui.download_button.setEnabled(
            not self.song_item_model.is_all_unselected())

    @pyqtSlot()
    def on_download_button_clicked(self):
        QMessageBox.information(self, "提示", "暂不提供下载")
        # spider = self.song_item_model.get_spider()
        # for song in self.song_item_model.get_items():
        #     if song.selected:
        #         self.download_manager.add_download()
        # self.song_item_model.unselect_all()

    @pyqtSlot()
    def on_jump_button_clicked(self):
        playlist_id = self.ui.cloud_music_play_list_line_edit.text()
        if not playlist_id or len(playlist_id) == 0:
            return
        if self.old_playlist_id == playlist_id:
            return

        self.old_playlist_id = playlist_id
        spider = SUPPORED_WEB_SITES[NETEASE_CLOUD_MUSIC]
        self.playlist_spider_thread = SpiderThread(
            spider.get_playlist, playlist_id)
        self.playlist_spider_thread.finished.connect(self.playlist_finished)
        self.playlist_spider_thread.start()

    @pyqtSlot()
    def playlist_finished(self):
        playlist_id = self.ui.cloud_music_play_list_line_edit.text()
        spider = SUPPORED_WEB_SITES[NETEASE_CLOUD_MUSIC]
        result = self.playlist_spider_thread.result
        total_count = self.playlist_spider_thread.num
        spider.set_query_num(total_count)
        self.set_total_song_number(total_count)
        query = self.ui.query_line_edit.text()
        self.search_manager.search_changed(
            spider, playlist_id, total_count, result)

    @pyqtSlot()
    def query_finished(self):
        spider = SUPPORED_WEB_SITES[self.ui.search_site_combobox.currentText()]
        query = self.ui.query_line_edit.text()
        result = self.query_spider_thread.result
        total_count = self.query_spider_thread.num
        self.set_total_song_number(total_count)
        self.search_manager.search_changed(spider, query, total_count, result)

    def set_total_song_number(self, number):
        self.ui.song_label.setText("共 %d 首歌曲" % (number))

    @pyqtSlot()
    def on_search_button_clicked(self):
        spider = SUPPORED_WEB_SITES[self.ui.search_site_combobox.currentText()]
        query = self.ui.query_line_edit.text()
        if not query or len(query) == 0:
            return
        if self.old_spider == spider and self.old_query == query:
            return

        self.old_spider = spider
        self.old_query = query

        self.query_spider_thread = SpiderThread(spider.get_songs, query)
        self.query_spider_thread.finished.connect(self.query_finished)
        self.query_spider_thread.start()

    def closeEvent(self, event):
        self.download_manager.cancel_all_download()

    @pyqtSlot()
    def to_center(self):
        self.move(get_screen_center_rect(self.frameGeometry()).topLeft())

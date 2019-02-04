from PyQt5.QtCore import QEvent, QRect, QSize, Qt
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QApplication, QStyle, QStyleOptionButton, QMessageBox

from config import ButtonConfig
from delegate.table_delegate import TableDelegate
from model.song_model import Song, SongModel
from utils import get_center_rect


class SongDelegate(TableDelegate):

    def __init__(self, parent=None, download_manager=None, play_manager=None):
        super().__init__(parent)

        self.playing_row = -1       # 当前播放行

        self.download_button = QStyleOptionButton()
        self.download_button.state |= QStyle.State_Enabled
        self.download_button.icon = ButtonConfig.DOWNLOAD_ICON
        self.play_button = QStyleOptionButton()
        self.play_button.state |= QStyle.State_Enabled

        self.download_manager = download_manager
        self.play_manager = play_manager

    def reset(self):
        super().reset()
        self.playing_row = -1

    def set_playing_row(self, row):
        self.playing_row = row

    def paint(self, painter, option, index):
        row = index.row()
        col = index.column()
        if col == SongModel.SECLECTION_INDEX:
            # 绘制 checkbox
            self.paint_hover_row(painter, option, index)
            selected_button = QStyleOptionButton()
            selected_button.state |= QStyle.State_Enabled
            selected_button.state |= QStyle.State_On if index.data(
                Qt.DisplayRole) else QStyle.State_Off
            selected_button.rect = get_center_rect(option.rect)
            QApplication.style().drawPrimitive(
                QStyle.PE_IndicatorCheckBox, selected_button, painter)
            return
        if col == SongModel.NAME_INDEX:
            if row == self.hover_row:
                # 设置背景颜色
                super().paint_hover_row(painter, option, index)

                if not index.data(Qt.UserRole).available:
                    super().paint(painter, option, index)
                    return

                # 绘制下载按钮
                self.download_button.rect = QRect(option.rect.right()
                                                  - ButtonConfig.BUTTON_WIDTH,
                                                  option.rect.top(),
                                                  ButtonConfig.BUTTON_WIDTH,
                                                  option.rect.height())
                w = int(min(self.download_button.rect.width(),
                            self.download_button.rect.height()) * 0.8)
                self.download_button.iconSize = QSize(w, w)

                QApplication.style().drawControl(
                    QStyle.CE_PushButtonLabel, self.download_button, painter)

                # 绘制播放按钮
                self.play_button.rect = QRect(self.download_button.rect.left()
                                              - ButtonConfig.BUTTON_WIDTH
                                              - ButtonConfig.BUTTON_MARGIN,
                                              option.rect.top(),
                                              ButtonConfig.BUTTON_WIDTH,
                                              option.rect.height())
                if row != self.playing_row:
                    self.play_button.icon = ButtonConfig.PLAY_ICON
                else:
                    self.play_button.icon = ButtonConfig.PAUSE_ICON \
                        if self.play_manager.play_control.state() == QMediaPlayer.PlayingState \
                        else ButtonConfig.PLAY_ICON
                self.play_button.iconSize = QSize(w, w)
                QApplication.style().drawControl(
                    QStyle.CE_PushButtonLabel, self.play_button, painter)

                # 调整文字绘制区域
                option.rect.setRight(
                    self.play_button.rect.left() - ButtonConfig.BUTTON_MARGIN)
        super().paint(painter, option, index)

    def is_click_check_box(self, pos, option):
        center_rect = get_center_rect(option.rect)
        if center_rect.contains(pos):
            return True
        return False

    def editorEvent(self, event, model, option, index):
        row = index.row()
        if not model.get_items()[row].available:
            return True
        event_type = event.type()
        if event_type == QEvent.MouseButtonRelease:
            pos = event.pos()
            col = index.column()
            if col == SongModel.NAME_INDEX:
                if self.download_button.rect.contains(pos):
                    self.on_download_button_clicked(model, row)
                    return True
                elif self.play_button.rect.contains(pos):
                    self.on_play_button_clicked(model, row)
                    return True
            elif col == SongModel.SECLECTION_INDEX:
                if not self.is_click_check_box(pos, option):
                    return True
            model.flip_selection(row)
            return True
        return super().editorEvent(event, model, option, index)

    def need_show_tool_tip(self, event, index):
        col = index.column()
        if col == SongModel.NAME_INDEX:
            pos = event.pos()
            if not self.download_button.rect.contains(pos) and not self.play_button.rect.contains(pos):
                return True
        elif col == SongModel.SINGERS_INDEX or col == SongModel.ALBUM_INDEX:
            return True
        return False

    def on_download_button_clicked(self, model, row):
        QMessageBox.information(None, "提示", "暂不提供下载")
        # spider = model.get_spider()
        # song = model.get_items()[row]
        # self.download_manager.add_download()

    def on_play_button_clicked(self, model, row):
        if row != self.playing_row:
            spider = model.get_spider()
            song = model.get_items()[row]
            self.play_manager.add_to_play(spider, song)
            self.playing_row = row
        self.play_manager.play_control.play_clicked()

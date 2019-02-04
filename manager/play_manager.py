import time

from PyQt5.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot
from PyQt5.QtMultimedia import QAudio, QMediaContent, QMediaPlayer
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel,
                             QMessageBox, QPushButton, QSlider, QWidget)

from config import ButtonConfig, HttpRequestConfig


class PlayControl(QWidget):

    play = pyqtSignal()
    pause = pyqtSignal()
    stop = pyqtSignal()

    def __init__(self, layout, parent=None):
        super().__init__(parent)

        self.play_button = QPushButton(parent)
        self.play_button.setIcon(ButtonConfig.PLAY_ICON)
        self.play_button.clicked.connect(self.play_clicked)

        self.stop_button = QPushButton(parent)
        self.stop_button.setIcon(ButtonConfig.STOP_ICON)
        self.stop_button.clicked.connect(self.stop)

        layout.insertWidget(0, self.stop_button)
        layout.insertWidget(0, self.play_button)

        self.play_state = QMediaPlayer.StoppedState

    def state(self):
        return self.play_state

    def set_state(self, state):
        if state == self.play_state:
            return

        self.play_state = state

        if state == QMediaPlayer.StoppedState:
            self.stop_button.setEnabled(False)
            self.play_button.setIcon(ButtonConfig.PLAY_ICON)
        elif state == QMediaPlayer.PlayingState:
            self.stop_button.setEnabled(True)
            self.play_button.setIcon(ButtonConfig.PAUSE_ICON)
        elif state == QMediaPlayer.PausedState:
            self.stop_button.setEnabled(True)
            self.play_button.setIcon(ButtonConfig.PLAY_ICON)

    def play_clicked(self):
        if self.play_state == QMediaPlayer.StoppedState \
                or self.play_state == QMediaPlayer.PausedState:
            self.play.emit()
        elif self.play_state == QMediaPlayer.PlayingState:
            self.pause.emit()


class PlayManager(QWidget):

    NO_PLAYING_SONG = "没有正在播放的歌曲"

    def __init__(self, layout, parent=None):
        super().__init__(parent)

        self.player = QMediaPlayer(self)
        self.player.setAudioRole(QAudio.MusicRole)

        self.player.durationChanged.connect(self.duration_changed)
        self.player.positionChanged.connect(self.position_changed)
        self.player.mediaStatusChanged.connect(self.status_changed)
        self.player.bufferStatusChanged.connect(self.buffering_progress)
        self.player.stateChanged.connect(self.state_changed)
        self.player.error[QMediaPlayer.Error].connect(
            self.display_error_message)

        self.play_control = PlayControl(layout, parent)
        self.play_control.set_state(self.player.state())
        self.play_control.play.connect(self.player.play)
        self.play_control.pause.connect(self.player.pause)
        self.play_control.stop.connect(self.player.stop)

        self.player.stateChanged.connect(self.play_control.set_state)

        self.song_label = QLabel()
        self.song_label.setText(self.NO_PLAYING_SONG)
        self.song_label.setWordWrap(True)

        song_grid = QGridLayout(parent)
        song_grid.addWidget(self.song_label, 0, 0)

        self.duration_label = QLabel()
        self.duration_label.setText("00:00 / 00:00")
        self.slider = QSlider(Qt.Horizontal, parent)
        self.slider.setRange(0, self.player.duration() / 1000)
        self.slider.sliderMoved.connect(self.seek)
        progress_layout = QHBoxLayout(parent)
        progress_layout.insertWidget(0, self.duration_label)
        progress_layout.insertWidget(0, self.slider)
        song_grid.addLayout(progress_layout, 1, 0)

        self.status_label = QLabel()
        song_grid.addWidget(self.status_label, 2, 0)

        layout.addLayout(song_grid)

        if not self.is_player_available():
            QMessageBox.warning(self, "警告", "QMediaPlayer 对象无可用的服务")
            return

        self.song = None

    def is_player_available(self):
        return self.player.isAvailable()

    def add_to_play(self, spider, song):
        self.song = song
        spider.get_song_url(song)
        url = song.url
        if url is None or len(url) == 0:
            return
        req = QNetworkRequest(QUrl(url))
        req.setHeader(QNetworkRequest.UserAgentHeader,
                      HttpRequestConfig.CHROME_USER_AGENT)
        self.player.setMedia(QMediaContent(req))

    def duration_changed(self, duration):
        self.duration = int(duration / 1000)
        self.slider.setMaximum(self.duration)
        t = "00:00 / %s" % (self.song.get_time())
        self.duration_label.setText(t)

    def position_changed(self, progress):
        if not self.slider.isSliderDown():
            self.slider.setValue(int(progress / 1000))

        self.update_duration_info(int(progress / 1000))

    @pyqtSlot(int)
    def seek(self, seconds):
        self.player.setPosition(seconds * 1000)

    def state_changed(self, state):
        if QMediaPlayer.PlayingState == state \
                or QMediaPlayer.PausedState == state:
            self.song_label.setText("%s - %s" %
                                    (self.song.get_singers(), self.song.name))
        else:
            self.song_label.setText(self.NO_PLAYING_SONG)

    def status_changed(self, status):
        if QMediaPlayer.UnknownMediaStatus == status \
                or QMediaPlayer.NoMedia == status \
                or QMediaPlayer.LoadedMedia == status \
                or QMediaPlayer.BufferedMedia == status:
            self.set_status_info("")
        elif QMediaPlayer.LoadingMedia == status:
            self.set_status_info("加载中...")
        elif QMediaPlayer.BufferingMedia == status:
            self.set_status_info("缓存中...")
        elif QMediaPlayer.StalledMedia == status:
            self.set_status_info("等待中...")
        elif QMediaPlayer.EndOfMedia == status:
            QApplication.alert(self)
        elif QMediaPlayer.InvalidMedia == status:
            self.display_error_message()

    @pyqtSlot(int)
    def buffering_progress(self, progress):
        if self.player.mediaStatus() == QMediaPlayer.StalledMedia:
            self.set_status_info("等待中 %d%%" % (progress,))
        else:
            self.set_status_info("缓存中 %d%%" % (progress,))

    def set_status_info(self, info):
        self.status_label.setText(info)

    def display_error_message(self):
        self.set_status_info(self.player.errorString())

    def update_duration_info(self, current_info):
        s = time.strftime("%M:%S", time.gmtime(current_info))
        t = "%s / %s" % (s, self.song.get_time())
        self.duration_label.setText(t)

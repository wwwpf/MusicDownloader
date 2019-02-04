import os

from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QDialog, QLabel
from PyQt5.uic import loadUi

from config import RESOURCE_PATH, ImageConfig


class AboutDialog(QDialog):

    MAX_LENGTH = 960

    def __init__(self, parent):
        super().__init__(parent)

        if os.path.exists(ImageConfig.ABOUT_DIALOG_BACKGROUND_FILE):
            self.setWindowTitle("关于 - 仅供学习研究使用")

            label = QLabel(self)
            label.setMaximumSize(self.MAX_LENGTH, self.MAX_LENGTH)
            movie = QMovie(ImageConfig.ABOUT_DIALOG_BACKGROUND_FILE)
            label.setMovie(movie)

            movie.start()
            self.resize(movie.currentImage().size())

        else:
            self.ui = loadUi(os.path.join(
                RESOURCE_PATH, "about_dialog.ui"), self)

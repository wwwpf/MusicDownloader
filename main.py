import logging
import sys

from PyQt5.QtWidgets import QApplication

from main_window import MainWindow
from utils import init_logging


def main():
    init_logging()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

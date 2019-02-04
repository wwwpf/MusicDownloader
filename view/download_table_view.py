from delegate.download_table_delegate import DownloadDelegate
from view.table_view import TableView


class DownloadTableView(TableView):
    def __init__(self, parent=None, download_manager=None):
        super().__init__(parent)

        self.setItemDelegate(DownloadDelegate(parent, download_manager))

from PyQt5.QtWidgets import QHeaderView, QStyle, QStyleOptionButton, QTableView

from delegate.table_delegate import TableDelegate


class TableHeaderView(QHeaderView):
    def __init__(self, orientation, model, parent=None):
        super().__init__(orientation, parent)

        self.model = model

        self.selected_button = QStyleOptionButton()
        self.selected_button.state |= QStyle.State_Enabled
        self.selected_button.state |= QStyle.State_Off

    def update_section(self):
        '''立即刷新复选框
        '''
        pass


class TableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMouseTracking(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.current_row = -1
        self.verticalHeader().hide()

        self.setItemDelegate(TableDelegate(parent))

    def paint_row(self, row):
        table_model = self.model()
        self.itemDelegate().set_hover_row(row)
        for i in range(table_model.columnCount()):
            self.update(table_model.index(self.current_row, i))
            self.update(table_model.index(row, i))

        self.current_row = row

    def mouseMoveEvent(self, event):
        row = self.indexAt(event.pos()).row()
        if row != self.current_row:
            self.paint_row(row)

    def mousePressEvent(self, event):
        row = self.indexAt(event.pos()).row()
        self.paint_row(row)

    def leaveEvent(self, event):
        self.itemDelegate().set_hover_row(-1)
        table_model = self.model()
        for i in range(table_model.columnCount()):
            self.update(table_model.index(self.current_row, i))

        self.current_row = -1

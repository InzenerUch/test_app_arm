from PyQt6.QtCore import Qt, QSortFilterProxyModel, QModelIndex

class RequestFilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.filter_recipient = ""
        self.filter_date = ""
        self.filter_number = ""
        self.filter_response_number = ""  # ✅ НОВОЕ
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def set_recipient_filter(self, text: str):
        self.filter_recipient = text.lower()
        self.invalidateFilter()

    def set_date_filter(self, text: str):
        self.filter_date = text.lower()
        self.invalidateFilter()

    def set_number_filter(self, text: str):
        self.filter_number = text.lower()
        self.invalidateFilter()

    def set_response_filter(self, text: str):  # ✅ НОВОЕ
        self.filter_response_number = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if self.filter_recipient:
            idx = model.index(source_row, 2, source_parent)
            val = str(model.data(idx, Qt.ItemDataRole.DisplayRole) or "").lower()
            if self.filter_recipient not in val: return False
            
        if self.filter_date:
            idx = model.index(source_row, 3, source_parent)
            val = model.data(idx, Qt.ItemDataRole.DisplayRole)
            date_str = val.toString("dd.MM.yyyy") if hasattr(val, 'toString') else str(val)
            if self.filter_date not in date_str.lower(): return False
            
        if self.filter_number:
            idx_num = model.index(source_row, 4, source_parent)
            val_num = str(model.data(idx_num, Qt.ItemDataRole.DisplayRole) or "").lower()
            idx_id = model.index(source_row, 0, source_parent)
            val_id = str(model.data(idx_id, Qt.ItemDataRole.DisplayRole) or "").lower()
            if self.filter_number not in val_num and self.filter_number not in val_id: return False

        # ✅ ФИЛЬТР ПО НОМЕРУ ОТВЕТА (Колонка 6)
        if self.filter_response_number:
            idx = model.index(source_row, 6, source_parent)
            val = str(model.data(idx, Qt.ItemDataRole.DisplayRole) or "").lower()
            if self.filter_response_number not in val: return False
            
        return True
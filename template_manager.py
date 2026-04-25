"""
Менеджер управления списком шаблонов в таблице
"""
from PyQt6.QtWidgets import QTableView, QMessageBox
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from template_edit_dialog import TemplateEditDialog

class TemplateManager:
    def __init__(self, db):
        self.db = db
        self.model = QSqlQueryModel()
        self.view = None

    def bind_view(self, view: QTableView):
        self.view = view
        view.setModel(self.model)
        view.setAlternatingRowColors(True)
        view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        view.horizontalHeader().setStretchLastSection(True)

    def load_templates(self):
        query = QSqlQuery(self.db)
        query.prepare("SELECT id, name, description, created_at FROM krd.document_templates WHERE is_deleted = FALSE ORDER BY name")
        query.exec()
        self.model.setQuery(query)
        if self.view:
            self.view.setColumnHidden(0, True)
            self.view.setColumnWidth(1, 250)
            self.view.setColumnWidth(2, 400)
            self.view.setColumnHidden(3, True)

    def add_template_dialog(self, parent):
        dialog = TemplateEditDialog(self.db, parent=parent)
        if dialog.exec() == 1:
            self.load_templates()

    def edit_template_dialog(self, parent):
        if not self.view or not self.view.selectionModel().hasSelection():
            return QMessageBox.warning(parent, "Внимание", "Выберите шаблон для редактирования")
        row = self.view.selectionModel().selectedRows()[0].row()
        template_id = self.model.data(self.model.index(row, 0))
        dialog = TemplateEditDialog(self.db, template_id=template_id, parent=parent)
        if dialog.exec() == 1:
            self.load_templates()

    def delete_selected(self, parent):
        if not self.view or not self.view.selectionModel().hasSelection():
            return QMessageBox.warning(parent, "Внимание", "Выберите шаблон для удаления")
        row = self.view.selectionModel().selectedRows()[0].row()
        template_id = self.model.data(self.model.index(row, 0))
        template_name = self.model.data(self.model.index(row, 1))
        reply = QMessageBox.question(parent, "Удалить шаблон", f"Удалить шаблон '{template_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            query = QSqlQuery(self.db)
            query.prepare("UPDATE krd.document_templates SET is_deleted = TRUE WHERE id = ?")
            query.addBindValue(template_id)
            if query.exec():
                self.load_templates()
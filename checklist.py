import sys
import json
import os

from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent


class ChecklistItem(QWidget):
    def __init__(self, text, on_delete):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox = QCheckBox(text)
        self.checkbox.stateChanged.connect(self.update_style)

        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.clicked.connect(on_delete)

        layout.addWidget(self.checkbox)
        layout.addStretch()
        layout.addWidget(self.delete_btn)
        self.setLayout(layout)

    def update_style(self):
        if self.checkbox.isChecked():
            self.checkbox.setStyleSheet("text-decoration: line-through; color: gray;")
        else:
            self.checkbox.setStyleSheet("")


class CategoryWidget(QGroupBox):
    def __init__(self, name, on_delete_category, on_move_up, on_move_down):
        super().__init__(name)
        self.category_name = name
        self.setCheckable(True)
        self.setChecked(True)

        self.main_layout = QVBoxLayout()
        self.items_layout = QVBoxLayout()
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header with move and delete buttons
        header_layout = QHBoxLayout()

        self.move_up_btn = QPushButton("▲")
        self.move_up_btn.setFixedSize(28, 24)
        self.move_up_btn.clicked.connect(on_move_up)
        self.move_up_btn.setToolTip("Move up")

        self.move_down_btn = QPushButton("▼")
        self.move_down_btn.setFixedSize(28, 24)
        self.move_down_btn.clicked.connect(on_move_down)
        self.move_down_btn.setToolTip("Move down")

        header_layout.addWidget(self.move_up_btn)
        header_layout.addWidget(self.move_down_btn)
        header_layout.addStretch()

        self.delete_category_btn = QPushButton("Delete Category")
        self.delete_category_btn.setFixedHeight(24)
        self.delete_category_btn.clicked.connect(on_delete_category)
        header_layout.addWidget(self.delete_category_btn)

        self.main_layout.addLayout(header_layout)
        self.main_layout.addLayout(self.items_layout)
        self.setLayout(self.main_layout)

    def add_item(self, item):
        self.items_layout.addWidget(item)

    def remove_item(self, item):
        self.items_layout.removeWidget(item)
        item.deleteLater()

    def get_items(self):
        items = []
        for i in range(self.items_layout.count()):
            layout_item = self.items_layout.itemAt(i)
            if layout_item is not None:
                widget = layout_item.widget()
                if isinstance(widget, ChecklistItem):
                    items.append({
                        "text": widget.checkbox.text(),
                        "checked": widget.checkbox.isChecked()
                    })
        return items

    def item_count(self):
        count = 0
        for i in range(self.items_layout.count()):
            layout_item = self.items_layout.itemAt(i)
            if layout_item is not None and isinstance(layout_item.widget(), ChecklistItem):
                count += 1
        return count


def get_app_path():
    """Get the correct path whether running as script or frozen exe."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(__file__)


class MainWindow(QMainWindow):
    SAVE_FILE = os.path.join(get_app_path(), "checklist_data.json")
    SETTINGS_FILE = os.path.join(get_app_path(), "checklist_settings.json")
    DEFAULT_CATEGORY = "General"

    LIGHT_STYLE = ""
    DARK_STYLE = """
        QMainWindow, QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QGroupBox {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }
        QGroupBox::title {
            color: #ffffff;
        }
        QLineEdit {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
            color: #ffffff;
        }
        QPushButton {
            background-color: #4a4a4a;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px 8px;
            color: #ffffff;
        }
        QPushButton:hover {
            background-color: #5a5a5a;
        }
        QComboBox {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
            color: #ffffff;
        }
        QComboBox QAbstractItemView {
            background-color: #3c3c3c;
            color: #ffffff;
            selection-background-color: #5a5a5a;
        }
        QScrollArea {
            border: none;
        }
        QCheckBox {
            color: #ffffff;
        }
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Checklist")
        self.setMinimumSize(400, 400)

        self.categories = {}  # name -> CategoryWidget
        self.dark_mode = False

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Category selection area
        category_layout = QHBoxLayout()

        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(150)

        add_category_btn = QPushButton("+ New Category")
        add_category_btn.clicked.connect(self.add_new_category)

        self.theme_btn = QPushButton("Dark")
        self.theme_btn.setFixedWidth(50)
        self.theme_btn.clicked.connect(self.toggle_theme)

        category_layout.addWidget(self.category_combo)
        category_layout.addWidget(add_category_btn)
        category_layout.addStretch()
        category_layout.addWidget(self.theme_btn)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Add a new item...")
        self.input_field.returnPressed.connect(self.add_item)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_item)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(add_btn)

        # Scrollable checklist area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.checklist_widget = QWidget()
        self.checklist_layout = QVBoxLayout()
        self.checklist_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.checklist_widget.setLayout(self.checklist_layout)
        scroll.setWidget(self.checklist_widget)

        main_layout.addLayout(category_layout)
        main_layout.addLayout(input_layout)
        main_layout.addWidget(scroll)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Load saved items and settings
        self.load_settings()
        self.load_items()

        # Ensure at least the default category exists
        if not self.categories:
            self.create_category(self.DEFAULT_CATEGORY)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet(self.DARK_STYLE)
            self.theme_btn.setText("Light")
        else:
            self.setStyleSheet(self.LIGHT_STYLE)
            self.theme_btn.setText("Dark")

    def load_settings(self):
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, "r") as f:
                    settings = json.load(f)
                    self.dark_mode = settings.get("dark_mode", False)
            except (json.JSONDecodeError, IOError):
                pass
        self.apply_theme()

    def save_settings(self):
        settings = {"dark_mode": self.dark_mode}
        with open(self.SETTINGS_FILE, "w") as f:
            json.dump(settings, f)

    def create_category(self, name):
        if name in self.categories:
            return self.categories[name]

        category_widget = CategoryWidget(
            name,
            lambda: self.delete_category(name),
            lambda: self.move_category_up(name),
            lambda: self.move_category_down(name)
        )
        self.categories[name] = category_widget
        self.checklist_layout.addWidget(category_widget)

        # Update combo box
        self.category_combo.addItem(name)

        return category_widget

    def move_category_up(self, name):
        if name not in self.categories:
            return
        category_widget = self.categories[name]
        index = self.checklist_layout.indexOf(category_widget)
        if index > 0:
            self.checklist_layout.removeWidget(category_widget)
            self.checklist_layout.insertWidget(index - 1, category_widget)
            self._update_combo_order()

    def move_category_down(self, name):
        if name not in self.categories:
            return
        category_widget = self.categories[name]
        index = self.checklist_layout.indexOf(category_widget)
        if index < self.checklist_layout.count() - 1:
            self.checklist_layout.removeWidget(category_widget)
            self.checklist_layout.insertWidget(index + 1, category_widget)
            self._update_combo_order()

    def _update_combo_order(self):
        """Update combo box order to match layout order."""
        current_text = self.category_combo.currentText()
        self.category_combo.clear()
        for i in range(self.checklist_layout.count()):
            layout_item = self.checklist_layout.itemAt(i)
            if layout_item is not None:
                widget = layout_item.widget()
                if isinstance(widget, CategoryWidget):
                    self.category_combo.addItem(widget.category_name)
        # Restore selection
        index = self.category_combo.findText(current_text)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

    def delete_category(self, name):
        if name in self.categories:
            category_widget = self.categories[name]

            # Remove from layout
            self.checklist_layout.removeWidget(category_widget)
            category_widget.deleteLater()

            # Remove from dict
            del self.categories[name]

            # Remove from combo box
            index = self.category_combo.findText(name)
            if index >= 0:
                self.category_combo.removeItem(index)

            # Ensure at least one category exists
            if not self.categories:
                self.create_category(self.DEFAULT_CATEGORY)

    def add_new_category(self):
        name, ok = QInputDialog.getText(self, "New Category", "Category name:")
        if ok and name.strip():
            name = name.strip()
            if name not in self.categories:
                self.create_category(name)
                # Select the new category
                index = self.category_combo.findText(name)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)

    def add_item(self):
        text = self.input_field.text().strip()
        if text:
            category_name = self.category_combo.currentText()
            if category_name and category_name in self.categories:
                category_widget = self.categories[category_name]

                item = ChecklistItem(text, lambda: None)
                item.delete_btn.clicked.disconnect()
                item.delete_btn.clicked.connect(lambda: category_widget.remove_item(item))

                category_widget.add_item(item)
                self.input_field.clear()

    def get_all_items(self):
        data = {"categories": {}}
        # Save in layout order to preserve category order
        for i in range(self.checklist_layout.count()):
            layout_item = self.checklist_layout.itemAt(i)
            if layout_item is not None:
                widget = layout_item.widget()
                if isinstance(widget, CategoryWidget):
                    data["categories"][widget.category_name] = {
                        "expanded": widget.isChecked(),
                        "items": widget.get_items()
                    }
        return data

    def save_items(self):
        with open(self.SAVE_FILE, "w") as f:
            json.dump(self.get_all_items(), f, indent=2)

    def load_items(self):
        if os.path.exists(self.SAVE_FILE):
            with open(self.SAVE_FILE, "r") as f:
                try:
                    data = json.load(f)

                    # Handle old format (list of items)
                    if isinstance(data, list):
                        self.create_category(self.DEFAULT_CATEGORY)
                        for item_data in data:
                            self.add_item_with_data(
                                self.DEFAULT_CATEGORY,
                                item_data["text"],
                                item_data.get("checked", False)
                            )
                    # Handle new format (categories dict)
                    elif isinstance(data, dict) and "categories" in data:
                        for cat_name, cat_data in data["categories"].items():
                            category_widget = self.create_category(cat_name)
                            category_widget.setChecked(cat_data.get("expanded", True))
                            for item_data in cat_data.get("items", []):
                                self.add_item_with_data(
                                    cat_name,
                                    item_data["text"],
                                    item_data.get("checked", False)
                                )
                except json.JSONDecodeError:
                    pass

    def add_item_with_data(self, category_name, text, checked=False):
        if category_name not in self.categories:
            self.create_category(category_name)

        category_widget = self.categories[category_name]
        item = ChecklistItem(text, lambda: None)
        item.delete_btn.clicked.disconnect()
        item.delete_btn.clicked.connect(lambda: category_widget.remove_item(item))

        if checked:
            item.checkbox.setChecked(True)

        category_widget.add_item(item)

    def closeEvent(self, a0: QCloseEvent | None) -> None:  # type: ignore[override]
        self.save_items()
        self.save_settings()
        if a0:
            a0.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

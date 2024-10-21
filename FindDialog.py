from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QLabel, QLineEdit, QDialog
from PyQt5.QtGui import  QTextCharFormat, QBrush, QColor

class FindDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar")
        self.setModal(True)
        self.setFixedSize(300, 100)

        self.layout = QVBoxLayout()

        self.label = QLabel("Buscar:")
        self.layout.addWidget(self.label)

        self.find_input = QLineEdit()
        self.layout.addWidget(self.find_input)

        self.find_button = QPushButton("Buscar")
        self.find_button.clicked.connect(self.find_text)
        self.layout.addWidget(self.find_button)

        self.setLayout(self.layout)
        self.parent = parent

    def find_text(self):
        text = self.find_input.text()
        if text:
            cursor = self.parent.text_edit.textCursor()
            document = self.parent.text_edit.document()
            found = False

            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QBrush(QColor("green")))
            highlight_format.setForeground(QBrush(QColor("white")))
            
            cursor.beginEditBlock()
            while not cursor.isNull() and not cursor.atEnd():
                cursor = document.find(text, cursor)
                if not cursor.isNull():
                    cursor.mergeCharFormat(highlight_format)
                    self.parent.text_edit.setTextCursor(cursor)
                    found = True
                    break
            cursor.endEditBlock()

            if not found:
                self.parent().show_message("Info", "Buscar", "No se encontró el texto.")


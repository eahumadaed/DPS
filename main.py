from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QLabel, QComboBox, QCheckBox, QHBoxLayout
from PyQt5.QtCore import Qt
import sys
import requests
from next_window import NextWindow
from comunas import *
import traceback

def log_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    with open("error_log.txt", "w") as f:
        f.write("Ocurrió un error no capturado:\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    print("Ha ocurrido un error. Revisa el archivo error_log.txt para más detalles.")
    input("Presiona Enter para salir...")

sys.excepthook = log_exception

class UserSelectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Seleccionar Usuario')
        self.setGeometry(100, 100, 300, 50)
        self.center_window()
        
        self.layout = QVBoxLayout()
        
        self.label = QLabel("Seleccione un usuario:", self)
        self.layout.addWidget(self.label)
        
        self.user_select = QComboBox(self)
        self.user_select.wheelEvent = lambda event: event.ignore()
        self.layout.addWidget(self.user_select)
        
        self.screen_layout = QHBoxLayout()
        self.screen_layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes
        self.screen_layout.setSpacing(0)
        
        self.screen_label = QLabel("Pantalla Pequeña:")
        self.screen_layout.addWidget(self.screen_label)
        self.screen_checkbox = QCheckBox()
        self.screen_layout.addWidget(self.screen_checkbox)
        
        
        
        self.screen_layout.setAlignment(self.screen_checkbox, Qt.AlignLeft)
        self.screen_layout.setAlignment(self.screen_label, Qt.AlignLeft)
        
        self.layout.addLayout(self.screen_layout)
        
        self.continue_button = QPushButton("Continuar", self)
        self.continue_button.clicked.connect(self.load_next_interface)
        self.layout.addWidget(self.continue_button)
        
        self.setLayout(self.layout)
        self.load_users()

    def load_users(self):
        try:
            response = requests.get('https://loverman.net/dbase/dga2024/api/api.php?action=getUsers', timeout=10)
            response.raise_for_status()
            users = response.json()
            for user in users:
                user_info = f"{user['name']} ({int(user['asignados'])+int(user['Pendiente'])} Asignados| {user['terminados']} Terminados)"
                self.user_select.addItem(user_info, {
                    'id': user['id'],
                    'name': user['name'],
                    'terminados': user['terminados']
                })
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener los usuarios: {e}")
            self.label.setText("Error al obtener los usuarios")
        except ValueError as e:
            print(f"Error al interpretar la respuesta: {e}")
            self.label.setText("Error al interpretar la respuesta")

    def load_next_interface(self):
        selected_user_data = self.user_select.currentData()
        if selected_user_data:
            selected_user_id = selected_user_data['id']
            selected_user_name = selected_user_data['name']
            selected_user_terminados = selected_user_data['terminados']

            print(f"ID del usuario seleccionado: {selected_user_id}")
            print(f"Nombre del usuario seleccionado: {selected_user_name}")
            print(f"Terminados del usuario seleccionado: {selected_user_terminados}")

            self.hide()
            self.next_window = NextWindow(selected_user_id, selected_user_name, selected_user_terminados, smallScreen=self.screen_checkbox.isChecked())
            self.next_window.showMaximized()
            self.next_window.show()

        
    def center_window(self):
        window_size = self.sizeHint()
        screen = self.screen().geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.setGeometry(x, y, 300, 50)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = UserSelectionWindow()
    main_window.show()
    
    try:
        sys.exit(app.exec_())
    except Exception as e:
        raise ValueError("Este es un error de prueba.")

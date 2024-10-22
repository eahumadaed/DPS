from PyQt5.QtWidgets import QVBoxLayout, QFrame, QListWidget, QPushButton, QLabel, QGridLayout, QComboBox, QLineEdit, QDialog, QListWidgetItem
import requests
import re


class UsuarioModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionar Usuarios")
        self.setGeometry(200, 200, 700, 700)
        self.layout = QVBoxLayout()

        self.loaded_ruts_with_error = []
        
        self.usuario_list = QListWidget(self)
        self.layout.addWidget(self.usuario_list)

        self.add_button = QPushButton("Agregar", self)
        self.add_button.clicked.connect(self.add_usuario)
        self.layout.addWidget(self.add_button)

        self.save_button = QPushButton("Guardar", self)
        self.save_button.clicked.connect(self.save_usuarios)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

        self.load_usuarios()
        

    def add_usuario(self, data=None):
        container = QFrame(self)
        layout = QGridLayout(container)

        rut_label = QLabel("RUT")
        layout.addWidget(rut_label, 0, 0)
        rut = QLineEdit()
        rut.textChanged.connect(lambda: self.parent().to_uppercase(rut))
        if data:
            rut.setText(data['rut'])
        layout.addWidget(rut, 0, 1)
        rut.focusOutEvent = lambda event: self.on_rut_focus_out(rut,event)

        buscar_button = QPushButton("Buscar", self)
        buscar_button.clicked.connect(lambda: self.buscar_rut(rut, container))
        layout.addWidget(buscar_button, 0, 2)

        nac_label = QLabel("Nacionalidad:")
        layout.addWidget(nac_label, 1, 0)
        nac = QComboBox()
        nac.wheelEvent = lambda event: event.ignore()
        nac.addItems(['--', 'CHILENA', 'EXTRANJERA'])
        if data:
            nac.setCurrentText(data['nac'])
        layout.addWidget(nac, 1, 1)

        tipo_label = QLabel("Tipo:")
        layout.addWidget(tipo_label, 1, 2)
        tipo = QComboBox()
        tipo.wheelEvent = lambda event: event.ignore()
        tipo.addItems(['--', 'NATURAL', 'JURIDICA'])
        if data:
            tipo.setCurrentText(data['tipo'])
        layout.addWidget(tipo, 1, 3)

        genero_label = QLabel("Género:")
        layout.addWidget(genero_label, 2, 0)
        genero = QComboBox()
        genero.wheelEvent = lambda event: event.ignore()
        genero.addItems(['--', 'F', 'M'])
        if data:
            genero.setCurrentText(data['genero'])
        layout.addWidget(genero, 2, 1)

        nombre_label = QLabel("Nombre:")
        layout.addWidget(nombre_label, 2, 2)
        nombre = QLineEdit()
        nombre.textChanged.connect(lambda: self.parent().to_uppercase(nombre))
        if data:
            nombre.setText(data['nombre'])
        layout.addWidget(nombre, 2, 3)

        paterno_label = QLabel("Apellido Paterno:")
        layout.addWidget(paterno_label, 3, 0)
        paterno = QLineEdit()
        paterno.textChanged.connect(lambda: self.parent().to_uppercase(paterno))
        if data:
            paterno.setText(data['paterno'])
        layout.addWidget(paterno, 3, 1)

        materno_label = QLabel("Apellido Materno:")
        layout.addWidget(materno_label, 3, 2)
        materno = QLineEdit()
        materno.textChanged.connect(lambda: self.parent().to_uppercase(materno))
        if data:
            materno.setText(data['materno'])
        layout.addWidget(materno, 3, 3)

        delete_button = QPushButton("Borrar", self)
        delete_button.clicked.connect(lambda: self.delete_usuario(container, data.get('id') if data else None))
        layout.addWidget(delete_button, 4, 0, 1, 4)

        list_item = QListWidgetItem()
        list_item.setSizeHint(container.sizeHint())
        self.usuario_list.addItem(list_item)
        self.usuario_list.setItemWidget(list_item, container)

    def delete_usuario(self, container, usuario_id=None):
        if usuario_id:
            try:
                response = requests.post(f'{self.parent().api_base_url}deleteUsuario', json={'id': usuario_id})
                response.raise_for_status()
                result = response.json()

                if result.get('message') == 'Usuario eliminado correctamente':
                    self.remove_usuario_from_list(container)
                    self.parent().show_message("Info", "Eliminar", "Usuario eliminado correctamente.")
                else:
                    self.parent().show_message("Error", "Eliminar", result.get('message', 'Error desconocido'))

            except requests.RequestException as e:
                self.parent().show_message("Error", "Eliminar", str(e))
        else:
            self.remove_usuario_from_list(container)

    def remove_usuario_from_list(self, container):
        for i in range(self.usuario_list.count()):
            item = self.usuario_list.item(i)
            if self.usuario_list.itemWidget(item) == container:
                self.usuario_list.takeItem(i)
                break

    def save_usuarios(self, silenc=False):
        if not self.parent().current_formulario_id:
            self.parent().show_message("Error", "Guardar", "Seleccione un trabajo antes de guardar usuarios.")
            return

        usuarios_data = []
        for i in range(self.usuario_list.count()):
            container = self.usuario_list.itemWidget(self.usuario_list.item(i))
            data = {}
            for j in range(container.layout().count()):
                widget = container.layout().itemAt(j).widget()
                if isinstance(widget, QLineEdit):
                    label = container.layout().itemAt(j - 1).widget().text()
                    if "RUT" in label:
                        data['rut'] = widget.text()
                    elif "Nombre" in label:
                        data['nombre'] = widget.text()
                    elif "Apellido Paterno" in label:
                        data['paterno'] = widget.text()
                    elif "Apellido Materno" in label:
                        data['materno'] = widget.text()
                elif isinstance(widget, QComboBox):
                    label = container.layout().itemAt(j - 1).widget().text()
                    if "Nacionalidad" in label:
                        data['nac'] = widget.currentText()
                    elif "Tipo" in label:
                        data['tipo'] = widget.currentText()
                    elif "Género" in label:
                        data['genero'] = widget.currentText()

            usuarios_data.append(data)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(f'{self.parent().api_base_url}saveUsuarios', json={
                    'trabajo_id': self.parent().current_trabajo_id,
                    'formulario_id': self.parent().current_formulario_id,
                    'usuarios': usuarios_data
                })
                response.raise_for_status()
                if not silenc:
                    print("Usuarios guardados:", usuarios_data)
                    self.accept()
                    self.parent().show_message("Info", "Guardar", "Usuarios guardados exitosamente.")
                    self.deleteLater()
                break
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    if not silenc:
                        self.parent().show_message("Error", "Error al guardar usuarios", str(e))
                        print(f"Error al guardar usuarios: {e}")
                else:
                    print(f"Reintentando... intento {attempt + 1} de {max_retries}")

    
    def formatear_rut(self, rut):
        """
        clean_rut = rut.replace(".", "").replace("-", "")
        if 7 <= len(clean_rut) <= 9:
            return self.parent().calcular_dv(clean_rut)
        """
        return rut

    def load_usuarios(self):
        if not self.parent().current_formulario_id:
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(f'{self.parent().api_base_url}getUsuarios&formulario_id={self.parent().current_formulario_id}')
                response.raise_for_status()
                usuarios_data = response.json()
                print(f"Usuarios cargados: {usuarios_data}")
                if isinstance(usuarios_data, list):
                    for usuario in usuarios_data:
                        usuario['rut'] = self.formatear_rut(usuario['rut'])
                        self.add_usuario_with_data(usuario)                        
                break
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"Error al cargar usuarios: {e}")
                    self.parent().show_message("Error", "Error al cargar usuarios", str(e))
                else:
                    print(f"Reintentando... intento {attempt + 1} de {max_retries}")

    def add_usuario_with_data(self, data):
        container = QFrame(self)
        layout = QGridLayout(container)

        rut_label = QLabel("RUT")
        layout.addWidget(rut_label, 0, 0)
        rut = QLineEdit()
        rut.textChanged.connect(lambda: self.parent().to_uppercase(rut))
        if data:
            verified_rut = self.parent().verificar_rut(rut=data['rut'], show_messages=False)
            rut.setText(verified_rut['rut'])
            if verified_rut['errorWasFounded']:
                self.loaded_ruts_with_error.append(verified_rut['rut'])
            
        layout.addWidget(rut, 0, 1)
        rut.focusOutEvent = lambda event: self.on_rut_focus_out(rut,event)

        buscar_button = QPushButton("Buscar", self)
        buscar_button.clicked.connect(lambda: self.buscar_rut(rut, container))
        layout.addWidget(buscar_button, 0, 2)

        nac_label = QLabel("Nacionalidad:")
        layout.addWidget(nac_label, 1, 0)
        nac = QComboBox()
        nac.wheelEvent = lambda event: event.ignore()
        nac.addItems(['--', 'CHILENA', 'EXTRANJERA'])
        nac.setCurrentText(data['nac'])
        layout.addWidget(nac, 1, 1)

        tipo_label = QLabel("Tipo:")
        layout.addWidget(tipo_label, 1, 2)
        tipo = QComboBox()
        tipo.wheelEvent = lambda event: event.ignore()
        tipo.addItems(['--', 'NATURAL', 'JURIDICA'])
        tipo.setCurrentText(data['tipo'])
        layout.addWidget(tipo, 1, 3)

        genero_label = QLabel("Género:")
        layout.addWidget(genero_label, 2, 0)
        genero = QComboBox()
        genero.wheelEvent = lambda event: event.ignore()
        genero.addItems(['--', 'F', 'M'])
        genero.setCurrentText(data['genero'])
        layout.addWidget(genero, 2, 1)

        nombre_label = QLabel("Nombre:")
        layout.addWidget(nombre_label, 2, 2)
        nombre = QLineEdit()
        nombre.textChanged.connect(lambda: self.parent().to_uppercase(nombre))
        nombre.setText(data['nombre'])
        layout.addWidget(nombre, 2, 3)

        paterno_label = QLabel("Apellido Paterno:")
        layout.addWidget(paterno_label, 3, 0)
        paterno = QLineEdit()
        paterno.textChanged.connect(lambda: self.parent().to_uppercase(paterno))
        paterno.setText(data['paterno'])
        layout.addWidget(paterno, 3, 1)

        materno_label = QLabel("Apellido Materno:")
        layout.addWidget(materno_label, 3, 2)
        materno = QLineEdit()
        materno.textChanged.connect(lambda: self.parent().to_uppercase(materno))
        materno.setText(data['materno'])
        layout.addWidget(materno, 3, 3)

        delete_button = QPushButton("Borrar", self)
        delete_button.clicked.connect(lambda: self.delete_usuario(container, data['id']))
        layout.addWidget(delete_button, 4, 0, 1, 4)

        list_item = QListWidgetItem()
        list_item.setSizeHint(container.sizeHint())
        self.usuario_list.addItem(list_item)
        self.usuario_list.setItemWidget(list_item, container)

    def on_rut_focus_out(self, entry, event):
            try:
                formatted_rut=""
                text = entry.text()
                base_rut = re.sub(r'\D', '', text.strip().split("-")[0])

                if len(base_rut) > 8:
                    base_rut = base_rut[:8] 
                
                if len(base_rut)>=6:
                    dv = self.parent().calculate_dv(base_rut)
                    formatted_rut = f"{base_rut}-{dv}"
                #formatted_rut = text
                entry.blockSignals(True)
                entry.setText(formatted_rut)
                entry.blockSignals(False)
            except:
                pass
            QLineEdit.focusOutEvent(entry, event)

    def buscar_rut(self, rut_entry, container):
        rut = rut_entry.text().split("-")[0]
        try:
            success, data = self.parent().buscar_rut_api(rut)

            if success:
                container.layout().itemAtPosition(2, 3).widget().setText(data['Nombre'])
                container.layout().itemAtPosition(3, 1).widget().setText(data['Apa'])
                container.layout().itemAtPosition(3, 3).widget().setText(data['Ama'])
                container.layout().itemAtPosition(2, 1).widget().setCurrentText(data['G'])
                container.layout().itemAtPosition(1, 3).widget().setCurrentText(data['P'])
                container.layout().itemAtPosition(1, 1).widget().setCurrentText(data['NAC'])
            else:
                self.parent().show_message("Error", "Error al buscar RUT", "No se encontraron datos para el RUT ingresado.")
        
        except requests.RequestException as e:
            self.parent().show_message("Error", "Error al buscar RUT", f"Error de conexión: {str(e)}")



                
    def closeEvent(self, event):
        self.save_usuarios(True)
        super().closeEvent(event)



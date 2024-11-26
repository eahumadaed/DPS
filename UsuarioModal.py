from PyQt5.QtWidgets import QVBoxLayout, QFrame, QListWidget, QPushButton, QLabel, QGridLayout, QComboBox, QLineEdit, QDialog, QListWidgetItem
from PyQt5.QtCore import Qt
import requests
import re


class UsuarioModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionar Usuarios")
        self.setGeometry(200, 200, 700, 700)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.layout = QVBoxLayout()

        self.loaded_ruts_with_error = []
        
        self.usuario_list = QListWidget(self)
        self.layout.addWidget(self.usuario_list)

        self.add_button = QPushButton("Agregar", self)
        self.add_button.clicked.connect(self.add_usuario)
        self.layout.addWidget(self.add_button)
        self.add_button.setFocusPolicy(Qt.NoFocus)

        self.save_button = QPushButton("Guardar", self)
        self.save_button.clicked.connect(self.save_usuarios)
        self.save_button.setFocusPolicy(Qt.NoFocus)
        self.layout.addWidget(self.save_button)
        
        self.focus_out_button = QPushButton("")
        self.focus_out_button.hide()
        self.layout.addWidget(self.focus_out_button)

        self.setLayout(self.layout)

        self.load_usuarios()
        
    
    def validate_fields(self):
        def add_wrong_field(wrong_field):
            wrong_fields.append(wrong_field)
        
        def get_value(user, key):
            value = user[key]['value']
            if isinstance(value, str):
                value = value.replace("\n", " ").strip()
            if value == "--":
                value = ""
            return value

        def add_red_borders():
            entries = []
            wrong_entries = []
            for user in usuarios_data:
                user_values = list(user.values())
                for value in user_values:
                    entries.append(value['entry'])
            
            for field in wrong_fields:
                wrong_entries.append(field['entry'])
            
            for entry in entries:
                if entry in wrong_entries:
                    entry.setStyleSheet("border-bottom: 2px solid red; border-radius: 0px;")
                else:
                    entry.setStyleSheet("")
                    
        usuarios_data = []
        
        wrong_fields = []
        
        ruts = []
        ruts_repetidos = []
                    
        for i in range(self.usuario_list.count()):
            container = self.usuario_list.itemWidget(self.usuario_list.item(i))
            data = {}
            for j in range(container.layout().count()):
                widget = container.layout().itemAt(j).widget()
                if isinstance(widget, QLineEdit):
                    label = container.layout().itemAt(j - 1).widget().text()
                    if "RUT" in label:
                        data['RUT'] = {"value": widget.text(), "entry": widget}
                    elif "Nombre" in label:
                        data['NOMBRE'] = {"value": widget.text(), "entry": widget}
                    elif "Apellido Paterno" in label:
                        data['PATERNO'] = {"value": widget.text(), "entry": widget}
                    elif "Apellido Materno" in label:
                        data['MATERNO'] = {"value": widget.text(), "entry": widget}
                elif isinstance(widget, QComboBox):
                    label = container.layout().itemAt(j - 1).widget().text()
                    if "Nacionalidad" in label:
                        data['NAC'] = {"value": widget.currentText(), "entry": widget}
                    elif "Tipo" in label:
                        data['TIPO'] = {"value": widget.currentText(), "entry": widget}
                    elif "Género" in label:
                        data['GENERO'] = {"value": widget.currentText(), "entry": widget}
            usuarios_data.append(data)
            
            
        for user in usuarios_data:
            obligatorios = ["TIPO", "RUT", "NOMBRE"]
            for tipo_campo in obligatorios:
                if not get_value(user, tipo_campo):
                    add_wrong_field(user[tipo_campo])
            tipo = get_value(user, 'TIPO')
            if tipo:
                if tipo=="NATURAL":
                    if not get_value(user, "NAC"): add_wrong_field(user['NAC'])
                    if not get_value(user, "GENERO"): add_wrong_field(user['GENERO'])
                    if not get_value(user, "PATERNO"): add_wrong_field(user['PATERNO'])
                elif tipo=="JURIDICA":
                    if get_value(user, "NAC"): add_wrong_field(user['NAC'])
                    if get_value(user, "GENERO"): add_wrong_field(user['GENERO'])
                    if get_value(user, "PATERNO"): add_wrong_field(user['PATERNO'])
                    if get_value(user, "MATERNO"): add_wrong_field(user['MATERNO'])
            rut = get_value(user, "RUT")
            if rut:
                if rut in ruts:
                    ruts_repetidos.append(rut)
                ruts.append(rut)
                
            rut_parent = self.parent().rut_entry.text()
            
            if rut_parent and rut_parent in ruts:
                ruts_repetidos.append(rut)
        
        add_red_borders()
        
        return wrong_fields, ruts_repetidos
        

    def add_usuario(self, data=None):
        container = QFrame(self)
        layout = QGridLayout(container)

        rut_label = QLabel("RUT")
        layout.addWidget(rut_label, 0, 0)
        rut = QLineEdit()
        rut.focusInEvent = self.wrap_focus_in_event(rut, rut.focusInEvent)
        rut.focusOutEvent = self.wrap_focus_out_event(rut.focusOutEvent)
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
        nac.focusInEvent = self.wrap_focus_in_event(nac, nac.focusInEvent)
        nac.currentIndexChanged.connect(lambda: self.validate_fields())
        nac.focusOutEvent = self.wrap_focus_out_event(nac.focusOutEvent)
        nac.wheelEvent = lambda event: event.ignore()
        nac.addItems(['--', 'CHILENA', 'EXTRANJERA'])
        if data:
            nac.setCurrentText(data['nac'])
        layout.addWidget(nac, 1, 1)

        tipo_label = QLabel("Tipo:")
        layout.addWidget(tipo_label, 1, 2)
        tipo = QComboBox()
        tipo.focusInEvent = self.wrap_focus_in_event(tipo, tipo.focusInEvent)
        tipo.currentIndexChanged.connect(lambda: self.validate_fields())
        tipo.focusOutEvent = self.wrap_focus_out_event(tipo.focusOutEvent)
        tipo.wheelEvent = lambda event: event.ignore()
        tipo.addItems(['--', 'NATURAL', 'JURIDICA'])
        if data:
            tipo.setCurrentText(data['tipo'])
        layout.addWidget(tipo, 1, 3)

        genero_label = QLabel("Género:")
        layout.addWidget(genero_label, 2, 0)
        genero = QComboBox()
        genero.focusInEvent = self.wrap_focus_in_event(genero, genero.focusInEvent)
        genero.currentIndexChanged.connect(lambda: self.validate_fields())
        genero.focusOutEvent = self.wrap_focus_out_event(genero.focusOutEvent)
        genero.wheelEvent = lambda event: event.ignore()
        genero.addItems(['--', 'F', 'M'])
        if data:
            genero.setCurrentText(data['genero'])
        layout.addWidget(genero, 2, 1)

        nombre_label = QLabel("Nombre:")
        layout.addWidget(nombre_label, 2, 2)
        nombre = QLineEdit()
        nombre.focusInEvent = self.wrap_focus_in_event(nombre, nombre.focusInEvent)
        nombre.focusOutEvent = self.wrap_focus_out_event(nombre.focusOutEvent)
        nombre.textChanged.connect(lambda: self.parent().to_uppercase(nombre))
        nombre.textChanged.connect(lambda: self.parent().add_nombre_item(nombre))
        nombre.setCompleter(self.parent().nombres_completer)
        nombre.returnPressed.connect(lambda: self.parent().select_completion("NOMBRE"))
        if data:
            nombre.setText(data['nombre'])
        layout.addWidget(nombre, 2, 3)

        paterno_label = QLabel("Apellido Paterno:")
        layout.addWidget(paterno_label, 3, 0)
        paterno = QLineEdit()
        paterno.focusInEvent = self.wrap_focus_in_event(paterno, paterno.focusInEvent)
        paterno.focusOutEvent = self.wrap_focus_out_event(paterno.focusOutEvent)
        paterno.textChanged.connect(lambda: self.parent().to_uppercase(paterno))
        paterno.textChanged.connect(lambda: self.parent().add_apellido_item(paterno))
        paterno.setCompleter(self.parent().apellido_completer)
        paterno.returnPressed.connect(lambda: self.parent().select_completion("PATERNO"))
        if data:
            paterno.setText(data['paterno'])
        layout.addWidget(paterno, 3, 1)

        materno_label = QLabel("Apellido Materno:")
        layout.addWidget(materno_label, 3, 2)
        materno = QLineEdit()
        materno.focusInEvent = self.wrap_focus_in_event(materno, materno.focusInEvent)
        materno.focusOutEvent = self.wrap_focus_out_event(materno.focusOutEvent)
        materno.textChanged.connect(lambda: self.parent().to_uppercase(materno))
        materno.textChanged.connect(lambda: self.parent().add_apellido_item(materno))
        materno.setCompleter(self.parent().apellido_completer)
        materno.returnPressed.connect(lambda: self.parent().select_completion("MATERNO"))
        if data:
            materno.setText(data['materno'])
        layout.addWidget(materno, 3, 3)

        delete_button = QPushButton("Borrar", self)
        delete_button.setFocusPolicy(Qt.NoFocus)
        delete_button.clicked.connect(lambda: self.delete_usuario(container, data.get('id') if data else None))
        layout.addWidget(delete_button, 4, 0, 1, 4)

        list_item = QListWidgetItem()
        list_item.setSizeHint(container.sizeHint())
        self.usuario_list.addItem(list_item)
        self.usuario_list.setItemWidget(list_item, container)
        self.validate_fields()

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
    
    def recordar_usaurios(self, users_data):
        for user in users_data:
            self.parent().recordar_usuario(user, True)
                
    def save_usuarios(self, silenc=False):
        if not self.parent().current_formulario_id:
            self.parent().show_message("Error", "Guardar", "Seleccione un trabajo antes de guardar usuarios.")
            return
        wrong_fields, ruts_repetidos  = self.validate_fields()
        if wrong_fields or ruts_repetidos:
            if wrong_fields and ruts_repetidos:
                message = f"Error en uno o más campos ingresados\n\nRuts duplicados:"
                for rut in ruts_repetidos:
                    message += f"\n  - {rut}"
            elif wrong_fields:
                message = "Error en uno o más campos ingresados"
            elif ruts_repetidos:
                message = "Ruts duplicados:"
                for rut in ruts_repetidos:
                    message += f"\n  - {rut}"
            self.parent().show_message("Error", "Campos inválidos", message)
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
            
        self.recordar_usaurios(usuarios_data)

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
        rut.focusInEvent = self.wrap_focus_in_event(rut, rut.focusInEvent)
        rut.focusOutEvent = self.wrap_focus_out_event(rut.focusOutEvent)
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
        nac.focusInEvent = self.wrap_focus_in_event(nac, nac.focusInEvent)
        nac.currentIndexChanged.connect(lambda: self.validate_fields())
        nac.focusOutEvent = self.wrap_focus_out_event(nac.focusOutEvent)
        nac.wheelEvent = lambda event: event.ignore()
        nac.addItems(['--', 'CHILENA', 'EXTRANJERA'])
        nac.setCurrentText(data['nac'])
        layout.addWidget(nac, 1, 1)

        tipo_label = QLabel("Tipo:")
        layout.addWidget(tipo_label, 1, 2)
        tipo = QComboBox()
        tipo.focusInEvent = self.wrap_focus_in_event(tipo, tipo.focusInEvent)
        tipo.currentIndexChanged.connect(lambda: self.validate_fields())
        tipo.focusOutEvent = self.wrap_focus_out_event(tipo.focusOutEvent)
        tipo.wheelEvent = lambda event: event.ignore()
        tipo.addItems(['--', 'NATURAL', 'JURIDICA'])
        tipo.setCurrentText(data['tipo'])
        layout.addWidget(tipo, 1, 3)

        genero_label = QLabel("Género:")
        layout.addWidget(genero_label, 2, 0)
        genero = QComboBox()
        genero.focusInEvent = self.wrap_focus_in_event(genero, genero.focusInEvent)
        genero.currentIndexChanged.connect(lambda: self.validate_fields())
        genero.focusOutEvent = self.wrap_focus_out_event(genero.focusOutEvent)
        genero.wheelEvent = lambda event: event.ignore()
        genero.addItems(['--', 'F', 'M'])
        genero.setCurrentText(data['genero'])
        layout.addWidget(genero, 2, 1)

        nombre_label = QLabel("Nombre:")
        layout.addWidget(nombre_label, 2, 2)
        nombre = QLineEdit()
        nombre.focusInEvent = self.wrap_focus_in_event(nombre, nombre.focusInEvent)
        nombre.focusOutEvent = self.wrap_focus_out_event(nombre.focusOutEvent)
        nombre.textChanged.connect(lambda: self.parent().to_uppercase(nombre))
        nombre.textChanged.connect(lambda: self.parent().add_nombre_item(nombre))
        nombre.setCompleter(self.parent().nombres_completer)
        nombre.returnPressed.connect(lambda: self.parent().select_completion("NOMBRE"))
        nombre.setText(data['nombre'])
        layout.addWidget(nombre, 2, 3)

        paterno_label = QLabel("Apellido Paterno:")
        layout.addWidget(paterno_label, 3, 0)
        paterno = QLineEdit()
        paterno.focusInEvent = self.wrap_focus_in_event(paterno, paterno.focusInEvent)
        paterno.focusOutEvent = self.wrap_focus_out_event(paterno.focusOutEvent)
        paterno.textChanged.connect(lambda: self.parent().to_uppercase(paterno))
        paterno.textChanged.connect(lambda: self.parent().add_apellido_item(paterno))
        paterno.setCompleter(self.parent().apellido_completer)
        paterno.returnPressed.connect(lambda: self.parent().select_completion("PATERNO"))
        paterno.setText(data['paterno'])
        layout.addWidget(paterno, 3, 1)

        materno_label = QLabel("Apellido Materno:")
        layout.addWidget(materno_label, 3, 2)
        materno = QLineEdit()
        materno.focusInEvent = self.wrap_focus_in_event(materno, materno.focusInEvent)
        materno.focusOutEvent = self.wrap_focus_out_event(materno.focusOutEvent)
        materno.textChanged.connect(lambda: self.parent().to_uppercase(materno))
        materno.textChanged.connect(lambda: self.parent().add_apellido_item(materno))
        materno.setCompleter(self.parent().apellido_completer)
        materno.returnPressed.connect(lambda: self.parent().select_completion("MATERNO"))
        materno.setText(data['materno'])
        layout.addWidget(materno, 3, 3)

        delete_button = QPushButton("Borrar", self)
        delete_button.setFocusPolicy(Qt.NoFocus)
        delete_button.clicked.connect(lambda: self.delete_usuario(container, data['id']))
        layout.addWidget(delete_button, 4, 0, 1, 4)

        list_item = QListWidgetItem()
        list_item.setSizeHint(container.sizeHint())
        self.usuario_list.addItem(list_item)
        self.usuario_list.setItemWidget(list_item, container)
        self.validate_fields()

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
        rut =  rut_entry.text().strip()
        if rut and rut in list(self.parent().users_list.keys()):
            data = self.parent().users_list[rut]
            print(data)
            
            container.layout().itemAtPosition(2, 3).widget().setText(data['NOMBRE'])
            container.layout().itemAtPosition(3, 1).widget().setText(data['PATERNO'])
            container.layout().itemAtPosition(3, 3).widget().setText(data['MATERNO'])
            container.layout().itemAtPosition(2, 1).widget().setCurrentText(data['GENERO'])
            container.layout().itemAtPosition(1, 3).widget().setCurrentText(data['TIPO'])
            container.layout().itemAtPosition(1, 1).widget().setCurrentText(data['NAC'])
            return
        
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
            
    def wrap_focus_in_event(self, entry, original_event):
        def wrapped_event(event):
            entry.setStyleSheet("")
            return original_event(event)
        return wrapped_event

    def wrap_focus_out_event(self, original_event):
        def wrapped_event(event):
            self.validate_fields()  # Ejecutar validación
            return original_event(event)  # Llamar al evento original
        return wrapped_event
    
    def closeEvent(self, event):
        self.save_usuarios(True)
        super().closeEvent(event)
        
        



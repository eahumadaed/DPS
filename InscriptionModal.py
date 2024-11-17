from PyQt5.QtWidgets import QVBoxLayout, QCompleter, QFrame, QListWidget, QPushButton, QLabel, QLineEdit, QGridLayout, QComboBox, QCheckBox, QDialog, QListWidgetItem
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt, QStringListModel
import requests
from comunas import Comunas_list

class InscriptionModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionar Inscripciones")
        self.setGeometry(200, 200, 700, 700)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        self.layout = QVBoxLayout()

        self.inscription_list = QListWidget(self)
        self.layout.addWidget(self.inscription_list)

        self.add_button = QPushButton("Agregar", self)
        self.add_button.clicked.connect(self.add_inscription)
        self.layout.addWidget(self.add_button)

        self.save_button = QPushButton("Guardar", self)
        self.save_button.clicked.connect(self.save_inscriptions)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)
        self.load_inscriptions()
    
    def validate_fields(self):
        def add_wrong_field(wrong_field):
            wrong_fields.append(wrong_field)
        
        def get_value(inscription, key):
            value = inscription[key]['value']
            if isinstance(value, str):
                value = value.replace("\n", " ").strip()
            if value == "--":
                value = ""
            return value

        def add_red_borders():
            entries = []
            wrong_entries = []
            for inscription in inscriptions_data:
                inscription_values = list(inscription.values())
                for value in inscription_values:
                    entries.append(value['entry'])
            
            for field in wrong_fields:
                wrong_entries.append(field['entry'])
            
            for entry in entries:
                if entry in wrong_entries:
                    entry.setStyleSheet("border-bottom: 2px solid red; border-radius: 0px;")
                else:
                    entry.setStyleSheet("")
                    
        inscriptions_data= []
        
        wrong_fields = []
        
        inscripciones = []
        inscripciones_repetidas = []
        
        for i in range(self.inscription_list.count()):
            container = self.inscription_list.itemWidget(self.inscription_list.item(i))
            cbr_entry = container.layout().itemAt(6).widget()
            foja_entry = container.layout().itemAt(8).widget()
            v_entry = container.layout().itemAt(10).widget()
            numero_entry = container.layout().itemAt(12).widget()
            anio_entry = container.layout().itemAt(14).widget()
            
            data = {
                'cbr': {'entry':cbr_entry, 'value':cbr_entry.text()},
                'foja': {'entry':foja_entry, 'value':foja_entry.text()},
                'numero': {'entry':numero_entry, 'value':numero_entry.text()},
                'anio': {'entry':anio_entry, 'value':anio_entry.text()}
            }

            inscriptions_data.append(data)
        
        for inscription in inscriptions_data:
            obligatorios = list(data.keys())
            for tipo_campo in obligatorios:
                if not get_value(inscription, tipo_campo):
                    add_wrong_field(inscription[tipo_campo])
            
            inscription_data = {}
            inscription_keys = list(inscription.keys())
            for key in inscription_keys:
                inscription_data[key] = inscription[key]['value']
                
            if inscription_data in inscripciones:
                inscripciones_repetidas.append(f"{inscription_data['cbr']} {inscription_data['anio']} {inscription_data['numero']} {inscription_data['foja']}")
            inscripciones.append(inscription_data)

            for i in inscripciones_repetidas:
                print(i)
                
        add_red_borders()
        return wrong_fields, inscripciones_repetidas
            

    def add_inscription(self, data=None):
        container = QFrame(self)
        layout = QGridLayout(container)

        id_hidden = QLineEdit()
        id_hidden.setVisible(False)
        if data and 'id' in data:
            id_hidden.setText(str(data['id']))
        layout.addWidget(id_hidden, 0, 0)

        f_inscripcion_label = QLabel("Fecha de Inscripción:")
        layout.addWidget(f_inscripcion_label, 1, 0)
        
        f_inscripcion = QLineEdit(self)
        f_inscripcion.setPlaceholderText("dd/mm/yyyy")
        if data:
            f_inscripcion.setText(data['f_inscripcion'])
        
        f_inscripcion.textChanged.connect(lambda: self.parent().auto_format_date(f_inscripcion))

        layout.addWidget(f_inscripcion, 1, 1)

        comuna_label = QLabel("Comuna:")
        layout.addWidget(comuna_label, 2, 0)
        comuna = QComboBox()
        comuna.wheelEvent = lambda event: event.ignore()
        comuna.addItems(Comunas_list)
        comuna.currentIndexChanged.connect(
                    lambda index: self.set_preferred_value(comuna.currentText())
                )
        if data:
            comuna.setCurrentText(data['comuna'])
        layout.addWidget(comuna, 2, 1)

        self.comunas_formatted_list = [
                    comuna.upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
                    for comuna in Comunas_list
                ]
        
        self.completer = QCompleter(self.comunas_formatted_list)
        self.completer.setCompletionMode(QCompleter.InlineCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        cbr_label = QLabel("CBR:")
        layout.addWidget(cbr_label, 3, 0)
        cbr = QLineEdit()
        cbr.focusOutEvent = self.wrap_focus_out_event(cbr.focusOutEvent)
        cbr.focusInEvent = self.wrap_focus_in_event(cbr, cbr.focusInEvent)
        cbr.setCompleter(self.completer)
        cbr.returnPressed.connect(self.select_completion)
        cbr.textChanged.connect(lambda: self.parent().to_uppercase(cbr))
        if data:
            cbr.setText(data['cbr'])
        layout.addWidget(cbr, 3, 1)

        foja_label = QLabel("Foja:")
        layout.addWidget(foja_label, 4, 0)
        foja = QLineEdit()
        foja.focusOutEvent = self.wrap_focus_out_event(foja.focusOutEvent)
        foja.focusInEvent = self.wrap_focus_in_event(foja, foja.focusInEvent)
        foja.setValidator(QIntValidator())
        if data:
            foja.setText(data['foja'])
        layout.addWidget(foja, 4, 1)

        v_label = QLabel("V:")
        layout.addWidget(v_label, 5, 0)
        v = QCheckBox()
        if data:
            v.setChecked(data['v'].lower() in ['true', '1'])
        layout.addWidget(v, 5, 1)

        numero_label = QLabel("Número:")
        layout.addWidget(numero_label, 6, 0)
        numero = QLineEdit()
        numero.focusOutEvent = self.wrap_focus_out_event(numero.focusOutEvent)
        numero.focusInEvent = self.wrap_focus_in_event(numero, numero.focusInEvent)
        numero.setValidator(QIntValidator())
        if data:
            numero.setText(data['numero'])
        layout.addWidget(numero, 6, 1)

        anio_label = QLabel("Año:")
        layout.addWidget(anio_label, 7, 0)
        anio = QLineEdit()
        anio.focusOutEvent = self.wrap_focus_out_event(anio.focusOutEvent)
        anio.focusInEvent = self.wrap_focus_in_event(anio, anio.focusInEvent)
        anio.setValidator(QIntValidator())
        if data:
            anio.setText(data['anio'])
        layout.addWidget(anio, 7, 1)

        delete_button = QPushButton("Borrar", self)
        delete_button.clicked.connect(lambda: self.delete_inscription(container, data.get('id') if data else None))
        layout.addWidget(delete_button, 8, 0, 1, 2)

        list_item = QListWidgetItem()
        list_item.setSizeHint(container.sizeHint())
        self.inscription_list.addItem(list_item)
        self.inscription_list.setItemWidget(list_item, container)
        self.validate_fields()
        
    def select_completion(self):
        if self.completer.completionCount() > 0:
            self.sender().setText(self.completer.currentCompletion())
        self.sender().focusNextPrevChild(True)
        
    def update_completer(self, preferredValue):
        updated_list = [preferredValue] + [comuna for comuna in self.comunas_formatted_list if comuna != preferredValue]

        model = QStringListModel(updated_list)
        self.completer.setModel(model)
            
    def set_preferred_value(self, value):
        # Establecer el valor preferido en la instancia
        self.preferredValue = value.upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
        self.update_completer(self.preferredValue)


    def delete_inscription(self, container, inscription_id=None):
        if inscription_id:
            try:
                response = requests.post(f'{self.parent().api_base_url}deleteInscripcion', json={'id': inscription_id})
                response.raise_for_status()
                result = response.json()

                if result.get('message') == 'Inscripción eliminada correctamente':
                    self.remove_inscription_from_list(container)
                    self.parent().show_message("Info", "Eliminar", "Inscripción eliminada correctamente.")
                else:
                    self.parent().show_message("Error", "Eliminar", result.get('message', 'Error desconocido'))

            except requests.RequestException as e:
                self.parent().show_message("Error", "Eliminar", str(e))
        else:
            self.remove_inscription_from_list(container)

    def remove_inscription_from_list(self, container):
        for i in range(self.inscription_list.count()):
            item = self.inscription_list.item(i)
            if self.inscription_list.itemWidget(item) == container:
                self.inscription_list.takeItem(i)
                break

    def save_inscriptions(self, silence=False):
        wrong_fields, inscripciones_repetidas = self.validate_fields()
        
        if not self.parent().current_formulario_id:
            self.parent().show_message("Error", "Guardar", "Seleccione un trabajo antes de guardar inscripciones.")
            return
        if wrong_fields:
             self.parent().show_message("Error", "Campos inválidos", "Error en uno o más campos ingresados")
             return
        elif inscripciones_repetidas:
            message = "Inscripciones duplicadas:"
            for inscripcion in inscripciones_repetidas:
                message += f"\n - {inscripcion}"
            
            self.parent().show_message("Error", "Campos inválidos", message)
            return

        inscriptions_data = []
        for i in range(self.inscription_list.count()):
            container = self.inscription_list.itemWidget(self.inscription_list.item(i))
            data = {
                'id': container.layout().itemAt(0).widget().text() or None,
                'f_inscripcion': container.layout().itemAt(2).widget().text(),
                'comuna': container.layout().itemAt(4).widget().currentText(),
                'cbr': container.layout().itemAt(6).widget().text(),
                'foja': container.layout().itemAt(8).widget().text(),
                'v': container.layout().itemAt(10).widget().isChecked(),
                'numero': container.layout().itemAt(12).widget().text(),
                'anio': container.layout().itemAt(14).widget().text()
            }
            inscriptions_data.append(data)

        try:
            response = requests.post(f'{self.parent().api_base_url}saveInscriptions', json={
                'trabajo_id': self.parent().current_trabajo_id,
                'formulario_id': self.parent().current_formulario_id,
                'inscriptions': inscriptions_data
            })
            response.raise_for_status()
            if not silence:
                self.accept()  # Cierra el modal al completar el guardado
                self.deleteLater() 
                self.parent().show_message("Info", "Guardar", "Inscripciones guardadas exitosamente.")

            print("Inscripciones guardadas:", inscriptions_data)
        except requests.RequestException as e:
            if not silence:
                self.parent().show_message("Error", "Error al guardar inscripciones", str(e))
            print(f"Error al guardar inscripciones: {e}")
            
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

    def load_inscriptions(self):
        if not self.parent().current_formulario_id:
            return

        try:
            response = requests.get(f'{self.parent().api_base_url}getInscriptions&formulario_id={self.parent().current_formulario_id}')
            response.raise_for_status()
            inscriptions_data = response.json()
            if isinstance(inscriptions_data, list):
                for inscription in inscriptions_data:
                    self.add_inscription(inscription)
        except requests.RequestException as e:
            print(f"Error al cargar inscripciones: {e}")
            self.parent().show_message("Error", "Error al cargar inscripciones", str(e))

    def closeEvent(self, event):
        self.save_inscriptions(silence=True)
        super().closeEvent(event)

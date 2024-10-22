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
        else:
            f_inscripcion.setText("--/--/----")
        
        f_inscripcion.textChanged.connect(self.auto_format_date)

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
        cbr.setCompleter(self.completer)
        cbr.returnPressed.connect(self.select_completion)
        cbr.textChanged.connect(lambda: self.parent().to_uppercase(cbr))
        if data:
            cbr.setText(data['cbr'])
        layout.addWidget(cbr, 3, 1)

        foja_label = QLabel("Foja:")
        layout.addWidget(foja_label, 4, 0)
        foja = QLineEdit()
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
        numero.setValidator(QIntValidator())
        if data:
            numero.setText(data['numero'])
        layout.addWidget(numero, 6, 1)

        anio_label = QLabel("Año:")
        layout.addWidget(anio_label, 7, 0)
        anio = QLineEdit()
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

    def auto_format_date(self, text):
        clean_text = text.replace("/", "")
        
        print(f"Texto ingresado: {text}")
        print(f"Texto limpio: {clean_text}")
        
        if len(clean_text) > 8:
            clean_text = clean_text[:8]
        
        formatted_text = ""
        cursor_position = self.sender().cursorPosition()
        print(f"Posición inicial del cursor: {cursor_position}")
        
        if len(clean_text) >= 2:
            formatted_text += clean_text[:2] + "/"
        else:
            formatted_text += clean_text
        
        if len(clean_text) >= 4:
            formatted_text += clean_text[2:4] + "/"
        elif len(clean_text) > 2:
            formatted_text += clean_text[2:4]
        
        if len(clean_text) > 4:
            formatted_text += clean_text[4:]
        
        print(f"Texto formateado: {formatted_text}")
        
        prev_length = len(self.sender().text())
        print(f"Longitud anterior del texto: {prev_length}")
        
        self.sender().blockSignals(True)
        self.sender().setText(formatted_text)
        self.sender().blockSignals(False)
        
        if len(formatted_text) > prev_length:
            cursor_position += 1
        elif len(formatted_text) < prev_length:
            cursor_position -= 1
        
        print(f"Posición ajustada del cursor: {cursor_position}")
        
        self.sender().setCursorPosition(cursor_position)
        print(f"Posición final del cursor: {self.sender().cursorPosition()}")


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
        if not self.parent().current_formulario_id:
            self.parent().show_message("Error", "Guardar", "Seleccione un trabajo antes de guardar inscripciones.")
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

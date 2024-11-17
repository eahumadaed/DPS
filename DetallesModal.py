from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QFrame, QGridLayout, QLabel, QComboBox, QLineEdit, QListWidgetItem, QTextEdit
import requests
from PyQt5.QtCore import Qt

class DetallesModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionar Detalles")
        self.setGeometry(200, 200, 700, 700)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.layout = QVBoxLayout()

        self.detalles_list = QListWidget(self)
        self.layout.addWidget(self.detalles_list)

        self.add_button = QPushButton("Agregar Detalle", self)
        self.add_button.clicked.connect(self.add_detalle)
        self.add_button.setFocusPolicy(Qt.NoFocus)
        self.layout.addWidget(self.add_button)

        self.save_button = QPushButton("Guardar", self)
        self.save_button.clicked.connect(self.save_detalles)
        self.save_button.setFocusPolicy(Qt.NoFocus)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)
        self.load_detalles()
    
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
            for detalle in detalles_data:
                detalles_values = list(detalle.values())
                for value in detalles_values:
                    entries.append(value['entry'])
            
            for field in wrong_fields:
                wrong_entries.append(field['entry'])
            
            for entry in entries:
                if entry in wrong_entries:
                    entry.setStyleSheet("border-bottom: 2px solid red; border-radius: 0px;")
                else:
                    entry.setStyleSheet("")
        
        wrong_fields = []
        
        detalles_data = []
        for i in range(self.detalles_list.count()):
            container = self.detalles_list.itemWidget(self.detalles_list.item(i))
            referencia_entry = container.layout().itemAt(20).widget()
            data = {
                'referencia': {"entry": referencia_entry, "value": referencia_entry.toPlainText()},
            }

            detalles_data.append(data)
            
        for detalle in detalles_data:
            obs_exeptions = ["PERFECTO", "PERFECCIONADO AL MARGEN", "SIN RUT", "NO SE LEE", "NO CARGA"]
            obs_value = self.parent().obs_entry.currentText()
            if not get_value(detalle, "referencia") and obs_value not in obs_exeptions:
                    add_wrong_field(detalle["referencia"])
        add_red_borders()
        
        return wrong_fields
                    

    def add_detalle(self, data=None):
        container = QFrame(self)
        layout = QGridLayout(container)

        # ID oculto
        id_hidden = QLineEdit()
        id_hidden.setVisible(False)
        if data and 'id' in data:
            id_hidden.setText(str(data['id']))
        layout.addWidget(id_hidden, 0, 0)

        # Ejercicio
        ejercicio_label = QLabel("Ejercicio del Derecho:")
        layout.addWidget(ejercicio_label, 1, 0)
        ejercicio = QComboBox()
        ejercicio.wheelEvent = lambda event: event.ignore()
        ejercicio.addItems(['--','PERMANENTE Y CONTINUO', 'EVENTUAL Y CONTINUO','PERM. Y CONT. Y PROVICIONALES','SIN EJERCICIO','PERM. Y DISC. Y PROVICIONALES','PERM Y ALTER. Y PROVICIONALES','EVENTUAL Y DISCONTINUO','EVENTUAL Y ALTERNADO','PERMANENTE Y DISCONTINUO','PERMANENTE Y ALTERNADO'])
        if data:
            ejercicio.setCurrentText(data.get('ejercicio', '--'))
        layout.addWidget(ejercicio, 1, 1)

        # Caudal
        metodo_label = QLabel("Método de Extracción:")
        layout.addWidget(metodo_label, 2, 0)
        metodo = QComboBox()
        metodo.wheelEvent = lambda event: event.ignore()
        metodo.addItems(['--','MECANICA','GRAVITACIONAL','MECANICA Y/O GRAVITACIONAL'])
        if data:
            metodo.setCurrentText(data.get('metodo', '--'))
        layout.addWidget(metodo, 2, 1)

        cantidad_label = QLabel("Cantidad:")
        layout.addWidget(cantidad_label, 3, 0)
        cantidad = QLineEdit()
        cantidad.textChanged.connect(lambda: self.parent().to_uppercase(cantidad))
        if data:
            cantidad.setText(data.get('cantidad', ''))
        layout.addWidget(cantidad, 3, 1)

        unidad_label = QLabel("Unidad:")
        layout.addWidget(unidad_label, 4, 0)
        unidad = QComboBox()
        unidad.wheelEvent = lambda event: event.ignore()
        unidad.addItems(['--','LT/S','M3/S','MM3/AÑO','M3/AÑO','LT/MIN','M3/H','LT/H','M3/MES','ACCIONES','M3/DIA','M3/MIN','LT/DIA','REGADORES','CUADRAS','TEJAS','HORAS TURNO','%','PARTES','LT/MES','MMM3/MES','M3/HA/MES', 'ETC'])
        if data:
            unidad.setCurrentText(data.get('unidad', '--'))
        layout.addWidget(unidad, 4, 1)

        # UTM NORTE
        utm_norte_label = QLabel("UTM Norte:")
        layout.addWidget(utm_norte_label, 5, 0)
        utm_norte = QLineEdit()
        utm_norte.textChanged.connect(lambda: self.parent().to_uppercase(utm_norte))
        if data:
            utm_norte.setText(data.get('utm_norte', ''))
        layout.addWidget(utm_norte, 5, 1)

        # UTM ESTE
        utm_este_label = QLabel("UTM Este:")
        layout.addWidget(utm_este_label, 6, 0)
        utm_este = QLineEdit()
        utm_este.textChanged.connect(lambda: self.parent().to_uppercase(utm_este))
        if data:
            utm_este.setText(data.get('utm_este', ''))
        layout.addWidget(utm_este, 6, 1)

        # UNIDAD UTM
        unidad_utm_label = QLabel("Unidad UTM:")
        layout.addWidget(unidad_utm_label, 7, 0)
        unidad_utm = QComboBox()
        unidad_utm.wheelEvent = lambda event: event.ignore()
        unidad_utm.addItems(['--','KM', 'MTS'])
        if data:
            unidad_utm.setCurrentText(data.get('unidad_utm', '--'))
        layout.addWidget(unidad_utm, 7, 1)

        # HUSO
        huso_label = QLabel("Huso:")
        layout.addWidget(huso_label, 8, 0)
        huso = QComboBox()
        huso.wheelEvent = lambda event: event.ignore()
        huso.addItems(['--','18', '19'])
        if data:
            huso.setCurrentText(data.get('huso', '--'))
        layout.addWidget(huso, 8, 1)

        # DATUM
        datum_label = QLabel("Datum:")
        layout.addWidget(datum_label, 9, 0)
        datum = QComboBox()
        datum.wheelEvent = lambda event: event.ignore()
        datum.addItems(['--','56', '69','84'])
        if data:
            datum.setCurrentText(data.get('datum', '--'))
        layout.addWidget(datum, 9, 1)
        
        # Referencias
        referencia_label = QLabel("Puntos Conocidos de Captación:")
        layout.addWidget(referencia_label, 10, 0)
        referencia = QTextEdit()
        referencia.focusOutEvent = self.wrap_focus_out_event(referencia.focusOutEvent)
        referencia.focusInEvent = self.wrap_focus_in_event(referencia, referencia.focusInEvent)
        
        referencia.setFixedHeight(100)
        if data:
            referencia.setPlainText(data.get('referencia', ''))
        
        referencia.textChanged.connect(lambda: self.parent().to_uppercase(referencia))
        layout.addWidget(referencia, 10, 1,6,1)

        delete_button = QPushButton("Borrar", self)
        delete_button.clicked.connect(lambda: self.delete_detalle(container, data.get('id') if data else None))
        layout.addWidget(delete_button, 16, 0, 1, 2)

        list_item = QListWidgetItem()
        list_item.setSizeHint(container.sizeHint())
        self.detalles_list.addItem(list_item)
        self.detalles_list.setItemWidget(list_item, container)
        self.validate_fields()

    def delete_detalle(self, container, detalle_id=None):
        if detalle_id:
            try:
                response = requests.post(f'{self.parent().api_base_url}deleteDetalle', json={'id': detalle_id})
                response.raise_for_status()
                result = response.json()

                if result.get('message') == 'Detalle eliminado correctamente':
                    self.remove_detalle_from_list(container)
                    self.parent().show_message("Info", "Eliminar", "Detalle eliminado correctamente.")
                else:
                    self.parent().show_message("Error", "Eliminar", result.get('message', 'Error desconocido'))

            except requests.RequestException as e:
                self.parent().show_message("Error", "Eliminar", str(e))
        else:
            self.remove_detalle_from_list(container)

    def remove_detalle_from_list(self, container):
        for i in range(self.detalles_list.count()):
            item = self.detalles_list.item(i)
            if self.detalles_list.itemWidget(item) == container:
                self.detalles_list.takeItem(i)
                break

    def save_detalles(self, silence=False):
        if not self.parent().current_formulario_id:
            self.parent().show_message("Error", "Guardar", "Seleccione un trabajo antes de guardar detalles.")
            return
        wrong_fields = self.validate_fields()
        if wrong_fields:
            self.parent().show_message("Error", "Guardar", "Debe añadir puntos de captación")
            return

        detalles_data = []
        for i in range(self.detalles_list.count()):
            container = self.detalles_list.itemWidget(self.detalles_list.item(i))
            data = {
                'id': container.layout().itemAt(0).widget().text() or None,
                'ejercicio': container.layout().itemAt(2).widget().currentText(),
                'metodo': container.layout().itemAt(4).widget().currentText(),
                'cantidad': container.layout().itemAt(6).widget().text(),
                'unidad': container.layout().itemAt(8).widget().currentText(),
                'utm_norte': container.layout().itemAt(10).widget().text(),
                'utm_este': container.layout().itemAt(12).widget().text(),
                'unidad_utm': container.layout().itemAt(14).widget().currentText(),
                'huso': container.layout().itemAt(16).widget().currentText(),
                'datum': container.layout().itemAt(18).widget().currentText(),
                'referencia': container.layout().itemAt(20).widget().toPlainText(),
            }
            
            if all(not value for value in data.values() if value is not None):
                continue 

            detalles_data.append(data)

        if not detalles_data:
            if not silence:
                self.accept()
                self.deleteLater() 
                self.parent().show_message("Info", "Guardar", "No hay detalles para guardar.")
            return

        try:
            response = requests.post(f'{self.parent().api_base_url}saveDetalles', json={
                'trabajo_id': self.parent().current_trabajo_id,
                'formulario_id': self.parent().current_formulario_id,
                'detalles': detalles_data
            })
            response.raise_for_status()
            if not silence:
                self.accept()
                self.deleteLater() 
                self.parent().show_message("Info", "Guardar", "Detalles guardados exitosamente.")
            print("Detalles guardados:", detalles_data)

        except requests.RequestException as e:
            if not silence:
                self.parent().show_message("Error", "Error al guardar detalles", str(e))
            print(f"Error al guardar detalles: {e}")


    def load_detalles(self):
        if not self.parent().current_formulario_id:
            return

        try:
            response = requests.get(f'{self.parent().api_base_url}getDetalles&formulario_id={self.parent().current_formulario_id}')
            response.raise_for_status()
            detalles_data = response.json()
            if isinstance(detalles_data, list):
                for detalle in detalles_data:
                    self.add_detalle(detalle)
        except requests.RequestException as e:
            print(f"Error al cargar detalles: {e}")
            self.parent().show_message("Error", "Error al cargar detalles", str(e))
    
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
        self.save_detalles(silence=True)
        super().closeEvent(event)

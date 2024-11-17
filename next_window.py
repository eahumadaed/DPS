from comunas import Comunas_list
import requests,json
from PyQt5.QtWidgets import QMessageBox, QStyle, QCompleter, QSplitter, QApplication, QMainWindow, QVBoxLayout, QWidget, QFrame, QHBoxLayout, QListWidget, QPushButton, QLabel, QScrollArea, QSpacerItem, QSizePolicy, QTextEdit, QDateEdit, QGridLayout, QComboBox, QLineEdit, QCheckBox, QListWidgetItem
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QDate, QEvent, QStringListModel
from PyQt5.QtGui import QIntValidator, QColor, QIcon
from UsuarioModal import UsuarioModal
from InscriptionModal import InscriptionModal
from DetallesModal import DetallesModal
from HistoryModal import HistoryModal
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp
import sys
from comunas import Comunas_list
import re
from datetime import datetime
import os
from custom_browser import CustomWebEngineView, DrawSquareWidget

API_BASE_URL = 'https://loverman.net/dbase/dga2024/api/api.php?action='
api_base_url = API_BASE_URL

class NextWindow(QMainWindow):
    def __init__(self, user_id, user_name,Cantidad, smallScreen=False):
        super().__init__()
        self.viewer_url = "https://www.dataresearch.cl/repositorio_dps_2024/viewerv2.html"
        self.smallScreen = smallScreen
        self.user_id = user_id
        self.current_trabajo_id = None
        self.current_trabajo_info = None
        self.current_formulario_id = None
        self.modal_abierto = False
        self.rut_was_verified = False
        self.user_name = user_name
        self.session_history = []
    
        self.API_BASE_URL = 'https://loverman.net/dbase/dga2024/api/api.php?action='
        self.api_base_url = self.API_BASE_URL

        self.setGeometry(1, 30, 1980, 1080)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        self.pdf_paths = []
        self.entries = []
        self.message_labels = {}
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout(self.form_widget)
        
        self.devolver_button = QPushButton("Devolver a asignados", self)
        
        self.nombres_list = []
        self.apellidos_list = []
        
        self.create_left_frame()
        self.create_middle_frame()
        self.create_right_frame()
        self.set_title(Cantidad)
        self.skip_inscription_button.setEnabled(False)
        self.devolver_button.setEnabled(False)

        self.splitter = QSplitter(Qt.Horizontal)
        
        self.splitter.addWidget(self.left_frame)
        self.splitter.addWidget(self.middle_frame)
        self.splitter.addWidget(self.right_frame)
        if smallScreen:
            self.splitter.setSizes([240, 350, self.width()-590])
        else:
            self.splitter.setSizes([300, 550, self.width()-850])
        
        self.layout.addWidget(self.splitter)

        self.load_trabajos()
        
    def set_title(self,Cantidad):
        self.setWindowTitle(f"DPs Formulario ({self.user_name}) - {Cantidad} Terminados")
    
    def show_message(self, message_type, title, message):
        msg_box = QMessageBox()
        if message_type == "Error":
            msg_box.setIcon(QMessageBox.Critical)
        elif message_type == "Info":
            msg_box.setIcon(QMessageBox.Information)
        elif message_type == "Warning":
            msg_box.setIcon(QMessageBox.Warning)
        else:
            msg_box.setIcon(QMessageBox.NoIcon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()
        
    def calculate_dv(self, rut):
        reversed_digits = map(int, reversed(rut))
        factors = [2, 3, 4, 5, 6, 7] 
        s = sum(d * f for d, f in zip(reversed_digits, factors * 3))
        dv = 11 - (s % 11)
        if dv == 11:
            return '0'
        elif dv == 10:
            return 'K'
        else:
            return str(dv)
        
    def show_rut_error(self, rut,error):
        self.show_message("Info", "Rut inválido", f'Rut "{rut}" con formato incorrecto, por favor corregir. (xxxxxxxx-x)\n\nError: {error}')
        
    def verificar_rut(self, rut, show_messages = True):
        rut = rut.replace(" ","").upper()
        errorWasFounded = False
        try:
            rut = rut.replace(" ","").upper()
            if "-" not in rut:
                errorWasFounded = True
                if show_messages:
                    self.show_rut_error(rut, "Falta '-'")
            elif not rut.replace("-","")[:-1].isdigit() and (rut.replace("-","")[-1].isdigit() or rut.replace("-","")[-1] == 'K'):
                errorWasFounded = True
                if show_messages:
                    self.show_rut_error(rut, "Hay caracteres no permitidos")
            else:
                base = rut.split("-")[0]
                dv = rut.split("-")[-1]
            
                if 6 > len(base) > 8:
                    errorWasFounded = True
                    if show_messages:
                        self.show_rut_error(rut, "Comprobación de longitud")
                
                else:
                    calculated_dv = self.calculate_dv(base)
                    if dv!=calculated_dv:
                        errorWasFounded = True
                        if show_messages:
                            self.show_rut_error(rut, "Dígito verificador incorrecto")
            
            return {"rut":rut, "errorWasFounded": errorWasFounded}


        except (ValueError, IndexError) as e:
            print(f"Error al verificar rut")
            return {"rut":rut, "errorWasFounded": False}
        
    def get_datetime(self):
        return datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
    def to_uppercase(self, entry):
        entry.blockSignals(True)
        
        if isinstance(entry, QLineEdit):
            cursor_position = entry.cursorPosition() 
            entry.setText(entry.text().upper())  
            entry.setCursorPosition(cursor_position)
        elif isinstance(entry, QTextEdit):
            cursor_position = entry.textCursor().position()
            entry.setPlainText(entry.toPlainText().upper())
            cursor = entry.textCursor()
            cursor.setPosition(cursor_position)
            entry.setTextCursor(cursor)
        entry.blockSignals(False)

        
    def buscar_rut_api(self, rut):
        try:
            url = f"http://loverman.net/api/buscar_rut.php?rut={rut}"
            response = requests.get(url)
            response.raise_for_status()
            return True, response.json()
        except Exception as e:
            print(f"Error al buscar RUT: {e}")
            return False, {}

    def create_left_frame(self):
        self.left_frame = QFrame(self)
        self.left_frame.setFrameShape(QFrame.StyledPanel)
        self.left_frame.setMaximumWidth(300)
        #self.layout.addWidget(self.left_frame)

        self.left_layout = QVBoxLayout(self.left_frame)

        self.history_layout = QHBoxLayout()
        
        self.dir_label = QLabel("Seleccione trabajo", self)
        self.history_layout.addWidget(self.dir_label)

        self.history_button = QPushButton("📋")
        self.history_button.setFixedWidth(30)
        self.history_button.clicked.connect(lambda: self.open_history_modal(history_list = self.session_history))
        self.history_layout.addWidget(self.history_button)
        
        self.left_layout.addLayout(self.history_layout)

        self.dir_listwidget = QListWidget(self)
        self.dir_listwidget.setMaximumHeight(180)
        self.dir_listwidget.itemSelectionChanged.connect(self.on_directory_select)
        self.left_layout.addWidget(self.dir_listwidget)
        
        self.dir_label = QLabel("Trabajos pendientes", self)
        self.left_layout.addWidget(self.dir_label)
        
        self.dir_pendientes_list = QListWidget(self)
        self.dir_pendientes_list.setMaximumHeight(180)
        self.dir_pendientes_list.itemSelectionChanged.connect(self.on_directory_select)
        self.left_layout.addWidget(self.dir_pendientes_list)
        
        self.devolver_button.clicked.connect(self.devolver_a_asignados)
        self.left_layout.addWidget(self.devolver_button)

        self.dir_label = QLabel("Seleccione PDF", self)
        self.left_layout.addWidget(self.dir_label)
        self.pdf_listbox = QListWidget(self)
        self.pdf_listbox.itemSelectionChanged.connect(self.on_pdf_select)
        self.left_layout.addWidget(self.pdf_listbox)
        
        self.dir_listwidget.itemClicked.connect(lambda item: self.cambiar_seleccion(item, self.dir_listwidget))
        self.dir_pendientes_list.itemClicked.connect(lambda item: self.cambiar_seleccion(item, self.dir_pendientes_list))
        self.pdf_listbox.itemClicked.connect(lambda item: self.cambiar_seleccion(item, self.pdf_listbox))
        
    def devolver_a_asignados(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de presionar el botóm.")
            return
        selected_items = self.dir_pendientes_list.selectedItems()
        
        if selected_items:
            self.update_trabajo_estado("Asignado")
            self.load_trabajos()
        self.current_trabajo_id = None
        self.devolver_button.setEnabled(False)
        
    def cambiar_seleccion(self, item, lista):
        current_item = lista.currentItem()
        selected_row = lista.row(item)
        
        if selected_row != current_item:
            lista.setCurrentRow(selected_row)

    def load_trabajos(self):
        try:
            self.dir_listwidget.clear()
            self.dir_pendientes_list.clear()
            response = requests.get(f'{API_BASE_URL}getTrabajos&user_id={self.user_id}')
            response.raise_for_status()
            trabajos = response.json()
            
            existsCorregir = False
            for trabajo in trabajos:
                if trabajo['estado'] == "Corregir":
                    existsCorregir = True
                    break
            for trabajo in trabajos:
                item = QListWidgetItem(f"{trabajo['numero']} - {trabajo['anio']} ({trabajo['estado']})")
                item.setData(Qt.UserRole, trabajo['id'])
                
                if trabajo['estado']=="Terminado":
                    item.setForeground(QColor('green'))
                    self.dir_listwidget.addItem(item)
                if existsCorregir:
                    if trabajo['estado']=="Corregir":
                        self.dir_listwidget.addItem(item)
                else:
                    if trabajo['estado']=="Pendiente":
                        self.dir_pendientes_list.addItem(item)
                    else:
                        self.dir_listwidget.addItem(item)
        except requests.RequestException as e:
            self.show_message("Error", "Error al cargar trabajos", str(e))

    def load_formulario(self, trabajo_id):
        try:
            response = requests.get(f'{API_BASE_URL}getFormulario&trabajo_id={trabajo_id}')
            response.raise_for_status()
            formulario = response.json()
            if 'id' in formulario:
                self.current_formulario_id = formulario['id']
                print(f"Id 2 Del formulario:{self.current_formulario_id}")
                self.fill_form(formulario)

            else:
                self.fill_form(formulario)

                self.current_formulario_id = formulario['id']
                print(f"Id 1 Del formulario:{self.current_formulario_id}")
        except requests.RequestException as e:
            self.show_message("Error", "Error al cargar el formulario", str(e))
            
    def update_nombre_completer(self,entry):
        if not self.recomendar_checkbox.isChecked():
            model = QStringListModel([])
            self.apellido_completer.setModel(model)
            return
        items = self.nombres_list
        nombres = {}

        fmt = '%Y-%m-%d %H:%M:%S'

        for item in items:
            nombre = item['nombre']
            timestamp = item['timestamp']
            trabajo_id = item['trabajo_id']

            if isinstance(timestamp, str):
                item_timestamp = datetime.strptime(timestamp, fmt)
            else:
                item_timestamp = timestamp

            if nombre in nombres:
                current_data = nombres[nombre]
                current_timestamp = current_data['lastTimestamp']
                
                if isinstance(current_timestamp, str):
                    current_timestamp = datetime.strptime(current_timestamp, fmt)

                nombres[nombre].update({
                    "fromCurrentTrabajoId": trabajo_id == self.current_trabajo_id,
                    "frecuencia": current_data['frecuencia'] + 1,
                    "lastTimestamp": max(current_timestamp, item_timestamp)
                })
            else:
                nombres[nombre] = {
                    "fromCurrentTrabajoId": trabajo_id == self.current_trabajo_id,
                    "frecuencia": 1,
                    "lastTimestamp": item_timestamp 
                }

        sorted_nombres = sorted(
            nombres.items(),
            key=lambda item: (
                not item[1]["fromCurrentTrabajoId"],
                -item[1]["frecuencia"],
                -item[1]["lastTimestamp"].timestamp()
            )
        )

        sorted_nombres = [nombre for nombre, _ in sorted_nombres if nombre.upper() != entry.text().upper()]
        model = QStringListModel(sorted_nombres)
        self.nombres_completer.setModel(model)
            
    def add_nombre_item(self, entry):
        nombre = entry.text().strip().upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
        if nombre:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            itemWasFound = False
            for item in self.nombres_list:
                if item['entry'] == entry and item['trabajo_id']==self.current_trabajo_id:
                    item.update({"nombre": nombre, "trabajo_id": self.current_trabajo_id, "timestamp": timestamp})
                    itemWasFound = True
            if not itemWasFound:
                self.nombres_list.append({"nombre": nombre, "entry": entry, "trabajo_id": self.current_trabajo_id, "timestamp": timestamp})
        else:
            self.delete_nombre_item(entry)
        self.update_nombre_completer(entry)
    
    def delete_nombre_item(self, entry):
        for i, item in enumerate(self.nombres_list):
            if item['entry'] == entry and item['trabajo_id']==self.current_trabajo_id:
                del self.nombres_list[i]
                return
            
    def update_apellido_completer(self, entry):
        if not self.recomendar_checkbox.isChecked():
            model = QStringListModel([])
            self.apellido_completer.setModel(model)
            return
        
        items = self.apellidos_list
        apellidos = {}

        fmt = '%Y-%m-%d %H:%M:%S'

        for item in items:
            apellido = item['apellido']
            timestamp = item['timestamp']
            trabajo_id = item['trabajo_id']

            if isinstance(timestamp, str):
                item_timestamp = datetime.strptime(timestamp, fmt)
            else:
                item_timestamp = timestamp

            if apellido in apellidos:
                current_data = apellidos[apellido]
                current_timestamp = current_data['lastTimestamp']
                
                if isinstance(current_timestamp, str):
                    current_timestamp = datetime.strptime(current_timestamp, fmt)

                apellidos[apellido].update({
                    "fromCurrentTrabajoId": trabajo_id == self.current_trabajo_id,
                    "frecuencia": current_data['frecuencia'] + 1,
                    "lastTimestamp": max(current_timestamp, item_timestamp)
                })
            else:
                apellidos[apellido] = {
                    "fromCurrentTrabajoId": trabajo_id == self.current_trabajo_id,
                    "frecuencia": 1,
                    "lastTimestamp": item_timestamp 
                }

        sorted_apellidos = sorted(
            apellidos.items(),
            key=lambda item: (
                not item[1]["fromCurrentTrabajoId"],
                -item[1]["frecuencia"],
                -item[1]["lastTimestamp"].timestamp()
            )
        )

        sorted_apellidos = [apellido for apellido, _ in sorted_apellidos if apellido.upper()!=entry.text().upper()]
   
        model = QStringListModel(sorted_apellidos)
        self.apellido_completer.setModel(model)
            
    def add_apellido_item(self, entry):
        apellido = entry.text().strip().upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
        if apellido:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            itemWasFound = False
            for item in self.apellidos_list:
                if item['entry'] == entry and item['trabajo_id']==self.current_trabajo_id:
                    item.update({"apellido": apellido, "trabajo_id": self.current_trabajo_id, "timestamp": timestamp})
                    itemWasFound = True
            if not itemWasFound:
                self.apellidos_list.append({"apellido": apellido, "entry": entry, "trabajo_id": self.current_trabajo_id, "timestamp": timestamp})
        else:
            self.delete_apellido_item(entry)
        self.update_apellido_completer(entry)
    
    def delete_apellido_item(self, entry):
        for i, item in enumerate(self.apellidos_list):
            if item['entry'] == entry and item['trabajo_id']==self.current_trabajo_id:
                del self.apellidos_list[i]
                return
    
    def fill_form(self, formulario):
        self.clear_form()

        field_mapping = {
            'f_inscripcion': 'F_INSCRIPCION',
            'comuna': 'COMUNA',
            'cbr': 'CBR',
            'foja': 'FOJA',
            'v': 'V',
            'numero': 'N°',
            'anio': 'AÑO',
            'naturaleza_agua': 'NATURALEZA DEL AGUA',
            'tipo_derecho': 'TIPO DE DERECHO',
            'nombre_comunidad': 'NOMBRE DE COMUNIDAD',
            'proyecto_parcelacion': 'PROYECTO DE PARCELACIÓN',
            'sitio': 'SITIO',
            'parcela': 'PARCELA',
            'ejercicio_derecho': 'EJERCICIO DEL DERECHO',
            'metodo_extraccion': 'METODO DE EXTRACCION',
            'cantidad': 'CANTIDAD',
            'unidad': 'UNIDAD',
            'utm_norte': 'UTM NORTE',
            'utm_este': 'UTM ESTE',
            'unidad_utm': 'UNIDAD UTM',
            'huso': 'HUSO',
            'datum': 'DATUM',
            'pto_conocidos_captacion': 'PTOS CONOCIDOS DE CAPTACION',
            'comentario': 'COMENTARIO',
            'user_rut': 'RUT',
            'user_nac': 'NAC',
            'user_tipo': 'TIPO',
            'user_genero': 'GENERO',
            'user_nombre': 'NOMBRE',
            'user_paterno': 'PATERNO',
            'user_materno': 'MATERNO',
            'OBS': 'OBS',
            'SIN_INSCRIPCION': 'SIN INSCRIPCION'  #ALGUNOS CAMPOS CON ESPACIOS O NOMBRE PARTICULARES, SE DEBEN MAPEAR, POR EJEMPLO LOS CHECKBOX, YA QUE NO EXISTE UN "BOOLEAN" EN SQL, SOLO EXISTE UN TYNYINT(0,1)
        }
        
        for json_key, form_label in field_mapping.items():
            if json_key in formulario:
                entry_value = formulario[json_key]     

                for label, entry in self.entries:
                    if label == form_label:
                        if isinstance(entry, QLineEdit):
                            entry.setText(entry_value if entry_value is not None else "")
                        elif isinstance(entry, QComboBox):
                            index = entry.findText(entry_value if entry_value is not None else "")
                            if index >= 0:
                                entry.setCurrentIndex(index)
                        elif isinstance(entry, QCheckBox):
                            entry.setChecked(entry_value.lower() in ['true', '1'] if entry_value is not None else False)
                        elif isinstance(entry, QTextEdit):
                            entry.setPlainText(entry_value if entry_value is not None else "")
                        elif isinstance(entry, QDateEdit) and entry_value:
                            entry.setDate(QDate.fromString(entry_value, "dd/MM/yyyy"))

        
        print("Formulario cargado:", formulario)


    def on_directory_select(self):
        self.rut_was_verified = False
        selected_items = []
        
        if self.sender() == self.dir_listwidget:
            self.dir_pendientes_list.clearSelection()
            selected_items = self.dir_listwidget.selectedItems()
            self.devolver_button.setEnabled(False)
            self.skip_inscription_button.setEnabled(True)
            
        elif self.sender() == self.dir_pendientes_list:
            self.dir_listwidget.clearSelection()
            selected_items = self.dir_pendientes_list.selectedItems()
            self.devolver_button.setEnabled(True)
            self.skip_inscription_button.setEnabled(False)
        
        if selected_items:
            selected_item = selected_items[0]
            selected_trabajo_id = selected_item.data(Qt.UserRole)
            
            item_info = selected_item.text()
            self.current_trabajo_info = {
                "numero_trabajo":item_info.split("-")[0].strip(),
                "anio_trabajo": item_info.split("-")[-1].split("(")[0].strip(),
                "estado_anterior": item_info.split("(")[-1].replace(")","").strip()
            }
            
            if self.current_trabajo_id is not None and self.current_trabajo_id != selected_trabajo_id and self.current_trabajo_info['estado_anterior']!="Terminado":
                self.save_form(silence=True)

            self.current_trabajo_id = selected_trabajo_id
            
            
            
            if self.current_trabajo_info['estado_anterior']=="Terminado" or self.current_trabajo_info['estado_anterior']=="Corregir":
                self.skip_inscription_button.setEnabled(False)
                
            
            print(f"Trabajo seleccionado: {selected_trabajo_id}")
            self.load_formulario(selected_trabajo_id)
            self.validate_fields()
            self.clear_pdf_list()
            self.clear_pdf_viewer()
            self.load_pdfs(selected_trabajo_id)
            

    def load_pdfs(self, trabajo_id):
        
        try:
            response = requests.get(f'{API_BASE_URL}getPDFs&trabajo_id={trabajo_id}')
            response.raise_for_status()
            pdfs = response.json()
            self.pdf_listbox.clear()
            self.pdf_paths = []
            for pdf in pdfs:
                self.pdf_listbox.addItem(pdf['nombre'])
                self.pdf_paths.append(pdf['ruta'])
        except requests.RequestException as e:
            self.show_message("Error", "Error al cargar PDFs", str(e))

    def on_pdf_select(self):
        selected_items = self.pdf_listbox.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            index = self.pdf_listbox.row(selected_item)
            pdf_url = self.pdf_paths[index]
            print(f"PDF seleccionado: {pdf_url}")
            self.load_pdf(pdf_url)

    def load_pdf(self, encoded_pdf_path):
        self.browser.reset_zoom()
        try:
            self.remove_highlights()
            pdf_url = f"{self.viewer_url}?file={encoded_pdf_path}#page=1"
            self.browser.load(QUrl(pdf_url))
            print(f"Mostrando PDF desde URL: {pdf_url}")
            #self.load_text_file(encoded_pdf_path)
        except Exception as e:
            self.show_message("Error", "Error al cargar PDF", str(e))

    def load_text_file(self, pdf_url):
        txt_url = pdf_url.replace('.pdf', '.txt').replace('.PDF', '.txt')
        try:
            response = requests.get(txt_url)
            response.raise_for_status()
            if response.status_code == 200:
                content = response.text
                self.text_edit.setText(content)
            else:
                self.text_edit.clear()
        except requests.RequestException as e:
            print(f"Error al cargar el archivo de texto: {e}")
            self.text_edit.clear()

    def navigate_pdf(self, direction):
        if self.pdf_doc:
            self.page_number = max(0, min(self.pdf_doc.page_count - 1, self.page_number + direction))
            self.show_pdf_page(self.page_number)
            self.page_label.setText(f"Página {self.page_number + 1} de {self.pdf_doc.page_count}")
            self.load_text_file()

    def create_middle_frame(self):
        self.middle_frame = QFrame(self)
        self.middle_frame.setFrameShape(QFrame.StyledPanel)
        self.middle_frame.setMaximumWidth(700)
        self.middle_frame.setMinimumWidth(350 if self.smallScreen else 550)
        #self.layout.addWidget(self.middle_frame)

        self.middle_layout = QVBoxLayout(self.middle_frame)
        self.middle_layout.setSpacing(5)

        self.middle_section_title_layout = QHBoxLayout()
        self.form_label = QLabel("Formulario", self)
        self.middle_section_title_layout.addWidget(self.form_label)
        
        self.skip_inscription_button = QPushButton("Saltar Inscripción ⏩", self)
        self.skip_inscription_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.skip_inscription_button.clicked.connect(self.skip_inscription)
        self.middle_section_title_layout.addWidget(self.skip_inscription_button)
        
        self.middle_layout.addLayout(self.middle_section_title_layout)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.middle_layout.addWidget(self.scroll_area)
        self.form_widget = QWidget()
        self.scroll_area.setWidget(self.form_widget)
        self.form_layout = QVBoxLayout(self.form_widget)
    
        # APARTADO: INSCRIPCIONES
        self.add_section_title("INSCRIPCIONES")
        self.inscriptions_layout = QGridLayout()
        self.form_layout.addLayout(self.inscriptions_layout)
        
        self.comunas_formatted_list = [
            comuna.upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
            for comuna in Comunas_list
        ]
        
        self.completer = QCompleter(self.comunas_formatted_list)
        self.completer.setCompletionMode(QCompleter.InlineCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        if self.smallScreen:
            self.add_input_field("SIN INSCRIPCION", "checkbox")
            self.add_input_field("F_INSCRIPCION", "date")
            self.add_input_field("COMUNA", "select", Comunas_list)  # Agrega las comunas correspondientes
            self.add_input_field("CBR", "text")
            self.add_input_field("FOJA", "number")
            self.add_input_field("V", "checkbox")
            self.add_input_field("N°", "number")
            self.add_input_field("AÑO", "number")
        else:
            self.add_input_field("SIN INSCRIPCION", "checkbox", parent_layout=self.inscriptions_layout, row=0, col=3)
            self.add_input_field("F_INSCRIPCION", "date", parent_layout=self.inscriptions_layout, row=1, col=0)
            self.add_input_field("COMUNA", "select", Comunas_list, parent_layout=self.inscriptions_layout, row=2, col=0)  # Agrega las comunas correspondientes
            self.add_input_field("CBR", "text", parent_layout=self.inscriptions_layout, row=3, col=0, size=0)
            self.add_input_field("FOJA", "number", parent_layout=self.inscriptions_layout, row=4, col=0, size=0)
            self.add_input_field("V", "checkbox", parent_layout=self.inscriptions_layout, row=4, col=1, size=0)
            self.add_input_field("N°", "number", parent_layout=self.inscriptions_layout, row=4, col=2, size=0)
            self.add_input_field("AÑO", "number", parent_layout=self.inscriptions_layout, row=4, col=3, size=0)
            
        self.add_inscription_button = QPushButton("Agregar Inscripción", self)
        self.add_inscription_button.clicked.connect(self.open_inscription_modal)
        self.form_layout.addWidget(self.add_inscription_button)

        # APARTADO: TIPO DE EXPEDIENTE
        self.add_section_title("TIPO DE EXPEDIENTE")
        self.add_input_field("NATURALEZA DEL AGUA", "select", ['--','SUPERFICIAL', 'SUBTERRANEA',"S. Y DETENIDA","SUP. Y CORRIENTE","SUP. CORRIENTES/DETENIDAS"])
        self.add_input_field("TIPO DE DERECHO", "select", ['--','CONSUNTIVO','NO CONSUNTIVO'])
        self.add_input_field("NOMBRE DE COMUNIDAD", "text")
        self.add_input_field("PROYECTO DE PARCELACIÓN", "text")
        self.add_input_field("SITIO", "text")
        self.add_input_field("PARCELA", "text")

        # APARTADO: USUARIOS
        self.add_section_title("USUARIOS")
        
        self.recomendar_layout = QHBoxLayout()
        self.recomendar_lbl = QLabel("Sugerir")
        self.recomendar_layout.addWidget(self.recomendar_lbl)
        self.recomendar_checkbox = QCheckBox()
        self.recomendar_checkbox.setChecked(True)
        self.recomendar_layout.addWidget(self.recomendar_checkbox)
        
        self.limpiar_recomendaciones_button = QPushButton("Borrar sugerencias")
        self.limpiar_recomendaciones_button.clicked.connect(self.limpiar_recomendaciones)
        self.recomendar_layout.addWidget(self.limpiar_recomendaciones_button)
        
        self.form_layout.addLayout(self.recomendar_layout)
        
        self.recomendar_layout.setAlignment(Qt.AlignRight)

        self.recomendar_layout.setContentsMargins(0, 0, 0, 0)
        self.recomendar_layout.setSpacing(5)

        self.form_layout.addLayout(self.recomendar_layout)
        
        self.user_layout = QGridLayout()
        self.form_layout.addLayout(self.user_layout)
        
        self.nombres_completer = QCompleter(self.nombres_list)
        self.nombres_completer.setCompletionMode(QCompleter.InlineCompletion)
        self.nombres_completer.setCaseSensitivity(Qt.CaseInsensitive)

        self.apellido_completer = QCompleter(self.apellidos_list)
        self.apellido_completer.setCompletionMode(QCompleter.InlineCompletion)
        self.apellido_completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        self.add_input_field("RUT", "text", parent_layout=self.user_layout, row=0, col=0)
        self.add_button_rut = QPushButton("Buscar", self)
        self.add_button_rut.clicked.connect(self.handle_rut_search)
        self.user_layout.addWidget(self.add_button_rut, 0, 1)

        if self.smallScreen:
            self.add_input_field("NAC", "select", ['--','CHILENA','EXTRANJERA'], parent_layout=self.user_layout, row=1, col=0)
            self.add_input_field("TIPO", "select", ['--','NATURAL','JURIDICA'], parent_layout=self.user_layout, row=1, col=1)
            self.add_input_field("GENERO", "select", ['--','F','M'], parent_layout=self.user_layout, row=2, col=0)
            self.add_input_field("NOMBRE", "text")
            self.add_input_field("PATERNO", "text")
            self.add_input_field("MATERNO", "text")
            self.add_user_button = QPushButton("Agregar Usuarios", self)
            self.add_user_button.clicked.connect(self.open_usuarios_modal)
            self.form_layout.addWidget(self.add_user_button)
        else:
            self.add_input_field("NAC", "select", ['--','CHILENA','EXTRANJERA'], parent_layout=self.user_layout, row=1, col=0)
            self.add_input_field("TIPO", "select", ['--','NATURAL','JURIDICA'], parent_layout=self.user_layout, row=1, col=1)
            self.add_input_field("GENERO", "select", ['--','F','M'], parent_layout=self.user_layout, row=2, col=0)
            self.add_input_field("NOMBRE", "text", parent_layout=self.user_layout, row=2, col=1)
            self.add_input_field("PATERNO", "text", parent_layout=self.user_layout, row=3, col=0)
            self.add_input_field("MATERNO", "text", parent_layout=self.user_layout, row=3, col=1)
            self.add_user_button = QPushButton("Agregar Usuarios", self)
            self.add_user_button.clicked.connect(self.open_usuarios_modal)
            self.form_layout.addWidget(self.add_user_button)

        # APARTADO: EJERCICIO
        self.add_section_title("EJERCICIO")
        self.add_input_field("EJERCICIO DEL DERECHO", "select", ['--','PERMANENTE Y CONTINUO', 'EVENTUAL Y CONTINUO','PERM. Y CONT. Y PROVICIONALES','SIN EJERCICIO','PERM. Y DISC. Y PROVICIONALES','PERM Y ALTER. Y PROVICIONALES','EVENTUAL Y DISCONTINUO','EVENTUAL Y ALTERNADO','PERMANENTE Y DISCONTINUO','PERMANENTE Y ALTERNADO'])
        self.add_input_field("METODO DE EXTRACCION", "select", ['--','MECANICA','GRAVITACIONAL','MECANICA Y/O GRAVITACIONAL'])

        # APARTADO: CAUDAL
        self.add_section_title("CAUDAL")
        self.add_input_field("CANTIDAD", "text")
        self.add_input_field("UNIDAD", "select", ['--','LT/S','M3/S','MM3/AÑO','M3/AÑO','LT/MIN','M3/H','LT/H','M3/MES','ACCIONES','M3/DIA','M3/MIN','LT/DIA','REGADORES','CUADRAS','TEJAS','HORAS TURNO','%','PARTES','LT/MES','MMM3/MES','M3/HA/MES', 'ETC'])
        self.add_input_field("UTM NORTE", "text")
        self.add_input_field("UTM ESTE", "text")
        self.add_input_field("UNIDAD UTM", "select", ['--','KM', 'MTS'])
        self.add_input_field("HUSO", "select", ['--','18', '19'])
        self.add_input_field("DATUM", "select", ['--','56', '69','84'])

        # APARTADO: REFERENCIAS
        self.add_section_title("REFERENCIAS")
        self.add_input_field("PTOS CONOCIDOS DE CAPTACION", "textarea")

        self.add_detalles_button = QPushButton("Agregar Detalles", self)
        self.add_detalles_button.clicked.connect(self.open_detalles_modal)
        self.form_layout.addWidget(self.add_detalles_button)
        self.add_input_field("OBS", "select", ['--', 'PERFECTO', 'IMPERFECTO', 'PERFECCIONADO AL MARGEN', 'SIN RUT', 'NO SE LEE', 'NO CARGA'])
        self.add_label("sugerencia","", "#2C3E50")

        self.comentario_layout = QVBoxLayout()
        self.add_section_title("INTERNO")
        self.add_input_field("COMENTARIO", "textarea")#, parent_layout=self.comentario_layout)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.form_layout.addItem(spacer)

        self.save_button = QPushButton("Guardar", self)
        self.save_button.clicked.connect(self.save_form)
        self.middle_layout.addWidget(self.save_button)

        self.submit_button = QPushButton("Registrar", self)
        self.submit_button.clicked.connect(self.submit_form)
        self.middle_layout.addWidget(self.submit_button)
        
    def limpiar_recomendaciones(self):
        self.nombres_list = []
        self.apellidos_list = []
        model = QStringListModel([])
        self.nombres_completer.setModel(model)
        self.apellido_completer.setModel(model)
        
    
    def skip_inscription(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de presionar el boton.")
            return
        self.save_form(silence=True)
        self.update_trabajo_estado("Pendiente")
        self.load_trabajos()
        self.clear_pdf_viewer()
        self.clear_pdf_list()
        self.current_trabajo_id = None
        self.skip_inscription_button.setEnabled(False)
        
        
    def update_completer(self, preferredValue):
        updated_list = [preferredValue] + [comuna for comuna in self.comunas_formatted_list if comuna != preferredValue]

        model = QStringListModel(updated_list)
        self.completer.setModel(model)
            
    def set_preferred_value(self, value):
        # Establecer el valor preferido en la instancia
        self.preferredValue = value.upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
        self.update_completer(self.preferredValue)
        
    def handle_rut_search(self):
        rut_entry = None
        for label, entry in self.entries:
            if label == "RUT":
                rut_entry = entry
                break

        if rut_entry:
            rut = rut_entry.text().split("-")[0]
            success, data = self.buscar_rut_api(rut)
            print(f"{success} - {data}")
            if success:
                self.fill_user_fields(data)
            else:
                self.show_message("Info", "Buscar RUT", "No se encontraron datos para el RUT ingresado.")
                
    def fill_user_fields(self, data):
        field_mapping = {
            'NAC': 'NAC',
            'TIPO': 'TIPO',
            'GENERO': 'GENERO',
            'NOMBRE': 'Nombre',
            'PATERNO': 'Apa',
            'MATERNO': 'Ama'
        }

        for json_key, form_label in field_mapping.items():
            entry_value = data.get(form_label, "")
            for label, entry in self.entries:
                if label == json_key:
                    if isinstance(entry, QLineEdit):
                        entry.setText(entry_value)
                    elif isinstance(entry, QComboBox):
                        index = entry.findText(entry_value)
                        if index >= 0:
                            entry.setCurrentIndex(index)
                            
    def on_viewer_changed(self):
        option = self.viewer_combo.currentText()
        
        if option == "Visor nuevo":
            self.browser.ignoreZoom = True
            viewer_url = "https://www.dataresearch.cl/repositorio_dps_2024/viewerv2.html"
        elif option == "Visor antiguo":
            self.browser.ignoreZoom = False
            viewer_url = "https://www.dataresearch.cl/repositorio_dps_2024/viewerv1.html"
        else:
            viewer_url = self.viewer_url
            
        print(viewer_url)
        
        if self.viewer_url!=viewer_url:
            self.viewer_url = viewer_url
            selected_items = self.pdf_listbox.selectedItems()
            if selected_items:
                selected_item = selected_items[0]
                index = self.pdf_listbox.row(selected_item)
                pdf_url = self.pdf_paths[index]
                print(f"PDF seleccionado: {pdf_url}")
                self.load_pdf(pdf_url)
        
    def remove_highlights(self):
        self.browser.selection_widget.rects = []
        self.browser.selection_widget.update()
                            
    def create_right_frame(self):
        self.right_frame = QFrame(self)
        self.right_frame.setFrameShape(QFrame.StyledPanel)
        #self.layout.addWidget(self.right_frame, stretch=1)

        self.right_layout = QVBoxLayout(self.right_frame)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        
        self.options_layout = QHBoxLayout()
        self.options_layout.setContentsMargins(5, 5, 5, 5)
        self.remove_highlights_button = QPushButton("Quitar marcas")
        self.remove_highlights_button.clicked.connect(self.remove_highlights)
        self.remove_highlights_button.adjustSize()
        self.remove_highlights_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.options_layout.addWidget(self.remove_highlights_button, alignment=Qt.AlignLeft)
        
        self.viewer_combo = QComboBox()
        self.viewer_combo.addItems(["Visor nuevo", "Visor antiguo"])
        self.viewer_combo.currentIndexChanged.connect(self.on_viewer_changed)
        self.viewer_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.options_layout.addWidget(self.viewer_combo, alignment=Qt.AlignRight)
        
        self.right_layout.addLayout(self.options_layout)
        
        self.browser = CustomWebEngineView()
        self.right_layout.addWidget(self.browser)
        
    
    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
                self.find_dialog.show()
                return True
        return super().eventFilter(source, event)
    
    def add_label(self, key, text, color="black"):
        message_label = QLabel(text)
        self.message_labels[key] = message_label
        message_label.setStyleSheet(f"color: {color};")
        message_label.setAlignment(Qt.AlignRight)
        self.form_layout.addWidget(message_label)

    def add_input_field(self, label_text, field_type="text", options=None, parent_layout=None, row=0, col=0, size=None):
        if parent_layout is None:
            parent_layout = self.form_layout

        container = QFrame(self.form_widget)
        if self.smallScreen and (label_text=="COMENTARIO" or label_text=="PTOS CONOCIDOS DE CAPTACION"):
            container_layout = QVBoxLayout(container)
        else:
            container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        label = QLabel(label_text)
        container_layout.addWidget(label)

        field_type = field_type.strip().lower()

        if field_type == "text":
            entry = QLineEdit()
            if size:
                entry.setFixedWidth(size)
            if label_text == "RUT":
                entry.focusOutEvent = lambda event: self.on_rut_focus_out(entry, event)
                self.rut_entry = entry
                
            if label_text == "CBR":
                entry.setCompleter(self.completer)
                entry.returnPressed.connect(lambda: self.select_completion(label_text))
            
            if label_text=="NOMBRE":
                entry.textChanged.connect(lambda: self.add_nombre_item(entry))
                entry.setCompleter(self.nombres_completer)
                entry.returnPressed.connect(lambda: self.select_completion(label_text))
            
            if label_text=="PATERNO" or label_text=="MATERNO":
                entry.textChanged.connect(lambda: self.add_apellido_item(entry))
                entry.setCompleter(self.apellido_completer)
                entry.returnPressed.connect(lambda: self.select_completion(label_text))
                
            entry.textChanged.connect(lambda: self.to_uppercase(entry))
            entry.focusOutEvent = self.wrap_focus_out_event(entry.focusOutEvent)
        elif field_type == "number":
            entry = QLineEdit()
            entry.setValidator(QIntValidator())
            if label_text == "AÑO":
                entry.setMaxLength(4)
            if size:
                entry.setFixedWidth(size)
            entry.focusOutEvent = self.wrap_focus_out_event(entry.focusOutEvent)
        elif field_type == "select":
            entry = QComboBox()
            entry.wheelEvent = lambda event: event.ignore()
            if label_text == "COMUNA":
                entry.currentIndexChanged.connect(
                    lambda index: self.set_preferred_value(entry.currentText())
                )
            elif label_text == "OBS":
                self.obs_entry = entry
            if options:
                entry.addItems(options)
            entry.currentIndexChanged.connect(lambda: self.validate_fields())
            entry.focusOutEvent = self.wrap_focus_out_event(entry.focusOutEvent)
        elif field_type == "date":
            entry = QLineEdit()
            entry.setPlaceholderText("--/--/----")
            date_regex = QRegExp(r"\d{0,8}")
            date_validator = QRegExpValidator(date_regex)
            entry.setValidator(date_validator)
            entry.textChanged.connect(lambda: self.auto_format_date(entry))
            entry.focusOutEvent = self.wrap_focus_out_event(entry.focusOutEvent)
        elif field_type == "checkbox":
            entry = QCheckBox()
            entry.stateChanged.connect(lambda: self.validate_fields())
        elif field_type == "textarea":
            entry = QTextEdit()
            entry.setMinimumHeight(100)  # Altura mínima
            entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  # Crecer verticalmente
            entry.textChanged.connect(lambda: self.adjust_height(entry))
            entry.textChanged.connect(lambda: self.to_uppercase(entry))
            entry.focusOutEvent = self.wrap_focus_out_event(entry.focusOutEvent)
        else:
            raise ValueError(f"Tipo de campo desconocido: {field_type}")
        entry.focusInEvent = self.wrap_focus_in_event(entry, entry.focusInEvent)
        
        if self.smallScreen:
            entry.setMinimumWidth(50)

        container_layout.addWidget(entry)
        self.entries.append((label_text, entry))

        if isinstance(parent_layout, QGridLayout):
            parent_layout.addWidget(container, row, col)
        else:
            parent_layout.addWidget(container)
        print(f"Campo agregado: {label_text}, tipo: {field_type}")
   
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
        
    
    def select_completion(self, entry_lbl):
        self.sender().focusNextPrevChild(True)
        
    def adjust_height(self,entry):
        # Ajustar la altura del QTextEdit según el contenido
        height = int(entry.document().size().height()) + 5  # +20 para un espaciado adicional
        entry.setFixedHeight(max(height, 100))
    
    def auto_format_date(self, entry):
        sender = self.sender()
        text = sender.text()
        cursor_pos = sender.cursorPosition()
        
        cleaned_text = ''.join(filter(str.isdigit, text))
        
        if len(cleaned_text) > 8:
            cleaned_text = cleaned_text[:8]
        
        formatted_text = ''
        for i, char in enumerate(cleaned_text):
            if i == 2 or i == 4:
                formatted_text += '/'
            formatted_text += char

        prev_barras = text[:cursor_pos].count('/')
        new_barras = formatted_text[:cursor_pos].count('/')
        adjustment = new_barras - prev_barras
        new_cursor_pos = cursor_pos + adjustment
        
        sender.blockSignals(True)
        sender.setText(formatted_text)
        sender.setCursorPosition(new_cursor_pos)
        sender.blockSignals(False)

    def on_rut_focus_out(self, entry, event):
        try:
            formatted_rut=""
            text = entry.text()
            base_rut = re.sub(r'\D', '', text.strip().split("-")[0])

            if len(base_rut) > 8:
                base_rut = base_rut[:8] 
            
            if len(base_rut)>=6:
                dv = self.calculate_dv(base_rut)
                formatted_rut = f"{base_rut}-{dv}"
            #formatted_rut = text
            entry.blockSignals(True)
            entry.setText(formatted_rut)
            entry.blockSignals(False)
        except:
            pass
        self.validate_fields()
        QLineEdit.focusOutEvent(entry, event)

    def add_section_title(self, title):
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px;")
        self.form_layout.addWidget(title_label)

    """
    def add_inscription(self):
        count = len([entry for entry in self.entries if entry[0].startswith("F_INSCRIPCION")]) + 1
        self.add_input_field(f"F_INSCRIPCION_{count}", "date")
        self.add_input_field(f"COMUNA_{count}", "select", ["--", "Comuna1", "Comuna2"])
        self.add_input_field(f"CBR_{count}", "text")
        self.add_input_field(f"FOJA_{count}", "number")
        self.add_input_field(f"V_{count}", "checkbox")
        self.add_input_field(f"N°_{count}", "number")
        self.add_input_field(f"AÑO_{count}", "number")
    """

    def add_user(self):
        count = len([entry for entry in self.entries if entry[0].startswith("RUT")]) + 1
        self.add_input_field(f"RUT_{count}", "text")
        self.add_input_field(f"NAC_{count}", "select", ['--','CHILENA','EXTRANJERA'])
        self.add_input_field(f"TIPO_{count}", "select", ['--','NATURAL','JURIDICA'])
        self.add_input_field(f"GENERO_{count}", "select", ['--','F','M'])
        self.add_input_field(f"NOMBRE_{count}", "text")
        self.add_input_field(f"PATERNO_{count}", "text")
        self.add_input_field(f"MATERNO_{count}", "text")

    def buscar_rut(self):
        rut = None
        for label_text, entry in self.entries:
            if label_text.startswith("RUT"):
                rut = entry.text()
                break
        self.show_message("Info", "Buscar RUT", f"Buscando información para RUT: {rut}")
    
    def get_form_data(self):
        form_data = {}
        for label_text, entry in self.entries:
            if isinstance(entry, QLineEdit):
                form_data[label_text] = {"type": "QLineEdit", "value": entry.text().strip()}
            elif isinstance(entry, QComboBox):
                form_data[label_text] = {"type": "QComboBox", "value": entry.currentText()}
            elif isinstance(entry, QCheckBox):
                form_data[label_text] = {"type": "QCheckBox", "value": entry.isChecked()}
            elif isinstance(entry, QTextEdit):
                form_data[label_text] = {"type": "QTextEdit", "value": entry.toPlainText()}
            elif isinstance(entry, QDateEdit):
                form_data[label_text] = {"type": "QDateEdit", "value": entry.date().toString("dd/MM/yyyy")}
        return form_data
    
    
    def validate_fields(self):
        form_data = self.get_form_data()
        
        rut = form_data['RUT']['value']
        if rut and not self.rut_was_verified:
            self.verificar_rut(rut)
            self.rut_was_verified = True
        
        wrong_entries = []
        
        def add_wrong_entry(wrong_entry):
            wrong_entries.append(wrong_entry)
        
        def get_value(label_text):
            value = form_data[label_text]['value']
            if isinstance(value, str):
                value = value.replace("\n", " ").strip()
            if value == "--":
                value = ""
            return value

        def add_red_borders():
            for label_text, entry in self.entries:
                if label_text in wrong_entries:
                    entry.setStyleSheet("border-bottom: 2px solid red; border-radius: 0px;")
                else:
                    entry.setStyleSheet("")
        
        if get_value('OBS')!='NO SE LEE' and get_value('OBS')!='NO CARGA':
            if get_value('SIN INSCRIPCION')==True:
                labels_to_check = ['F_INSCRIPCION', 'COMUNA', 'CBR', 'FOJA', 'V', 'N°', 'AÑO']
                for lbl in labels_to_check:
                    value = get_value(lbl)
                    if value: add_wrong_entry(lbl)
                if get_value('OBS')=="PERFECTO" or get_value('OBS')== "PERFECCIONADO AL MARGEN":
                    add_wrong_entry('SIN INSCRIPCION')
            else:
                labels_to_check = ['CBR', 'FOJA', 'N°', 'AÑO']
                for lbl in labels_to_check:
                    value = get_value(lbl)
                    if not value: add_wrong_entry(lbl)
                    
                if not get_value('OBS'): add_wrong_entry('OBS')
                if(
                    not get_value('PTOS CONOCIDOS DE CAPTACION') and not (
                    get_value('OBS')=="PERFECTO" or
                    get_value('OBS')=="PERFECCIONADO AL MARGEN" or
                    get_value('OBS')=="SIN RUT"
                )):
                    add_wrong_entry('PTOS CONOCIDOS DE CAPTACION')
                    
                if get_value('OBS')!="PERFECTO" and get_value('OBS')!="PERFECCIONADO AL MARGEN":
                    if get_value('OBS')!='SIN RUT':
                        tipo_value = get_value('TIPO') 
                        if not tipo_value: add_wrong_entry('TIPO')
                        if tipo_value == 'NATURAL':
                            if not get_value('NAC'): add_wrong_entry('NAC')
                            if not get_value('GENERO'): add_wrong_entry('GENERO')
                            if not get_value('PATERNO'): add_wrong_entry('PATERNO')
                        if tipo_value == 'JURIDICA':
                            if get_value('NAC'): add_wrong_entry('NAC')
                            if get_value('GENERO'): add_wrong_entry('GENERO')
                            if get_value('PATERNO'): add_wrong_entry('PATERNO')
                            if get_value('MATERNO'): add_wrong_entry('MATERNO')
                        if not get_value('RUT'): add_wrong_entry('RUT')
                        if not get_value('NOMBRE'): add_wrong_entry('NOMBRE')
                    else:
                        if get_value('RUT'): add_wrong_entry('RUT')
                        if get_value('NAC'): add_wrong_entry('NAC')
                        if get_value('TIPO'): add_wrong_entry('TIPO')
                        if get_value('GENERO'): add_wrong_entry('GENERO')
                        if get_value('NOMBRE'): add_wrong_entry('NOMBRE')
                        if get_value('PATERNO'): add_wrong_entry('PATERNO')
                        if get_value('MATERNO'): add_wrong_entry('MATERNO')
            
        sugerencia = ""
        if not get_value('RUT'):
            sugerencia = "SIN RUT"
        elif(
            not get_value('CBR') or
            not get_value('FOJA') or
            not get_value('N°') or
            not get_value('AÑO')
        ):
            sugerencia = "MARCAR SIN INSCRIPCION"
        elif(
            get_value('NATURALEZA DEL AGUA') and
            get_value('TIPO DE DERECHO') and
            get_value('EJERCICIO DEL DERECHO') and
            get_value('UTM NORTE') and
            get_value('UTM ESTE') and
            get_value('CANTIDAD') and
            get_value('UNIDAD')
        ):
            sugerencia = "PERFECTO"
            
        elif(
            get_value('NATURALEZA DEL AGUA') and
            get_value('TIPO DE DERECHO') and
            get_value('EJERCICIO DEL DERECHO') and
            get_value('CANTIDAD') and
            get_value('UNIDAD')
        ):
            sugerencia = "POSIBLE PERFECTO (Verificar punto de captación)"
            
        elif(
            get_value('NATURALEZA DEL AGUA') and
            get_value('TIPO DE DERECHO') and
            get_value('EJERCICIO DEL DERECHO')
        ):
            sugerencia = "POSIBLE PERFECTO (Verificar caudal y punto de captación)"
            
        elif(
            not get_value('NATURALEZA DEL AGUA') or
            not get_value('TIPO DE DERECHO') or
            not get_value('EJERCICIO DEL DERECHO')
        ):
            sugerencia = "IMPERFECTO"
            
        sugerencia_label = self.message_labels['sugerencia']
        if get_value('SIN INSCRIPCION'):
            sugerencia_text=""
        else:
            sugerencia_text = f"SUGERENCIA: {sugerencia}"
        sugerencia_label.setText(sugerencia_text)
            
        add_red_borders()
        
        return wrong_entries 
        

    def save_form(self,silence=False):
        self.validate_fields()
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de guardar.")
            return
        if self.current_trabajo_info['estado_anterior']=="Terminado":
            wrong_entries = self.validate_fields()
            if wrong_entries:
                self.show_message("Error", "Campos inválidos", f"Revisar los campos: \n-{"\n-".join(wrong_entries)}")
                return
        
        form_data = self.get_form_data()
        form_data['user_id'] = self.user_id
        form_data['trabajo_id'] = self.current_trabajo_id
        form_data['formulario_id'] = self.current_formulario_id
        form_data['PARTERNO'] = form_data['PATERNO']
        print(form_data)
        print("Datos del formulario que se enviarán:", json.dumps(form_data, indent=4))
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post('https://loverman.net/dbase/dga2024/api/api.php?action=saveForm', json=form_data)
                response.raise_for_status()
                if not silence:
                    self.show_message("Info", "Guardar", "Formulario guardado exitosamente.")
                    print("Formulario guardado:", form_data)

                break
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    if not silence:
                        self.show_message("Error", "Error al guardar formulario", str(e))
                        print(f"Error al guardar formulario: {e}")
                else:
                    print(f"Reintentando... intento {attempt + 1} de {max_retries}")

    def load_form(self, trabajo_id):
        self.clear_form()
        try:
            response = requests.get(f'{API_BASE_URL}getForm&trabajo_id={trabajo_id}')
            response.raise_for_status()
            form_data = response.json()
            for label_text, data in form_data.items():
                entry_type = data["type"]
                entry_value = data["value"]
                if not any(label == label_text for label, _ in self.entries):
                    if entry_type == "QLineEdit":
                        self.add_input_field(label_text, "text")
                    elif entry_type == "QComboBox":
                        self.add_input_field(label_text, "select", [])
                    elif entry_type == "QCheckBox":
                        self.add_input_field(label_text, "checkbox")
                    elif entry_type == "QTextEdit":
                        self.add_input_field(label_text, "textarea")
                    elif entry_type == "QDateEdit":
                        self.add_input_field(label_text, "date")
                for label, entry in self.entries:
                    if label == label_text:
                        if entry_type == "QLineEdit":
                            entry.setText(entry_value)
                        elif entry_type == "QComboBox":
                            index = entry.findText(entry_value)
                            if index >= 0:
                                entry.setCurrentIndex(index)
                        elif entry_type == "QCheckBox":
                            entry.setChecked(entry_value)
                        elif entry_type == "QTextEdit":
                            entry.setPlainText(entry_value)
                        elif entry_type == "QDateEdit":
                            entry.setDate(QDate.fromString(entry_value, "dd/MM/yyyy"))
            print("Formulario cargado:", form_data)
            
        except requests.RequestException as e:
            print(f"Fallo cargar: {e}")
            self.show_message("Error", "Error al cargar formulario", str(e))
            
    def clear_form(self):
        for _, entry in self.entries:
            if isinstance(entry, QLineEdit):
                entry.clear()
            elif isinstance(entry, QComboBox):
                entry.setCurrentIndex(-1)
            elif isinstance(entry, QDateEdit):
                entry.setDate(QDate.fromString("01/01/1985", "dd/MM/yyyy"))
            elif isinstance(entry, QTextEdit):
                entry.clear()
            elif isinstance(entry, QCheckBox):
                entry.setChecked(False)
        print("Formulario limpiado")

    def submit_form(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de guardar.")
            return
        wrong_entries = self.validate_fields()
        if wrong_entries:
            self.show_message("Error", "Campos inválidos", f"Revisar los campos: \n-{"\n-".join(wrong_entries)}")
            return
        self.save_form()
        self.update_trabajo_estado("Terminado")
        self.load_trabajos()
        self.clear_pdf_viewer()
        self.clear_pdf_list()
        self.current_trabajo_id = None
        self.skip_inscription_button.setEnabled(False)
        self.devolver_button.setEnabled(False)

    def clear_pdf_list(self):
        self.pdf_listbox.clear()
        self.pdf_paths = []

    def clear_pdf_viewer(self):
        self.browser.setUrl(QUrl())
        
    def update_trabajo_estado(self, estado):
        try:
            if not self.current_trabajo_id or not self.current_formulario_id:
                self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de guardar.")
                return
            if self.current_trabajo_info['estado_anterior'] != "Terminado":
                response = requests.post(f'{API_BASE_URL}updateTrabajoEstado', json={
                    'trabajo_id': self.current_trabajo_id,
                    'estado': estado
                })
                response.raise_for_status()
                response_data = response.json()
                
                self.show_message("Info", "Estado Actualizado", f"El estado del trabajo se ha actualizado a {estado}.")
                self.scroll_area.verticalScrollBar().setValue(0)
                
                terminados_count = None
                if 'terminados_count' in response_data:
                    terminados_count = response_data['terminados_count']
                    self.set_title(terminados_count)

                history_record = {
                    "numero_trabajo":self.current_trabajo_info['numero_trabajo'],
                    "anio_trabajo": self.current_trabajo_info['anio_trabajo'],
                    "estado_anterior": self.current_trabajo_info['estado_anterior'],
                    "estado_nuevo": estado,
                    "terminados_count": terminados_count,
                    "datetime": self.get_datetime()
                }
                
                self.session_history.insert(0, history_record)

        except requests.RequestException as e:
            self.show_message("Error", "Error al actualizar estado", str(e))
            print(f"Error al actualizar estado: {e}")

    def open_inscription_modal(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de continuar.")
            return
        if self.modal_abierto:
            self.show_message("Error", "Acción no permitida", "Ya hay un modal abierto.")
            return
        self.modal_abierto = True
        self.inscription_modal = InscriptionModal(self)
        self.inscription_modal.show()
        self.inscription_modal.finished.connect(self.on_modal_closed)

        
    def open_usuarios_modal(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de continuar.")
            return
        if self.modal_abierto:
            self.show_message("Error", "Acción no permitida", "Ya hay un modal abierto.")
            return
        
        self.modal_abierto = True
        self.usuario_modal = UsuarioModal(self)
        self.usuario_modal.show() 
        self.usuario_modal.finished.connect(self.on_modal_closed)
        
        if self.usuario_modal.loaded_ruts_with_error:
            message = "Los siguientes ruts son inválidos:\n"
            for rut in self.usuario_modal.loaded_ruts_with_error:
                message += f"\n'{rut}'"
            self.show_message("Info", "Ruts inválidos", message)
        
    def open_history_modal(self, history_list):
        if self.modal_abierto:
            self.show_message("Error", "Acción no permitida", "Ya hay un modal abierto.")
            return
        self.modal_abierto = True
        self.history_modal = HistoryModal(self, history_list=history_list)
        self.history_modal.show()
        self.history_modal.finished.connect(self.on_modal_closed)
        

    def open_detalles_modal(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de continuar.")
            return
        if self.modal_abierto:
            self.show_message("Error", "Acción no permitida", "Ya hay un modal abierto.")
            return
        
        self.modal_abierto = True
        self.details_modal = DetallesModal(self)
        self.details_modal.show()
        self.details_modal.finished.connect(self.on_modal_closed)

    def on_modal_closed(self):
        self.modal_abierto = False 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    next_window = NextWindow(1, "Edinson", 0, False)
    next_window.showMaximized()
    next_window.show()
    sys.exit(app.exec_())
        

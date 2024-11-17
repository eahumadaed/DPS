from PyQt5.QtCore import Qt, QRect, QUrl
from PyQt5.QtGui import QPainter, QColor, QCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStyle
from PyQt5.QtWebEngineWidgets import QWebEngineView


class DrawSquareWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(parent.geometry())
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setMouseTracking(True)
        self.rect = None
        self.drawing = False
        self.rects = []
        self.setStyleSheet("background: transparent;")
        style = self.style()
        self.trash_cursor = QCursor(style.standardIcon(QStyle.SP_MessageBoxCritical).pixmap(27, 27))
        self.drawing_cursor = QCursor(Qt.CrossCursor)

        self.setCursor(self.drawing_cursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            clicked_pos = event.pos()

            for rect in self.rects:
                if rect.contains(clicked_pos):
                    self.rects.remove(rect)
                    self.update()
                    return
            self.start_pos = clicked_pos
            self.rect = QRect(self.start_pos, self.start_pos).normalized()
            self.drawing = True
            self.update()
        event.accept()

    def mouseMoveEvent(self, event):
        hovered_pos = event.pos()
        cursor_changed = False

        for rect in self.rects:
            if rect.contains(hovered_pos):
                self.setCursor(self.trash_cursor) 
                cursor_changed = True
                break

        if not cursor_changed:
            self.setCursor(self.drawing_cursor)

        if self.drawing:
            self.rect = QRect(self.start_pos, event.pos()).normalized()
            self.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton and self.rect:
            self.drawing = False
            self.rects.append(self.rect)
            self.rect = None
            self.update()
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        event.accept()
    
    def wheelEvent(self, event):
        
        event.ignore()

    def paintEvent(self, event):
        painter = QPainter(self)

        for rect in self.rects:
            painter.setPen(QColor(0, 0, 255, 0))
            painter.setBrush(QColor(0, 0, 255, 50))
            painter.drawRoundedRect(rect, 10, 10)

        if self.rect:
            painter.setPen(Qt.red)
            painter.setBrush(QColor(255, 0, 0, 40))
            painter.drawRoundedRect(self.rect, 10, 10)


class CustomWebEngineView(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.setHtml("<body></body>")
        self.setGeometry(0, 0, 800, 600)

        self.selection_widget = DrawSquareWidget(self)
        self.selection_widget.setGeometry(self.geometry())
        self.selection_widget.show()
        self.zoom_factor = 1.0
        self.selection_widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.ignoreZoom = True

    def load(self, url):
        self.selection_widget.rect = None
        self.selection_widget.update()
        super().load(url)
        self.selection_widget.raise_()

    def setUrl(self, url):
        super().setUrl(url)
        self.selection_widget.raise_()

    def resizeEvent(self, event):
        self.selection_widget.setGeometry(self.geometry())
        super().resizeEvent(event)

    # CAPTURAR CLIC DERECHO DE ESTA MANERA EN EL NAV
    def contextMenuEvent(self, event):
        self.selection_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        event.accept()

    def wheelEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.ControlModifier and not self.ignoreZoom:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
        else:
            super().wheelEvent(event)
            
    def zoom_in(self):
        self.zoom_factor *= 1.1
        self.set_zoom(self.zoom_factor)

    def zoom_out(self):
        self.zoom_factor *= 0.9
        self.set_zoom(self.zoom_factor)

    def set_zoom(self, factor):
        self.setZoomFactor(factor)
    
    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.set_zoom(self.zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selection_widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selection_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        return super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Browser with Drawing")
        self.showMaximized()
        self.browser = CustomWebEngineView()
        self.browser.setHtml("""
        <head>
            <style>
                body {
                    max-width: 600px;
                    margin: 0 auto;
                    word-wrap: break-word;
                }
                button {
                padding: 10px 20px;
                background-color: black;
                color: white;
                border: none;
                cursor: pointer;
                width: 300px;
            }
            </style>
        </head>
        <body>
            <h1>PÁGINA DE PRUEBA</h1>
            <button id="toggleButton">Botón de prueba</button>
            <p>Deserunt veniam do non aliqua eu proident cupidatat aute aute deserunt. Fugiat cupidatat enim qui ex culpa proident sint. Esse do commodo aliquip cupidatat proident laborum. Nostrud incididunt enim irure ut duis proident cupidatat commodo amet mollit ullamco proident nulla enim. Minim labore aute occaecat reprehenderit. Nostrud labore eu minim adipisicing Lorem aute.</p>
            <p>Et excepteur quis magna voluptate anim in ea adipisicing ea do ea. Nulla velit incididunt consequat anim ipsum anim consequat esse velit adipisicing minim tempor fugiat. Eiusmod velit laborum consequat ad dolor laborum ipsum minim ad qui. Minim minim voluptate mollit tempor ut culpa minim dolore fugiat ex aute fugiat. Anim occaecat est veniam consequat non anim dolor incididunt est. Irure qui sit non aliquip cillum. In consequat consectetur cupidatat cillum sit elit id nulla ut fugiat incididunt dolore do incididunt.</p>
            <p>Dolor enim Lorem irure aute in nulla Lorem nulla consequat. Proident eu Lorem deserunt esse laboris occaecat. Nisi dolore tempor ut do mollit laboris aliqua velit sint aliquip commodo.</p>
            <p>Qui culpa aliqua sint commodo laborum consectetur. Nulla exercitation quis elit anim veniam nisi culpa sunt in exercitation sit dolore ut. Do aliquip do voluptate culpa in duis ullamco elit et sint nulla quis pariatur adipisicing. Qui elit do amet minim proident laboris veniam sint aute veniam incididunt velit. Sunt do quis occaecat cillum. Fugiat duis occaecat consequat sint ipsum. Aliqua eiusmod laboris amet commodo voluptate Lorem ex.</p>
            <p>Eu et cupidatat laboris culpa cillum elit exercitation quis culpa sunt adipisicing voluptate anim magna. Aliqua eu id culpa velit nisi enim labore consequat non. Exercitation proident minim aute tempor fugiat Lorem fugiat excepteur. Id cupidatat quis id magna pariatur exercitation nisi incididunt reprehenderit qui ipsum Lorem laboris. Ad non est excepteur nulla proident enim esse sit eu.</p>
            <p>Occaecat commodo quis aute ullamco ut. Officia excepteur mollit esse ullamco exercitation velit et labore fugiat ex elit est mollit. Duis adipisicing sunt nostrud qui officia ea velit.</p>
            <p>Deserunt veniam do non aliqua eu proident cupidatat aute aute deserunt. Fugiat cupidatat enim qui ex culpa proident sint. Esse do commodo aliquip cupidatat proident laborum. Nostrud incididunt enim irure ut duis proident cupidatat commodo amet mollit ullamco proident nulla enim. Minim labore aute occaecat reprehenderit. Nostrud labore eu minim adipisicing Lorem aute.</p>
            <p>Et excepteur quis magna voluptate anim in ea adipisicing ea do ea. Nulla velit incididunt consequat anim ipsum anim consequat esse velit adipisicing minim tempor fugiat. Eiusmod velit laborum consequat ad dolor laborum ipsum minim ad qui. Minim minim voluptate mollit tempor ut culpa minim dolore fugiat ex aute fugiat. Anim occaecat est veniam consequat non anim dolor incididunt est. Irure qui sit non aliquip cillum. In consequat consectetur cupidatat cillum sit elit id nulla ut fugiat incididunt dolore do incididunt.</p>
            <p>Dolor enim Lorem irure aute in nulla Lorem nulla consequat. Proident eu Lorem deserunt esse laboris occaecat. Nisi dolore tempor ut do mollit laboris aliqua velit sint aliquip commodo.</p>
            <p>Qui culpa aliqua sint commodo laborum consectetur. Nulla exercitation quis elit anim veniam nisi culpa sunt in exercitation sit dolore ut. Do aliquip do voluptate culpa in duis ullamco elit et sint nulla quis pariatur adipisicing. Qui elit do amet minim proident laboris veniam sint aute veniam incididunt velit. Sunt do quis occaecat cillum. Fugiat duis occaecat consequat sint ipsum. Aliqua eiusmod laboris amet commodo voluptate Lorem ex.</p>
            <p>Eu et cupidatat laboris culpa cillum elit exercitation quis culpa sunt adipisicing voluptate anim magna. Aliqua eu id culpa velit nisi enim labore consequat non. Exercitation proident minim aute tempor fugiat Lorem fugiat excepteur. Id cupidatat quis id magna pariatur exercitation nisi incididunt reprehenderit qui ipsum Lorem laboris. Ad non est excepteur nulla proident enim esse sit eu.</p>
            <p>Occaecat commodo quis aute ullamco ut. Officia excepteur mollit esse ullamco exercitation velit et labore fugiat ex elit est mollit. Duis adipisicing sunt nostrud qui officia ea velit.</p>
            <script>
                const button = document.getElementById('toggleButton');
                button.onclick = function() {
                    if (button.style.backgroundColor === 'black') {
                        button.style.backgroundColor = 'red';
                    } else {
                        button.style.backgroundColor = 'black';
                    }
                };
            </script>
        </body>
        """)
        self.setCentralWidget(self.browser)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()

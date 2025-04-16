#!/usr/bin/env python

import io
import requests
import sys
import pyautogui
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QDialog, QMenuBar, QToolBar, QStatusBar, QLabel, QTextEdit, QGridLayout
from PySide6.QtGui import QAction, QPixmap, QScreen, QMouseEvent, QPainter, QPen
from PySide6.QtCore import Qt
from PySide6.QtCore import QThread, QObject, Signal
from PIL.ImageQt import ImageQt

class ShowRectDialog(QDialog):
    def __init__(self, rect:tuple[int,int,int,int]):
        self.rect = rect
        super().__init__()
        self.setModal = True
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.5)
        self.showFullScreen()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        x, y, w, h = self.rect
        painter = QPainter(self)
        pen = QPen(Qt.red, 2, Qt.SolidLine)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(x, y, w, h)

    def mouseReleaseEvent(self, event:QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.accept()

class CaptureRectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setModal = True
        self.is_drawing = False
        self.captured_rect:list[int,int,int,int] = [0, 0, 0, 0] # x, y, w, h
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.5)
        self.showFullScreen()

    def mousePressEvent(self, event:QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            globalPos = event.globalPosition()
            self.captured_rect[0] = int(globalPos.x())
            self.captured_rect[1] = int(globalPos.y())

    def updateCapturedRect(self, event:QMouseEvent):
        globalPos = event.globalPosition()
        x = int(globalPos.x())
        y = int(globalPos.y())
        self.captured_rect[2] = x - self.captured_rect[0]
        self.captured_rect[3] = y - self.captured_rect[1]

    def mouseMoveEvent(self, event:QMouseEvent) -> None:
        self.updateCapturedRect(event)
        self.is_drawing = True
        self.repaint()

    def mouseReleaseEvent(self, event:QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.updateCapturedRect(event)
            self.accept()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.is_drawing:
            x, y, w, h = self.captured_rect
            painter = QPainter(self)
            pen = QPen(Qt.red, 2, Qt.SolidLine)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(x, y, w, h)

    def keyPressEvent(self, event):
        print(event.key())
        if event.key() == Qt.Key_Escape:
            QApplication.quit()

class WorkerSignals(QObject):
    status = Signal(str)
    error = Signal(str)
    ocr_result = Signal(str)
    finished = Signal()

class ServerWorker(QObject):

    process_image_signal = Signal(object)

    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.process_image_signal.connect(self.process_image)

    def process_image(self, img_buf:memoryview):
        try:
            self.signals.status.emit(f"OCR")
            res1 = requests.post("http://localhost:8000", img_buf)
            if res1.status_code == 200:
                ocr_text = res1.text
                self.signals.ocr_result.emit(ocr_text)
            else:
                self.signals.error.emit(f"status: {res1.status_code}")
        except Exception as e:
            self.signals.error.emit(f"exception: {str(e)}")

class MainWindow(QMainWindow):
    N_MSG_ROWS = 3

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test App")
        self.resize(800, 700)

        self.scaled_rect:list[int,int,int,int] = [0, 0, 200, 100]
        self._init_gui()
        self._init_thread()

    def __del__(self):
        self.ocr_thread.quit()
        self.ocr_thread.wait()

    def _init_gui(self):
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu("File")
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(quit_action)
        self.setMenuBar(menu_bar)

        tool_bar = QToolBar("ToolBar1", self)
        tool_bar.addAction("Action1")
        tool_bar.addAction("Action2")
        self.addToolBar(tool_bar)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        self.setStatusBar(self.status_bar)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout1 = QVBoxLayout(central_widget)
        layout1.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout1_1 = QHBoxLayout()
        layout1.insertLayout(0, layout1_1)
        layout1_1_1 = QVBoxLayout()
        layout1_1.insertLayout(0, layout1_1_1)

        self.btn_show_area = QPushButton("Show Area")
        self.btn_show_area.clicked.connect(self._btn_show_area_clicked)
        layout1_1_1.addWidget(self.btn_show_area)
        self.btn_set_area = QPushButton("Set Area")
        self.btn_set_area.clicked.connect(self._btn_set_area_clicked)
        layout1_1_1.addWidget(self.btn_set_area)
        self.btn_capture = QPushButton("Capture")
        self.btn_capture.clicked.connect(self._btn_capture_clicked)
        layout1_1_1.addWidget(self.btn_capture)
        self.ted_text_in = QTextEdit()
        layout1.addWidget(self.ted_text_in)

        self.lbl_image = QLabel("Image")
        layout1_1.addWidget(self.lbl_image)

        layout1_2 = QGridLayout()
        self.ted_messages:list[list[QLabel]] = []
        for row_i in range(self.N_MSG_ROWS):
            self.ted_messages.append([])
            for col_i in range(2):
                tmp_tedit = QTextEdit(f"{row_i} {col_i}")
                self.ted_messages[row_i].append(tmp_tedit)
                layout1_2.addWidget(tmp_tedit, row_i, col_i)
        layout1.addLayout(layout1_2)

    def _init_thread(self):
        self.ocr_thread = QThread()
        self.worker = ServerWorker()
        self.worker.moveToThread(self.ocr_thread)
        self.worker.signals.status.connect(self.recv_status)
        self.worker.signals.error.connect(self.recv_error)
        self.worker.signals.ocr_result.connect(self.recv_ocr_result)
        self.worker.signals.finished.connect(self.recv_finished)
        self.ocr_thread.start()

    def _btn_show_area_clicked(self):
        dialog = ShowRectDialog(self.scaled_rect)
        dialog.exec()
        self.status_bar.showMessage(f"{self.scaled_rect}")

    def _btn_set_area_clicked(self):
        self._get_scaling()
        dialog = CaptureRectDialog()
        if dialog.exec():
            self.scaled_rect = dialog.captured_rect

    def _btn_capture_clicked(self):
        self.status_bar.showMessage("clicked")
        rect = self._calc_rect()
        pil_img = pyautogui.screenshot(region=rect)
        qim = ImageQt(pil_img)
        orig_pixmap = QPixmap.fromImage(qim)
        pixmap = orig_pixmap.scaled(400, 100, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.lbl_image.setPixmap(pixmap)

        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format="PNG")
        img_buf = img_byte_arr.getbuffer()
        self.worker.process_image_signal.emit(img_buf)

    def _get_scaling(self) -> float:
        window_handle = self.windowHandle()
        if not window_handle:
            self.status_bar.showMessage("Error: No window handle")
            return 1.0
        screen = window_handle.screen()
        if not screen:
            self.status_bar.showMessage("Error: no screen found")
            return 1.0
        scaling = screen.devicePixelRatio()
        self.status_bar.showMessage(f"Scaling: {scaling}")
        return scaling

    def _calc_rect(self) -> tuple[int,int,int,int]:
        scaling = self._get_scaling()
        rect = [int(v * scaling) for v in self.scaled_rect]
        return tuple(rect)

    def recv_status(self, message:str):
        self.status_bar.showMessage(message)

    def recv_error(self, error_message:str):
        self.status_bar.showMessage(f"Error: {error_message}")

    def recv_ocr_result(self, ocr_text:str):
        self.ted_text_in.setText(ocr_text)

    def recv_finished(self):
        print("process_finished")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

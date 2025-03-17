#!/usr/bin/env python

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QDialog, QLabel, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QMouseEvent, QFont

g_captured_rect:list[int,int,int,int] = [0, 0, 0, 0]

class CaptureRectWindow(QDialog):
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
        #super().mouseMoveEvent(event)
        self.updateCapturedRect(event)
        self.is_drawing = True
        self.repaint()
        return

    def mouseReleaseEvent(self, event:QMouseEvent) -> None:
        global g_captured_rect
        if event.button() == Qt.MouseButton.LeftButton:
            self.updateCapturedRect(event)
            g_captured_rect = self.captured_rect
            self.close()

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
        if event.key() == Qt.Key_Escape:
            QApplication.quit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window")

        self.capture_rect:tuple[int,int,int,int] = (400, 300, 600, 200) # x, y, w, h

        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.layout = QVBoxLayout()
        self.centralWidget.setLayout(self.layout)
        self.layout2 = QHBoxLayout()
        self.layout.addLayout(self.layout2)
        self.button_select_rect = QPushButton("Select Rect")
        self.button_select_rect.clicked.connect(self.select_rect)
        self.label_capture_rect = QLabel(f"capture text in: {self.capture_rect}")
        self.layout2.addWidget(self.button_select_rect)
        self.layout2.addWidget(self.label_capture_rect)

        self.button_start_stop = QPushButton("Start")
        self.button_start_stop.clicked.connect(self.start_stop_clicked)
        self.layout.addWidget(self.button_start_stop)

        font = QFont()
        font.setPointSize(16)
        self.textEdit_in = QTextEdit()
        self.textEdit_in.setFont(font)
        self.textEdit_in.setReadOnly(True)
        self.layout.addWidget(self.textEdit_in)

    def select_rect(self):
        #self.capture_rect = (int(self.line_edit_x.text()), int(self.line_edit_y.text()), int(self.line_edit_w.text()), int(self.line_edit_h.text()))
        self.capture_rect_window = CaptureRectWindow()
        self.capture_rect_window.finished.connect(self.captureRectFinished)
        self.capture_rect_window.show()

    def captureRectFinished(self, result:int):
        #print(f"captureRectFinished {g_captured_rect}")
        self.capture_rect = g_captured_rect
        self.label_capture_rect.setText(f"capture text in: {self.capture_rect}")

    def start_stop_clicked(self, event):
        print(f"start")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    #window = FullScreenWindow()
    sys.exit(app.exec())

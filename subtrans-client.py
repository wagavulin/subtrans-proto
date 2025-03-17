#!/usr/bin/env python

#%%
import sys
import requests
import numpy as np
import easyocr
import matplotlib.pyplot as plt
import PySide6
from PySide6 import QtCore, QtWidgets, QtGui
import pyautogui

#%%
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Subtrans")
        self.setGeometry(100, 100, 800, 600)
        self.ocr_reader = easyocr.Reader(['en'])
        self.capture_rect:tuple[int,int,int,int] = (400, 300, 600, 200) # x, y, w, h
        self.initUI()

    def initUI(self):
        self.centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralWidget)
        self.layout = QtWidgets.QVBoxLayout()
        self.centralWidget.setLayout(self.layout)

        self.layout2 = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.layout2)
        self.line_edit_x = QtWidgets.QLineEdit(str(self.capture_rect[0]))
        self.line_edit_y = QtWidgets.QLineEdit(str(self.capture_rect[1]))
        self.line_edit_w = QtWidgets.QLineEdit(str(self.capture_rect[2]))
        self.line_edit_h = QtWidgets.QLineEdit(str(self.capture_rect[3]))
        self.button_apply_rect = QtWidgets.QPushButton("Apply")
        self.layout2.addWidget(self.line_edit_x)
        self.layout2.addWidget(self.line_edit_y)
        self.layout2.addWidget(self.line_edit_w)
        self.layout2.addWidget(self.line_edit_h)
        self.layout2.addWidget(self.button_apply_rect)

        font = QtGui.QFont()
        font.setPointSize(16)

        self.textEdit_in = QtWidgets.QTextEdit()
        self.textEdit_in.setFont(font)
        self.layout.addWidget(self.textEdit_in)
        self.textEdit_out = QtWidgets.QTextEdit()
        self.textEdit_out.setFont(font)
        self.layout.addWidget(self.textEdit_out)

        self.button = QtWidgets.QPushButton("Translate")
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.translate)

    def translate(self):
        print("translate")
        pil_img = pyautogui.screenshot(region=(600,300, 200, 200))
        pil_img.save("ss.png")
        img = np.asarray(pil_img)
        result = self.ocr_reader.readtext(img, detail=0)
        #plt.imshow(img)
        self.textEdit_in.setText(result[0])
        return

        text_in = self.textEdit_in.toPlainText()
        server = "http://localhost:8000"
        res = requests.post(server, text_in)
        self.textEdit_out.setText(res.text)

app = QtWidgets.QApplication(sys.argv)
win = MainWindow()
win.show()
app.exec()

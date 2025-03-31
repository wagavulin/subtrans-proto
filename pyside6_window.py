import sys
import io
import pyautogui
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton,
    QDialog, QGridLayout, QSpinBox, QDialogButtonBox
)
from PySide6.QtCore import QTimer, QThread, Signal, QObject
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QMouseEvent

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
        #super().mouseReleaseEvent(event)

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


class CaptureAreaDialog(QDialog):
    """キャプチャ範囲を指定するためのダイアログ"""
    def __init__(self, parent=None, x=250, y=920, width=500, height=50):
        super().__init__(parent)
        self.setWindowTitle("キャプチャ範囲を指定")
        self.setMinimumWidth(300)
        
        # レイアウトを作成
        layout = QGridLayout(self)
        
        # X座標
        layout.addWidget(QLabel("X座標:"), 0, 0)
        self.x_spinbox = QSpinBox()
        self.x_spinbox.setRange(0, 3000)
        self.x_spinbox.setValue(x)
        layout.addWidget(self.x_spinbox, 0, 1)
        
        # Y座標
        layout.addWidget(QLabel("Y座標:"), 1, 0)
        self.y_spinbox = QSpinBox()
        self.y_spinbox.setRange(0, 3000)
        self.y_spinbox.setValue(y)
        layout.addWidget(self.y_spinbox, 1, 1)
        
        # 幅
        layout.addWidget(QLabel("幅:"), 2, 0)
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(10, 3000)
        self.width_spinbox.setValue(width)
        layout.addWidget(self.width_spinbox, 2, 1)
        
        # 高さ
        layout.addWidget(QLabel("高さ:"), 3, 0)
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(10, 3000)
        self.height_spinbox.setValue(height)
        layout.addWidget(self.height_spinbox, 3, 1)
        
        # ボタン
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box, 4, 0, 1, 2)
    
    def get_values(self):
        """ダイアログで設定された値を取得する"""
        return {
            'x': self.x_spinbox.value(),
            'y': self.y_spinbox.value(),
            'width': self.width_spinbox.value(),
            'height': self.height_spinbox.value()
        }


class WorkerSignals(QObject):
    """ワーカースレッドからのシグナルを定義するクラス"""
    status = Signal(str)  # 状態メッセージを送信するシグナル
    error = Signal(str)   # エラーメッセージを送信するシグナル
    result = Signal(str)  # 最終結果を送信するシグナル
    finished = Signal()   # 処理完了を通知するシグナル


class ServerWorker(QObject):
    """サーバー通信を非同期で行うワーカークラス"""
    # 画像処理を開始するためのシグナル
    process_image_signal = Signal(object)
    
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        
        # シグナルをスロットに接続
        self.process_image_signal.connect(self.process_image)
        
    def process_image(self, img_data):
        """画像データを処理し、サーバーに送信する"""
        try:
            # 最初のサーバーにHTTPリクエストを送信
            self.signals.status.emit("画像をサーバー(8000)に送信中...")
            response1 = requests.post(
                'http://localhost:8000',
                img_data
            )
            
            # 最初のサーバーからのレスポンスを確認
            if response1.status_code == 200:
                first_response = response1.text
                self.signals.status.emit(f"サーバー(8000)からの応答: {first_response}、次のサーバーに送信中...")
                print(f"OCR: {first_response}")
                
                # 2番目のサーバーに最初のレスポンスを送信
                try:
                    response2 = requests.post(
                        'http://localhost:8001',
                        data=first_response
                    )
                    
                    # 2番目のサーバーからのレスポンスを表示
                    if response2.status_code == 200:
                        self.signals.result.emit(response2.text)
                        print(f"  {response2.text}")
                    else:
                        self.signals.error.emit(f"サーバー(8001)エラー: ステータスコード {response2.status_code}")
                except Exception as e:
                    self.signals.error.emit(f"サーバー(8001)通信エラー: {str(e)}")
            else:
                self.signals.error.emit(f"サーバー(8000)エラー: ステータスコード {response1.status_code}")
        except Exception as e:
            self.signals.error.emit(f"サーバー(8000)通信エラー: {str(e)}")
        finally:
            self.signals.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # キャプチャ範囲の初期設定
        self.capture_area = {
            'x': 250,
            'y': 920,
            'width': 500,
            'height': 50
        }
        
        # ウィンドウのタイトルを設定
        self.setWindowTitle("PySide6 ウィンドウ")
        
        # ウィンドウのサイズを設定
        self.setGeometry(100, 100, 400, 300)
        
        # 中央ウィジェットを作成
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # レイアウトを作成
        layout = QVBoxLayout(central_widget)
        
        # ラベルを追加
        label = QLabel("PySide6でウィンドウを表示しています")
        label.setStyleSheet("font-size: 16px; margin: 20px;")
        layout.addWidget(label)
        
        # キャプチャ範囲を指定するボタンを追加
        self.set_area_button = QPushButton("キャプチャ範囲を指定")
        self.set_area_button.setStyleSheet("font-size: 14px; padding: 10px;")
        self.set_area_button.clicked.connect(self.set_capture_area)
        layout.addWidget(self.set_area_button)
        
        # キャプチャボタンを追加
        self.capture_button = QPushButton("Start Capture")
        self.capture_button.setStyleSheet("font-size: 14px; padding: 10px;")
        self.capture_button.clicked.connect(self.toggle_capture)
        layout.addWidget(self.capture_button)
        
        # 状態表示用ラベル
        self.status_label = QLabel("ボタンをクリックすると画面の一部をキャプチャします")
        layout.addWidget(self.status_label)
        
        self.capture_timer = QTimer(self)
        self.capture_timer.timeout.connect(self._take_screenshot)
        
        # サーバー通信用のワーカーとスレッドを初期化
        self.thread = QThread()
        self.worker = ServerWorker()
        self.worker.moveToThread(self.thread)
        
        # ワーカーのシグナルをスロットに接続
        self.worker.signals.status.connect(self.update_status)
        self.worker.signals.error.connect(self.show_error)
        self.worker.signals.result.connect(self.show_result)
        self.worker.signals.finished.connect(self.process_finished)
        
        # スレッドを開始
        self.thread.start()
        
    def __del__(self):
        # アプリケーション終了時にスレッドを終了
        self.thread.quit()
        self.thread.wait()
    
    def toggle_capture(self):
        if self.capture_button.text() == "Start Capture":
            self.capture_timer.start(5000)
            self.capture_button.setText("End Capture")
        else:
            self.capture_button.setText("Start Capture")
            self.capture_timer.stop()
        #self.status_label.setText("1秒後にキャプチャします...")

        # 1秒後にキャプチャを実行（ウィンドウを最小化する時間を確保）
        #QTimer.singleShot(1000, self._perform_capture)

    def _func1(self):
        print("_func1")
    
    def _perform_capture(self):
        try:
            # ウィンドウを最小化（キャプチャ対象から外すため）
            self.showMinimized()
            
            # 少し待機してウィンドウが最小化されるのを待つ
            QTimer.singleShot(500, lambda: self._take_screenshot())
        except Exception as e:
            self.status_label.setText(f"エラー: {str(e)}")
            self.showNormal()
    
    def set_capture_area(self):
        global g_captured_rect
        dialog = CaptureRectWindow()
        dialog.exec()
        rect = g_captured_rect
        sys.stdout.flush()
        self.capture_area["x"] = int(rect[0] * 3 / 2)
        self.capture_area["y"] = int(rect[1] * 3 / 2)
        self.capture_area["width"] = int(rect[2] * 3 / 2)
        self.capture_area["height"] = int(rect[3] * 3 / 2)
        self.status_label.setText(
            f"キャプチャ範囲を設定しました: X={self.capture_area['x']}, Y={self.capture_area['y']}, "
            f"幅={self.capture_area['width']}, 高さ={self.capture_area['height']}"
        )

    def set_capture_area2(self):
        """キャプチャ範囲を指定するダイアログを表示する"""
        dialog = CaptureAreaDialog(
            self,
            x=self.capture_area['x'],
            y=self.capture_area['y'],
            width=self.capture_area['width'],
            height=self.capture_area['height']
        )
        
        # ダイアログを表示し、OKボタンがクリックされた場合は値を保存
        if dialog.exec():
            self.capture_area = dialog.get_values()
            self.status_label.setText(
                f"キャプチャ範囲を設定しました: X={self.capture_area['x']}, Y={self.capture_area['y']}, "
                f"幅={self.capture_area['width']}, 高さ={self.capture_area['height']}"
            )
    
    def _take_screenshot(self):
        try:
            print("_take_screenshot")
            # 設定されたキャプチャ範囲を使用
            x = self.capture_area['x']
            y = self.capture_area['y']
            width = self.capture_area['width']
            height = self.capture_area['height']
            
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            #screenshot.save("tmp-ss.png")
            
            # 画像をPNGとしてバイトストリームにエンコード
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_buf = img_byte_arr.getbuffer()
            
            # ウィンドウを元に戻す
            self.showNormal()
            self.status_label.setText("サーバーに画像を送信中...")
            
            # 非同期でサーバー通信を実行
            # シグナルを発行してワーカースレッドでprocess_imageメソッドを実行
            self.worker.process_image_signal.emit(img_buf)
            
            # キャプチャボタンを一時的に無効化（処理完了まで）
            self.capture_button.setEnabled(False)
        except Exception as e:
            self.status_label.setText(f"キャプチャエラー: {str(e)}")
            self.showNormal()
    
    # ワーカーからのシグナルを受け取るスロット
    def update_status(self, message):
        """ステータスメッセージを更新するスロット"""
        self.status_label.setText(message)
    
    def show_error(self, error_message):
        """エラーメッセージを表示するスロット"""
        self.status_label.setText(f"エラー: {error_message}")
        self.capture_button.setEnabled(True)
    
    def show_result(self, result):
        """最終結果を表示するスロット"""
        self.status_label.setText(f"最終応答: {result}")
        self.capture_button.setEnabled(True)
    
    def process_finished(self):
        """処理完了時に呼び出されるスロット"""
        # 処理が完了したらキャプチャボタンを再度有効化
        self.capture_button.setEnabled(True)

def main():
    # アプリケーションを作成
    app = QApplication(sys.argv)
    
    # メインウィンドウを作成
    window = MainWindow()
    
    # ウィンドウを表示
    window.show()
    
    # アプリケーションのイベントループを開始
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

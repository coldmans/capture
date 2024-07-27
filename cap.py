import sys
import time
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit, QFileDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QDialog
from PyQt5.QtCore import Qt, QRect, QTimer
from PyQt5.QtGui import QPainter, QPen, QPixmap, QImage
from PIL import ImageGrab, Image
import io

class ScreenshotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.is_drawing = False
        self.preview_window = None

    def initUI(self):
        self.setWindowTitle('Screenshot Automation')
        self.setGeometry(100, 100, 400, 300)

        self.save_path_label = QLabel('저장경로:', self)
        self.save_path_input = QLineEdit(self)
        self.browse_button = QPushButton('경로지정', self)
        self.browse_button.clicked.connect(self.browse_folder)
        self.desktop_button = QPushButton('바탕화면', self)
        self.desktop_button.clicked.connect(self.set_desktop_path)

        self.region_label = QLabel('캡쳐 범위:', self)
        self.region_input = QLineEdit(self)
        self.region_input.setReadOnly(True)

        self.interval_label = QLabel('연속캡쳐 (초):', self)
        self.interval_input = QLineEdit(self)

        self.count_label = QLabel('캡쳐할 장 수:', self)
        self.count_input = QLineEdit(self)

        self.hide_window_checkbox = QCheckBox('캡쳐 시 창 숨기기', self)

        self.start_button = QPushButton('캡쳐 시작', self)
        self.start_button.clicked.connect(self.start_capture)

        self.set_capture_area_button = QPushButton('캡쳐 범위 지정', self)
        self.set_capture_area_button.clicked.connect(self.set_capture_area)
        self.fullscreen_button = QPushButton('전체화면', self)
        self.fullscreen_button.clicked.connect(self.set_fullscreen_area)

        save_path_layout = QHBoxLayout()
        save_path_layout.addWidget(self.save_path_input)
        save_path_layout.addWidget(self.browse_button)
        save_path_layout.addWidget(self.desktop_button)

        capture_area_layout = QHBoxLayout()
        capture_area_layout.addWidget(self.set_capture_area_button)
        capture_area_layout.addWidget(self.fullscreen_button)

        layout = QVBoxLayout()
        layout.addWidget(self.save_path_label)
        layout.addLayout(save_path_layout)
        layout.addWidget(self.region_label)
        layout.addWidget(self.region_input)
        layout.addLayout(capture_area_layout)
        layout.addWidget(self.interval_label)
        layout.addWidget(self.interval_input)
        layout.addWidget(self.count_label)
        layout.addWidget(self.count_input)
        layout.addWidget(self.hide_window_checkbox)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.save_path_input.setText(folder)

    def set_desktop_path(self):
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        self.save_path_input.setText(desktop_path)

    def set_capture_area(self):
        self.is_drawing = True
        self.showFullScreen()
        self.setWindowOpacity(0.3)

    def set_fullscreen_area(self):
        screen_rect = QApplication.desktop().screenGeometry()
        self.start_x = screen_rect.left()
        self.start_y = screen_rect.top()
        self.end_x = screen_rect.right()
        self.end_y = screen_rect.bottom()
        self.region_input.setText(f"{self.start_x},{self.start_y},{self.end_x},{self.end_y}")

    def mousePressEvent(self, event):
        if self.is_drawing:
            self.start_x = event.x()
            self.start_y = event.y()
            self.end_x = None
            self.end_y = None

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_x = event.x()
            self.end_y = event.y()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_drawing:
            self.end_x = event.x()
            self.end_y = event.y()
            self.is_drawing = False
            self.setWindowOpacity(1.0)
            self.showNormal()
            self.region_input.setText(f"{self.start_x},{self.start_y},{self.end_x},{self.end_y}")
            self.update()

    def paintEvent(self, event):
        if self.is_drawing and self.end_x is not None and self.end_y is not None:
            rect = QRect(self.start_x, self.start_y, self.end_x - self.start_x, self.end_y - self.start_y)
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.drawRect(rect)

    def start_capture(self):
        save_path = self.save_path_input.text()
        region = self.region_input.text()
        interval = int(self.interval_input.text())
        count = int(self.count_input.text())
        hide_window = self.hide_window_checkbox.isChecked()

        if region:
            x1, y1, x2, y2 = map(int, region.split(','))
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])
            region = (x1, y1, x2, y2)
        else:
            region = None

        if hide_window:
            self.hide()
            QTimer.singleShot(1000, lambda: self.delayed_capture(save_path, region, interval, count))  # 캡쳐 시작 전에 1초 딜레이
        else:
            self.continuous_capture(save_path, region, interval, count)

    def delayed_capture(self, save_path, region, interval, count):
        self.continuous_capture(save_path, region, interval, count)
        QTimer.singleShot(interval * count * 1000 + 500, self.show)  # 캡쳐 완료 후 창 표시

    def capture_screenshot(self, save_path, region=None):
        screenshot = ImageGrab.grab(bbox=region)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_name = f"screenshot_{timestamp}.png"
        full_path = os.path.join(save_path, file_name)
        screenshot.save(full_path)
        print(f"Saved: {full_path}")

        self.copy_image_to_clipboard(screenshot)
        self.show_preview(screenshot)

    def copy_image_to_clipboard(self, image):
        output = io.BytesIO()
        image.save(output, format='PNG')
        data = output.getvalue()
        qim = QImage.fromData(data)
        clipboard = QApplication.clipboard()
        clipboard.setImage(qim)
        print("Image copied to clipboard")

    def continuous_capture(self, save_path, region=None, interval=5, count=10):
        def capture_and_wait(i):
            if i < count:
                self.capture_screenshot(save_path, region)
                QTimer.singleShot(interval * 1000, lambda: capture_and_wait(i + 1))

        capture_and_wait(0)

    def show_preview(self, image):
        if self.preview_window is None:
            self.preview_window = PreviewWindow()

        pixmap = self.pil2pixmap(image).scaled(150, 100, Qt.KeepAspectRatio)
        self.preview_window.update_image(pixmap)
        self.preview_window.show()
        QTimer.singleShot(3000, self.preview_window.hide)

    def pil2pixmap(self, image):
        image = image.convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        qim = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qim)
        return pixmap

class PreviewWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(QApplication.desktop().width() - 170, QApplication.desktop().height() - 120, 150, 100)
        self.image_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

    def update_image(self, pixmap):
        self.image_label.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ScreenshotApp()
    ex.show()
    sys.exit(app.exec_())

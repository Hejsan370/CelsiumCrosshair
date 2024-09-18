import sys
import ctypes
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QPushButton, QColorDialog, QFileDialog, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont, QPixmap

# Constants for making the window click-through
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
GWL_EXSTYLE = -20

def make_window_click_through(window_id):
    hwnd = int(window_id)
    extended_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, extended_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

class CrosshairOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setGeometry(0, 0, QApplication.desktop().width(), QApplication.desktop().height())

        self.crosshair_visible = False
        self.default_size = 15
        self.default_thickness = 2
        self.default_color = QColor(255, 0, 0, 255)
        self.reset_to_default()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_overlay)
        self.timer.start(16)  # 60 FPS

        self.show()
        make_window_click_through(self.winId())

    def reset_to_default(self):
        self.size = self.default_size
        self.thickness = self.default_thickness
        self.color = self.default_color
        self.crosshair_image = None
        self.update()

    def update_overlay(self):
        if self.crosshair_visible:
            self.show()
        else:
            self.hide()

    def toggle_crosshair(self, visible):
        self.crosshair_visible = visible

    def set_size(self, size):
        self.size = size
        self.update()

    def set_thickness(self, thickness):
        self.thickness = thickness
        self.update()

    def set_color(self, color):
        self.color = color
        self.update()

    def load_custom_crosshair(self, image_path):
        self.crosshair_image = QPixmap(image_path)
        self.update()

    def paintEvent(self, event):
        if not self.crosshair_visible:
            return

        painter = QPainter(self)

        if self.crosshair_image:
            # Draw custom crosshair image
            image_rect = self.crosshair_image.rect()
            image_rect.moveCenter(self.rect().center())
            painter.drawPixmap(image_rect, self.crosshair_image)
        else:
            # Draw default crosshair
            painter.setPen(self.color)
            mid_x = self.width() // 2
            mid_y = self.height() // 2

            pen = painter.pen()
            pen.setWidth(self.thickness)
            painter.setPen(pen)

            # Draw horizontal line
            painter.drawLine(mid_x - self.size, mid_y, mid_x + self.size, mid_y)

            # Draw vertical line
            painter.drawLine(mid_x, mid_y - self.size, mid_x, mid_y + self.size)

        painter.end()

class CrosshairSettingsUI(QWidget):
    def __init__(self, crosshair_overlay):
        super().__init__()
        self.crosshair_overlay = crosshair_overlay
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Crosshair Settings")
        self.setGeometry(100, 100, 400, 450)  # Increased height for additional slider

        # Glassmorphism effect with rounded corners
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 20px;
                backdrop-filter: blur(15px);
                padding: 15px;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 18px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                padding: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.2);
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 1px solid #ffffff;
                width: 15px;
                margin: -5px 0; /* half the handle size */
                border-radius: 7px;
            }
        """)

        # Custom fonts
        font = QFont("Arial", 14)

        # Layout setup
        layout = QVBoxLayout()

        # Crosshair size slider
        self.size_label = QLabel(f"Crosshair Size: {self.crosshair_overlay.size}")
        self.size_label.setFont(font)
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(5)
        self.size_slider.setMaximum(100)
        self.size_slider.setValue(self.crosshair_overlay.size)
        self.size_slider.valueChanged.connect(self.update_size)

        # Crosshair thickness slider
        self.thickness_label = QLabel(f"Crosshair Thickness: {self.crosshair_overlay.thickness}")
        self.thickness_label.setFont(font)
        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setMinimum(1)
        self.thickness_slider.setMaximum(10)
        self.thickness_slider.setValue(self.crosshair_overlay.thickness)
        self.thickness_slider.valueChanged.connect(self.update_thickness)

        # FOV slider
        self.fov_label = QLabel(f"Field of View (FOV): {90}")  # Default value
        self.fov_label.setFont(font)
        self.fov_slider = QSlider(Qt.Horizontal)
        self.fov_slider.setMinimum(60)
        self.fov_slider.setMaximum(120)
        self.fov_slider.setValue(90)  # Default value
        self.fov_slider.valueChanged.connect(self.update_fov)

        # Crosshair color picker button
        self.color_button = QPushButton("Choose Crosshair Color")
        self.color_button.setFont(font)
        self.color_button.clicked.connect(self.choose_color)

        # Upload custom crosshair button
        self.upload_button = QPushButton("Upload Custom Crosshair")
        self.upload_button.setFont(font)
        self.upload_button.clicked.connect(self.upload_custom_crosshair)

        # Remove custom crosshair button
        self.remove_custom_button = QPushButton("Remove Custom Crosshair")
        self.remove_custom_button.setFont(font)
        self.remove_custom_button.clicked.connect(self.remove_custom_crosshair)

        # Enable/disable crosshair button
        self.crosshair_button = QPushButton("Enable Crosshair")
        self.crosshair_button.setFont(font)
        self.crosshair_button.setCheckable(True)
        self.crosshair_button.clicked.connect(self.toggle_crosshair)

        # Layout organization
        layout.addWidget(self.size_label)
        layout.addWidget(self.size_slider)
        layout.addWidget(self.thickness_label)
        layout.addWidget(self.thickness_slider)
        layout.addWidget(self.fov_label)
        layout.addWidget(self.fov_slider)
        layout.addWidget(self.color_button)
        layout.addWidget(self.upload_button)

        # Create a horizontal layout for centering the remove button
        center_layout = QHBoxLayout()
        center_layout.addStretch()  # Add stretchable space before the button
        center_layout.addWidget(self.remove_custom_button)
        center_layout.addStretch()  # Add stretchable space after the button

        # Add the center_layout to the main layout
        layout.addLayout(center_layout)

        layout.addWidget(self.crosshair_button)

        self.setLayout(layout)

    def update_size(self, value):
        self.size_label.setText(f"Crosshair Size: {value}")
        self.crosshair_overlay.set_size(value)

    def update_thickness(self, value):
        self.thickness_label.setText(f"Crosshair Thickness: {value}")
        self.crosshair_overlay.set_thickness(value)

    def update_fov(self, value):
        self.fov_label.setText(f"Field of View (FOV): {value}")
        # Implement logic to handle FOV adjustment for the game here

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.crosshair_overlay.set_color(color)

    def upload_custom_crosshair(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Crosshair Image", "", "Images (*.png *.xpm *.jpg);;All Files (*)", options=options)
        if file_path:
            self.crosshair_overlay.load_custom_crosshair(file_path)

    def remove_custom_crosshair(self):
        self.crosshair_overlay.reset_to_default()

    def toggle_crosshair(self):
        if self.crosshair_button.isChecked():
            self.crosshair_button.setText("Disable Crosshair")
            self.crosshair_overlay.toggle_crosshair(True)
        else:
            self.crosshair_button.setText("Enable Crosshair")
            self.crosshair_overlay.toggle_crosshair(False)

def main():
    app = QApplication(sys.argv)

    # Create the crosshair overlay (invisible initially)
    overlay = CrosshairOverlay()

    # Create the settings window (always visible for interaction)
    settings_window = CrosshairSettingsUI(overlay)
    settings_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

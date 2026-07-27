import sys
import json
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QPushButton
)
from PyQt6.QtCore import Qt


class SmartCtlMon:
    @staticmethod
    def get_disk_info(device_path="/dev/nvme0n1"):
        try:
            cmd = ["pkexec", "smartctl", "-a", "-j", device_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception as e:
            print(f"Error reading disk info: {e}")
            return None


class PyDiskInfo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_device = "/dev/nvme0n1"
        self.init_ui()
        self.update_data()

    def init_ui(self):
        self.setWindowTitle("PyDiskInfo")
        self.resize(650, 480)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Device:"))
        self.dev_combo = QComboBox()
        self.dev_combo.addItems(["/dev/nvme0n1", "/dev/sda", "/dev/sdb"])
        self.dev_combo.currentTextChanged.connect(self.on_device_changed)
        top_bar.addWidget(self.dev_combo)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.update_data)
        top_bar.addWidget(refresh_btn)        
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        status_layout = QHBoxLayout()
        self.health_label = QLabel("HEALTH: UNKNOWN")
        self.health_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.health_label.setStyleSheet(
            "background-color: #6c757d; color: white; font-weight: bold; font-size: 16px; padding: 12px; border-radius: 0px;"
        )
        self.temp_label = QLabel("TEMP: -- °C")
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp_label.setStyleSheet(
            "background-color: #17a2b8; color: white; font-weight: bold; font-size: 16px; padding: 12px; border-radius: 0px;"
        )
        status_layout.addWidget(self.health_label, 2)
        status_layout.addWidget(self.temp_label, 1)
        main_layout.addLayout(status_layout)

        self.info_label = QLabel("Model: -\nSerial: -")
        main_layout.addWidget(self.info_label)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID / Attribute Name", "Current", "Worst", "Raw Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)

    def on_device_changed(self, device):
        self.current_device = device
        self.update_data()

    def update_data(self):
        data = SmartCtlMon.get_disk_info(self.current_device)
        if not data:
            self.health_label.setText("ERROR")
            self.health_label.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; font-size: 16px;")
            return
        model = data.get("model_name", data.get("device", {}).get("name", "Unknown"))
        serial = data.get("serial_number", "N/A")
        
        self.info_label.setText(f"Model: {model}  |  Serial: {serial}")
        temp = data.get("temperature", {}).get("current", 0)
        
        self.temp_label.setText(f"TEMP: {temp} °C")
        passed = data.get("smart_status", {}).get("passed", True)
        
        if passed:
            status_str = "GOOD"
            color_code = "#007bff"
        else:
            status_str = "BAD"
            color_code = "#dc3545"

        if "nvme_smart_health_information_log" in data:
            used = data["nvme_smart_health_information_log"].get("percentage_used", 0)
            if used > 90 and passed:
                status_str = "CAUTION"
                color_code = "#ffc107"

        self.health_label.setText(f"HEALTH: {status_str}")
        self.health_label.setStyleSheet(
            f"background-color: {color_code}; color: white; font-weight: bold; font-size: 16px; padding: 12px; border-radius: 0px;"
        )

        self.table.setRowCount(0)
        if "ata_smart_attributes" in data:
            attrs = data["ata_smart_attributes"].get("table", [])
            for attr in attrs:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(attr.get("name"))))
                self.table.setItem(row, 1, QTableWidgetItem(str(attr.get("value"))))
                self.table.setItem(row, 2, QTableWidgetItem(str(attr.get("worst"))))
                self.table.setItem(row, 3, QTableWidgetItem(str(attr.get("raw", {}).get("string"))))
        elif "nvme_smart_health_information_log" in data:
            nvme_log = data["nvme_smart_health_information_log"]
            for key, val in nvme_log.items():
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(key))
                self.table.setItem(row, 1, QTableWidgetItem("-"))
                self.table.setItem(row, 2, QTableWidgetItem("-"))
                self.table.setItem(row, 3, QTableWidgetItem(str(val)))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = PyDiskInfo()
    window.show()
    
    sys.exit(app.exec())

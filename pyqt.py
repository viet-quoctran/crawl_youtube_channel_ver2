import sys
import io
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLineEdit, QTextEdit, QLabel, QListWidget, QListWidgetItem, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer
from settings import Settings  # Import từ file settings.py

# Đặt mã hóa đầu ra thành UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='ignore')

class CheckableListWidgetItem(QListWidgetItem):
    def __init__(self, text):
        super().__init__()
        self.setText(text)
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setCheckState(Qt.Unchecked)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Crawler")
        self.setGeometry(100, 100, 600, 400)  # Chỉnh sửa kích thước cửa sổ khởi tạo
        self.settings = Settings()
        self.initUI()
        self.load_settings()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Tạo group box cho từ khóa, API keys và profile ID
        input_group_box = QGroupBox("Inputs")
        input_layout = QVBoxLayout()

        # Nhập từ khóa và profile ID
        input_hbox = QHBoxLayout()
        self.keyword_input = QLineEdit(self)
        self.keyword_input.setPlaceholderText("Enter keyword and press Enter")
        self.keyword_input.setFixedHeight(30)  # Chỉnh chiều cao
        self.keyword_input.setStyleSheet("font-size: 12px; padding: 5px;")  # Chỉnh kích thước font và padding
        self.keyword_input.returnPressed.connect(self.process_input)
        input_hbox.addWidget(QLabel("Keyword:"))
        input_hbox.addWidget(self.keyword_input)

        self.add_button = QPushButton("Add Keyword", self)
        self.add_button.clicked.connect(self.process_input)
        self.add_button.setFixedHeight(30)  # Chỉnh chiều cao
        self.add_button.setStyleSheet("background-color: #007BFF; color: white; font-size: 12px; padding: 5px;")  # Chỉnh màu và kích thước font
        input_hbox.addWidget(self.add_button)

        input_hbox.addWidget(QLabel("Profile ID:"))
        self.profile_id_input = QLineEdit(self)
        self.profile_id_input.setPlaceholderText("Enter Profile ID")
        self.profile_id_input.setFixedHeight(30)  # Chỉnh chiều cao
        self.profile_id_input.setStyleSheet("font-size: 12px; padding: 5px;")  # Chỉnh kích thước font và padding
        input_hbox.addWidget(self.profile_id_input)

        input_layout.addLayout(input_hbox)

        # Nhập API key
        api_hbox = QHBoxLayout()
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setPlaceholderText("Enter API key")
        self.api_key_input.setFixedHeight(30)  # Chỉnh chiều cao
        self.api_key_input.setStyleSheet("font-size: 12px; padding: 5px;")  # Chỉnh kích thước font và padding
        api_hbox.addWidget(QLabel("API Key:"))
        api_hbox.addWidget(self.api_key_input)

        self.add_api_key_button = QPushButton("Add API Key", self)
        self.add_api_key_button.clicked.connect(self.add_api_key)
        self.add_api_key_button.setFixedHeight(30)  # Chỉnh chiều cao
        self.add_api_key_button.setStyleSheet("background-color: #007BFF; color: white; font-size: 12px; padding: 5px;")  # Chỉnh màu và kích thước font
        api_hbox.addWidget(self.add_api_key_button)

        input_layout.addLayout(api_hbox)

        # Nhập tên file Excel
        excel_hbox = QHBoxLayout()
        self.excel_input = QLineEdit(self)
        self.excel_input.setPlaceholderText("Enter Excel file name (e.g., channel_info)")
        self.excel_input.setFixedHeight(30)  # Chỉnh chiều cao
        self.excel_input.setStyleSheet("font-size: 12px; padding: 5px;")  # Chỉnh kích thước font và padding
        excel_hbox.addWidget(QLabel("Excel File:"))
        excel_hbox.addWidget(self.excel_input)

        input_layout.addLayout(excel_hbox)
        input_group_box.setLayout(input_layout)

        # Danh sách từ khóa và API keys nằm ngang nhau
        lists_hbox = QHBoxLayout()

        # Danh sách từ khóa
        keyword_list_layout = QVBoxLayout()
        keyword_list_layout.addWidget(QLabel("Keywords:"))
        self.keyword_list = QListWidget(self)
        keyword_list_layout.addWidget(self.keyword_list)

        self.delete_button = QPushButton("Delete Selected Keywords", self)
        self.delete_button.clicked.connect(self.delete_selected_keywords)
        self.delete_button.setFixedHeight(30)  # Chỉnh chiều cao
        self.delete_button.setStyleSheet("background-color: #FF0000; color: white; font-size: 12px; padding: 5px;")  # Chỉnh màu và kích thước font
        keyword_list_layout.addWidget(self.delete_button)

        lists_hbox.addLayout(keyword_list_layout)

        # Danh sách API keys
        api_key_list_layout = QVBoxLayout()
        api_key_list_layout.addWidget(QLabel("API Keys:"))
        self.api_key_list = QListWidget(self)
        api_key_list_layout.addWidget(self.api_key_list)

        self.delete_api_key_button = QPushButton("Delete Selected API Keys", self)
        self.delete_api_key_button.clicked.connect(self.delete_selected_api_keys)
        self.delete_api_key_button.setFixedHeight(30)  # Chỉnh chiều cao
        self.delete_api_key_button.setStyleSheet("background-color: #FF0000; color: white; font-size: 12px; padding: 5px;")  # Chỉnh màu và kích thước font
        api_key_list_layout.addWidget(self.delete_api_key_button)

        lists_hbox.addLayout(api_key_list_layout)

        # Phần mô tả trạng thái tiến trình ở cuối cùng
        status_layout = QVBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_text = QTextEdit(self)
        self.status_text.setReadOnly(True)
        self.status_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        status_layout.addWidget(self.status_text)

        # Nút bắt đầu
        start_layout = QHBoxLayout()
        self.start_button = QPushButton("Start", self)
        self.start_button.setFixedHeight(30)  # Chỉnh chiều cao
        self.start_button.setStyleSheet("background-color: #28A745; color: white; font-size: 12px; padding: 5px;")  # Chỉnh màu và kích thước font
        self.start_button.setFixedSize(80, 30)
        self.start_button.clicked.connect(self.start_crawler)  # Kết nối với hàm start_crawler
        start_layout.addWidget(self.start_button)

        main_layout.addWidget(input_group_box)
        main_layout.addLayout(lists_hbox)
        main_layout.addLayout(status_layout)
        main_layout.addLayout(start_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Thiết lập Timer để cập nhật trạng thái từ file
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # Cập nhật trạng thái mỗi giây

    def load_settings(self):
        # Load thông tin từ settings.json
        self.profile_id_input.setText(self.settings.profile_id)
        self.excel_input.setText(self.settings.excel_file_path.rsplit('.', 1)[0])  # Load tên file Excel mà không có đuôi

        for api_key in self.settings.api_keys:
            item = CheckableListWidgetItem(api_key)
            self.api_key_list.addItem(item)

        for url in self.settings.search_urls:
            keyword = url.split('=')[-1].replace('+', ' ')
            item = CheckableListWidgetItem(keyword)
            self.keyword_list.addItem(item)

    def process_input(self):
        keyword = self.keyword_input.text()

        if not keyword:
            self.append_status("Please enter a keyword", error=True)
            return

        item = CheckableListWidgetItem(keyword)
        self.keyword_list.addItem(item)
        self.keyword_input.clear()

    def add_api_key(self):
        api_key = self.api_key_input.text()

        if not api_key:
            self.append_status("Please enter an API key", error=True)
            return

        item = CheckableListWidgetItem(api_key)
        self.api_key_list.addItem(item)
        self.api_key_input.clear()

    def delete_selected_api_keys(self):
        for index in reversed(range(self.api_key_list.count())):
            item = self.api_key_list.item(index)
            if item.checkState() == Qt.Checked:
                self.api_key_list.takeItem(index)

    def delete_selected_keywords(self):
        for index in reversed(range(self.keyword_list.count())):
            item = self.keyword_list.item(index)
            if item.checkState() == Qt.Checked:
                self.keyword_list.takeItem(index)

    def save_settings(self):
        # Lưu thông tin profile ID
        self.settings.profile_id = self.profile_id_input.text()

        # Lưu tên file Excel
        excel_file_name = self.excel_input.text().strip()
        if not excel_file_name.endswith(".xlsx"):
            excel_file_name += ".xlsx"
        self.settings.excel_file_path = excel_file_name

        # Lưu thông tin từ khóa
        keywords = []
        for index in range(self.keyword_list.count()):
            item = self.keyword_list.item(index).text().replace(' ', '+')
            keywords.append(f"https://www.youtube.com/results?search_query={item}")

        self.settings.search_urls = keywords

        # Lưu API keys
        self.settings.api_keys = [self.api_key_list.item(index).text() for index in range(self.api_key_list.count())]

        # Gọi hàm save_settings của lớp Settings để lưu vào file settings.json
        self.settings.save_settings()

        self.append_status("Settings saved successfully!")

    def start_crawler(self):
        if not self.profile_id_input.text():
            self.append_status("Please enter a Profile ID", error=True)
            return

        self.save_settings()
        # Xóa file status.log trước khi bắt đầu
        open("status.log", "w").close()
        # Chạy main.py
        subprocess.Popen(["python", "main.py"])

    def append_status(self, message, error=False):
        if error:
            self.status_text.setTextColor(Qt.red)
        else:
            self.status_text.setTextColor(Qt.black)
        self.status_text.append(message)

    def update_status(self):
        try:
            with open("status.log", "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    self.status_text.setPlainText("".join(lines))
        except FileNotFoundError:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

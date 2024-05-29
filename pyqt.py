import sys
import io
import requests
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLineEdit, QTextEdit, QLabel, QListWidget, QListWidgetItem, QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt
from googletrans import Translator, LANGUAGES
from icecream import ic
from country_to_language import country_to_language  # Import từ file country_to_language.py
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
        self.setGeometry(100, 100, 800, 400)
        self.settings = Settings()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Tạo group box cho từ khóa, proxy và profile ID
        input_group_box = QGroupBox("Inputs")
        input_layout = QVBoxLayout()

        # Nhập từ khóa, proxy và profile ID
        input_hbox = QHBoxLayout()
        self.keyword_input = QLineEdit(self)
        self.keyword_input.setPlaceholderText("Enter keyword and press Enter")
        self.keyword_input.returnPressed.connect(self.process_input)
        input_hbox.addWidget(QLabel("Keyword:"))
        input_hbox.addWidget(self.keyword_input)

        self.add_button = QPushButton("Add", self)
        self.add_button.clicked.connect(self.process_input)
        self.add_button.setStyleSheet("background-color: blue; color: white; font-size: 14px; padding: 5px;")
        input_hbox.addWidget(self.add_button)

        self.proxy_input = QLineEdit(self)
        self.proxy_input.setPlaceholderText("IP:port:username:password")
        input_hbox.addWidget(QLabel("Proxy:"))
        input_hbox.addWidget(self.proxy_input)

        self.profile_id_input = QLineEdit(self)
        self.profile_id_input.setPlaceholderText("Enter Profile ID")
        input_hbox.addWidget(QLabel("Profile ID:"))
        input_hbox.addWidget(self.profile_id_input)

        input_layout.addLayout(input_hbox)
        input_group_box.setLayout(input_layout)

        # Danh sách từ khóa và phần mô tả trạng thái tiến trình
        horizontal_layout = QHBoxLayout()

        # Danh sách từ khóa
        keyword_list_layout = QVBoxLayout()
        keyword_list_layout.addWidget(QLabel("Keywords:"))
        self.keyword_list = QListWidget(self)
        keyword_list_layout.addWidget(self.keyword_list)
        
        # Nút xóa
        self.delete_button = QPushButton("Delete Selected", self)
        self.delete_button.clicked.connect(self.delete_selected_keywords)
        self.delete_button.setStyleSheet("background-color: red; color: white; font-size: 14px; padding: 5px;")
        keyword_list_layout.addWidget(self.delete_button)

        horizontal_layout.addLayout(keyword_list_layout)

        # Phần mô tả trạng thái tiến trình
        status_layout = QVBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_text = QTextEdit(self)
        self.status_text.setReadOnly(True)
        self.status_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        status_layout.addWidget(self.status_text)
        horizontal_layout.addLayout(status_layout)

        # Nút bắt đầu
        start_layout = QHBoxLayout()
        self.start_button = QPushButton("Start", self)
        self.start_button.setStyleSheet("background-color: green; color: white; font-size: 14px; padding: 5px;")
        self.start_button.setFixedSize(80, 30)
        self.start_button.clicked.connect(self.start_crawler)  # Kết nối với hàm start_crawler
        start_layout.addWidget(self.start_button)

        main_layout.addWidget(input_group_box)
        main_layout.addLayout(start_layout)
        main_layout.addLayout(horizontal_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def process_input(self):
        keyword = self.keyword_input.text()
        proxy = self.proxy_input.text()

        if not keyword or not proxy:
            self.status_text.append("Please enter both keyword and proxy")
            return

        country_code = self.lookup_proxy_country(proxy)
        if country_code:
            language_code = country_to_language.get(country_code, "en")
            translated_keyword = self.translate_keyword(keyword, language_code)
            item = CheckableListWidgetItem(translated_keyword)
            self.keyword_list.addItem(item)
            self.keyword_input.clear()

    def lookup_proxy_country(self, proxy):
        ip = proxy.split(':')[0]
        try:
            response = requests.get(f"https://ipinfo.io/{ip}/json")
            if response.status_code == 200:
                data = response.json()
                country = data.get("country", "Unknown")
                self.status_text.append(f"Proxy country: {country}")
                return country
            else:
                self.status_text.append("Failed to lookup proxy country")
        except requests.RequestException as e:
            self.status_text.append(f"Error looking up proxy: {e}")
        return None

    def translate_keyword(self, keyword, language_code):
        translator = Translator()
        translation = translator.translate(keyword, dest=language_code)
        return translation.text

    def delete_selected_keywords(self):
        for index in reversed(range(self.keyword_list.count())):
            item = self.keyword_list.item(index)
            if item.checkState() == Qt.Checked:
                self.keyword_list.takeItem(index)

    def save_settings(self):
        # Lưu thông tin proxy
        self.settings.proxies = [self.proxy_input.text()]

        # Lưu thông tin profile ID
        self.settings.profile_id = self.profile_id_input.text()

        # Lưu thông tin từ khóa
        keywords = []
        for index in range(self.keyword_list.count()):
            item = self.keyword_list.item(index).text().replace(' ', '+')
            keywords.append(f"https://www.youtube.com/results?search_query={item}")

        self.settings.search_urls = keywords

        # Gọi hàm save_settings của lớp Settings để lưu vào file settings.json
        self.settings.save_settings()

        self.status_text.append("Settings saved successfully!")

    def start_crawler(self):
        self.save_settings()
        # Chạy main.py
        subprocess.Popen(["python", "main.py"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

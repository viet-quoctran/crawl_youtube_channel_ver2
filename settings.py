import json

class Settings:
    def __init__(self):
        self.api_url = 'http://127.0.0.1:19995/api/v3/'
        self.start_endpoint = 'profiles/start/{id}'
        self.close_endpoint = 'profiles/close/{id}'
        self.update_endpoint = 'profiles/update/{id}'
        self.profile_id = ''
        self.search_urls = []
        self.excel_file_path = 'channel_info.xlsx'  # Mặc định tên file Excel
        self.api_keys = []  # Danh sách API keys
        self.load_settings()

    def load_settings(self):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.profile_id = data.get("profile_id", "")
                self.search_urls = data.get("search_urls", [])
                self.excel_file_path = data.get("excel_file_path", "channel_info.xlsx")  # Load tên file Excel từ settings.json
                self.api_keys = data.get("api_keys", [])  # Load API keys từ settings.json
        except FileNotFoundError:
            pass

    def save_settings(self):
        data = {
            "profile_id": self.profile_id,
            "search_urls": self.search_urls,
            "excel_file_path": self.excel_file_path,  # Lưu tên file Excel vào settings.json
            "api_keys": self.api_keys  # Lưu API keys vào settings.json
        }
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

settings = Settings()

import sys
import io
import os
import pandas as pd
import time
from icecream import ic
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from settings import Settings
from api import GPMLoginApiV3
from utils import setup_driver, crawl_channel_info, crawl_data

# Đặt mã hóa đầu ra thành UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='ignore')

# Cấu hình từ settings
settings = Settings()

# Khởi tạo API
api = GPMLoginApiV3(settings.api_url, settings.start_endpoint, settings.close_endpoint, settings.update_endpoint)

def write_status(message):
    with open("status.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

def main():
    search_urls = settings.search_urls
    proxies = settings.proxies
    proxy_index = 0
    current_proxy = proxies[proxy_index]
    driver = setup_driver(api, settings.profile_id, current_proxy, update_proxy=False)
    if not driver:
        return

    collected_urls = set()  # Sử dụng set để kiểm tra trùng lặp URL
    duplicate_count = 0  # Biến đếm số lượng URL bị trùng
    while True:
        try:
            channel_urls = crawl_data(driver, search_urls)
            if channel_urls:
                for channel_url in channel_urls:
                    if channel_url not in collected_urls:  # Kiểm tra trùng lặp URL
                        collected_urls.add(channel_url)
                    else:
                        duplicate_count += 1  # Tăng biến đếm nếu URL bị trùng

                status_message = f"Total channel URLs collected: {len(collected_urls)}"
                write_status(status_message)
                break
        except (NoSuchElementException, TimeoutException):
            status_message = "Error encountered, switching proxy..."
            write_status(status_message)
            proxy_index = (proxy_index + 1) % len(proxies)
            api.close_profile(settings.profile_id)
            current_proxy = proxies[proxy_index]
            driver = setup_driver(api, settings.profile_id, current_proxy, update_proxy=True)
            if not driver:
                return

    # Đọc DataFrame hiện có từ file nếu tồn tại
    if os.path.exists(settings.excel_file_path):
        channel_infos_df = pd.read_excel(settings.excel_file_path)
    else:
        channel_infos_df = pd.DataFrame()

    for i, channel_url in enumerate(collected_urls):
        channel_info = crawl_channel_info(driver, channel_url, api, settings.profile_id, current_proxy, channel_infos_df, settings.excel_file_path)
        if channel_info is None:
            continue

        print(f'Channel {i+1}:')
        print(f'Channel Name: {channel_info["channel_name"]}')
        print(f'Channel ID: {channel_info["id"]}')
        print(f'Channel URL: {channel_url}')
        print(f'Sub Count: {channel_info["sub_count"]}')
        print(f'Video Count: {channel_info["video_count"]}')
        print('-----------------------------')
        
    api.close_profile(settings.profile_id)
    

if __name__ == "__main__":
    main()

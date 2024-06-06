import sys
import io
import os
import pandas as pd
from settings import Settings
from api import GPMLoginApiV3, get_proxy_country
from utils import setup_driver, crawl_channel_info, crawl_data, write_status

# Đặt mã hóa đầu ra thành UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='ignore')

# Cấu hình từ settings
settings = Settings()

# Khởi tạo API
api = GPMLoginApiV3(settings.api_url, settings.start_endpoint, settings.close_endpoint, settings.update_endpoint, settings.profile_info_endpoint)

def main():
    search_urls = settings.search_urls

    collected_urls = set()  # Sử dụng set để kiểm tra trùng lặp URL

    driver = setup_driver(api, settings.profile_id)
    if not driver:
        return
    
    try:
        for search_url in search_urls:
            channel_urls = crawl_data(driver, [search_url])
            if channel_urls:
                for channel_url in channel_urls:
                    if channel_url not in collected_urls:  # Kiểm tra trùng lặp URL
                        collected_urls.add(channel_url)

                status_message = f"Total channel URLs collected: {len(collected_urls)}"
                write_status(status_message)
    finally:
        driver.quit()

    # Lấy quốc gia của proxy từ profile
    proxy_country = get_proxy_country(api, settings.profile_id)
    write_status(f"Proxy country: {proxy_country}")

    # Đọc DataFrame hiện có từ file nếu tồn tại
    if os.path.exists(settings.excel_file_path):
        channel_infos_df = pd.read_excel(settings.excel_file_path)
    else:
        channel_infos_df = pd.DataFrame()

    for i, channel_url in enumerate(collected_urls):
        channel_info = crawl_channel_info(channel_url, channel_infos_df, settings.excel_file_path, proxy_country)
        if channel_info is None:
            continue

        print(f'Channel {i+1}:')
        print(f'Channel Name: {channel_info["channel_name"]}')
        print(f'Channel ID: {channel_info["id"]}')
        print(f'Channel URL: {channel_url}')
        print(f'Sub Count: {channel_info["sub_count"]}')
        print(f'Video Count: {channel_info["video_count"]}')
        print(f'Country: {channel_info["country"]}')
        print('-----------------------------')

if __name__ == "__main__":
    main()

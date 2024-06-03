import time
import pandas as pd
import requests
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from api import GPMLoginApiV3
from settings import Settings  # Import Settings để lấy API_KEYS
import sys  # Thêm sys để dùng sys.exit

settings = Settings()
current_key_index = 0

def get_current_api_key():
    global current_key_index
    return settings.api_keys[current_key_index]

def switch_api_key():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(settings.api_keys)
    if current_key_index == 0:  # Nếu quay lại key đầu tiên, tức là đã hết tất cả các keys
        return False
    return True

def setup_driver(api, profile_id, update_proxy=False):
    # Khởi động profile
    start_result = api.start_profile(profile_id)
    if not start_result or "data" not in start_result:
        write_status("Failed to start profile")
        return None

    options = Options()
    options.binary_location = start_result["data"]["browser_location"]
    options.add_experimental_option("debuggerAddress", f"localhost:{start_result['data']['remote_debugging_address'].split(':')[1]}")
    service = Service(executable_path=start_result["data"]["driver_path"])
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def write_status(message):
    with open("status.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

def crawl_data(driver, search_urls):
    all_channel_urls = []
    for search_url in search_urls:
        driver.get(search_url)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ytd-video-renderer"))
            )

            last_height = driver.execute_script("return document.documentElement.scrollHeight")
            
            while True:
                video_elements = driver.find_elements(By.CSS_SELECTOR, "ytd-video-renderer")
                
                for video in video_elements:
                    try:
                        channel_element = video.find_element(By.CSS_SELECTOR, 'a.yt-simple-endpoint.style-scope.yt-formatted-string')
                        channel_url_path = channel_element.get_attribute('href')
                        
                        if channel_url_path and channel_url_path.startswith("http"):
                            channel_url = channel_url_path
                        elif channel_url_path:
                            channel_url = f"https://www.youtube.com{channel_url_path}"
                        else:
                            message = f"Invalid channel_url_path: {channel_url_path}"
                            write_status(message)
                            continue

                        all_channel_urls.append(channel_url)
                    except StaleElementReferenceException:
                        message = "StaleElementReferenceException encountered for video."
                        write_status(message)
                        continue
                    except NoSuchElementException:
                        message = f"NoSuchElementException encountered for video: {video}"
                        write_status(message)
                        continue

                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.documentElement.scrollHeight")

                if new_height == last_height:
                    break
                last_height = new_height

            message = f"Total channel URLs collected: {len(all_channel_urls)}"
            write_status(message)
        except NoSuchElementException as e:
            if "404" in driver.page_source:
                raise e
            else:
                continue
        except TimeoutException:
            message = f"Loading search URL {search_url} took too long, skipping..."
            write_status(message)
            continue

    return all_channel_urls

def get_channel_info_from_api(channel_url):
    global current_key_index

    channel_id = None
    handle = None

    # Kiểm tra loại URL
    if "/channel/" in channel_url:
        match = re.search(r"youtube\.com\/channel\/([a-zA-Z0-9_-]+)", channel_url)
        if match:
            channel_id = match.group(1)
    elif "/user/" in channel_url:
        match = re.search(r"youtube\.com\/user\/([a-zA-Z0-9_-]+)", channel_url)
        if match:
            handle = match.group(1)
    elif "/@" in channel_url:
        match = re.search(r"youtube\.com\/@([a-zA-Z0-9_-]+)", channel_url)
        if match:
            handle = match.group(1)

    if not channel_id and not handle:
        write_status(f"Invalid channel URL: {channel_url}")
        return None

    if handle:
        while True:
            api_key = get_current_api_key()
            search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={handle}&key={api_key}"
            response = requests.get(search_url)
            if response.status_code == 200:
                data = response.json()
                if "items" in data and len(data["items"]) > 0:
                    channel_id = data["items"][0]["snippet"]["channelId"]
                    break
                else:
                    write_status(f"No data found for handle: {handle}")
                    return None
            elif response.status_code == 403:  # Quota exceeded
                write_status(f"Quota exceeded for API key: {api_key}, switching key...")
                if not switch_api_key():
                    write_status("All API keys have exceeded their quota.")
                    sys.exit("All API keys have exceeded their quota. Exiting program.")
            else:
                write_status(f"Failed to fetch channel info for handle: {handle}, status code: {response.status_code}")
                return None

    while True:
        api_key = get_current_api_key()
        api_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={api_key}"

        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                item = data["items"][0]
                channel_info = {
                    'channel_name': item['snippet']['title'],
                    'id': channel_id,
                    'sub_count': item['statistics'].get('subscriberCount', 'N/A'),
                    'video_count': item['statistics'].get('videoCount', 'N/A'),
                    'channel_url': channel_url
                }
                return channel_info
            else:
                write_status(f"No data found for channel URL: {channel_url}")
                return None
        elif response.status_code == 403:  # Quota exceeded
            write_status(f"Quota exceeded for API key: {api_key}, switching key...")
            if not switch_api_key():
                write_status("All API keys have exceeded their quota.")
                sys.exit("All API keys have exceeded their quota. Exiting program.")
        else:
            write_status(f"Failed to fetch channel info for URL: {channel_url}, status code: {response.status_code}")
            return None

def crawl_channel_info(channel_url, channel_infos_df, excel_file_path):
    channel_info = get_channel_info_from_api(channel_url)
    if channel_info is None:
        return None

    # Đọc DataFrame hiện có từ file nếu tồn tại
    if os.path.exists(excel_file_path):
        existing_df = pd.read_excel(excel_file_path)
        channel_infos_df = pd.concat([existing_df, pd.DataFrame([channel_info])], ignore_index=True)
    else:
        channel_infos_df = pd.DataFrame([channel_info])

    # Lưu DataFrame vào file Excel
    channel_infos_df.to_excel(excel_file_path, index=False)

    return channel_info

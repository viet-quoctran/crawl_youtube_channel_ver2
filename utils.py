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
from icecream import ic
from api import GPMLoginApiV3

def setup_driver(api, profile_id, proxy):
    # Cập nhật proxy cho profile
    api.update_proxy(profile_id, proxy)

    # Khởi động profile
    start_result = api.start_profile(profile_id)
    if not start_result or "data" not in start_result:
        print("Failed to start profile")
        return None

    options = Options()
    options.binary_location = start_result["data"]["browser_location"]
    options.add_experimental_option("debuggerAddress", f"localhost:{start_result['data']['remote_debugging_address'].split(':')[1]}")
    service = Service(executable_path=start_result["data"]["driver_path"])
    driver = webdriver.Chrome(service=service, options=options)
    return driver

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
                            ic(f"Invalid channel_url_path: {channel_url_path}")
                            continue

                        all_channel_urls.append(channel_url)
                    except StaleElementReferenceException:
                        ic(f"StaleElementReferenceException encountered for video.")
                        continue
                    except NoSuchElementException:
                        ic(f"NoSuchElementException encountered for video: {video}")
                        continue

                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.documentElement.scrollHeight")

                if new_height == last_height:
                    break
                last_height = new_height

            ic(f"Total channel URLs collected: {len(all_channel_urls)}")
        except NoSuchElementException as e:
            if "404" in driver.page_source:
                raise e
            else:
                continue
        except TimeoutException:
            print(f"Loading search URL {search_url} took too long, skipping...")
            continue

    return all_channel_urls

def crawl_channel_info(driver, channel_url, api, profile_id, proxy, channel_infos_df, excel_file_path):
    while True:
        # Kiểm tra trạng thái HTTP của URL kênh trước khi truy cập bằng Selenium
        response = requests.head(channel_url)
        ic(response.status_code)
        if response.status_code != 200:
            ic(channel_url)
            print(f"URL {channel_url} is not reachable, skipping to next channel...")
            return None
        
        try:
            driver.get(channel_url)
            container_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#page-header.style-scope.ytd-tabbed-page-header'))
            )

            # Lấy tên kênh từ thẻ h1
            channel_name_element = container_element.find_element(By.CSS_SELECTOR, 'h1.dynamic-text-view-model-wiz__h1')
            channel_name = channel_name_element.text

            # Lấy metadata và phân tích cú pháp
            metadata_element = container_element.find_element(By.CSS_SELECTOR, 'yt-content-metadata-view-model')
            metadata_text = metadata_element.text

            # Sử dụng regex để phân tích metadata
            metadata_parts = re.split(r'•', metadata_text)
            id_part = metadata_parts[0].strip()
            sub_count_part = metadata_parts[1].strip()
            video_count_part = metadata_parts[2].strip() if len(metadata_parts) > 2 else ""

            channel_info = {
                'channel_name': channel_name,
                'id': id_part,
                'sub_count': sub_count_part,
                'video_count': video_count_part,
                'channel_url': channel_url
            }

            # Đọc DataFrame hiện có từ file nếu tồn tại
            if os.path.exists(excel_file_path):
                existing_df = pd.read_excel(excel_file_path)
                channel_infos_df = pd.concat([existing_df, pd.DataFrame([channel_info])], ignore_index=True)
            else:
                channel_infos_df = pd.DataFrame([channel_info])

            # Lưu DataFrame vào file Excel
            channel_infos_df.to_excel(excel_file_path, index=False)

            return channel_info
        except (NoSuchElementException, TimeoutException):
            ic("Loading channel URL took too long, restarting profile...")
            api.close_profile(profile_id)
            time.sleep(5)  # Thời gian chờ để đảm bảo profile đã đóng hoàn toàn
            driver = setup_driver(api, profile_id, proxy)  # Khởi động lại profile với proxy
            if not driver:
                return None
            continue
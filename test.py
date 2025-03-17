import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
from time import sleep
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_images_from_page(url, headers=None, use_selenium=False):
    """ 爬取單頁面所有圖片並回傳列表，包含在特定div內的圖片 """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    if use_selenium:
        return get_images_with_selenium(url, headers)

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 檢查是否成功（非 200）

        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            print(f"Warning: {url} 不是 HTML 內容 ({content_type})")

        soup = BeautifulSoup(response.text, 'html.parser')
        images = []

        # 方法1: 直接尋找所有 img 標籤
        for img in soup.find_all("img"):
            process_image(img, url, images)

        # 方法2: 尋找 div 元素中的 background-image
        for div in soup.find_all(["div", "section", "header", "footer", "a"]):
            # 檢查 style 屬性中的背景圖片
            style = div.get("style", "")
            if "background-image" in style:
                try:
                    # 嘗試從 style 中提取 URL
                    bg_url = style.split("background-image:")[1].split(";")[0]
                    bg_url = bg_url.strip().replace("url(", "").replace(")", "").strip("'\"")
                    full_bg_url = urljoin(url, bg_url)
                    div_id = div.get("id", "")
                    div_class = div.get("class", [])
                    div_class_str = " ".join(div_class) if isinstance(div_class, list) else div_class

                    images.append({
                        "src": full_bg_url,
                        "alt": f"背景圖片 {div_id} {div_class_str}".strip(),
                        "type": "background-image"
                    })
                except Exception as e:
                    print(f"處理背景圖片錯誤: {e}")

            # 在 div 內部尋找 img 標籤
            for img in div.find_all("img"):
                process_image(img, url, images, f"in-div-{div.name}")

        print(f"找到 {len(images)} 張圖片")
        return images

    except requests.exceptions.RequestException as e:
        print(f"請求錯誤: {url} - {e}")
        return []
    except Exception as e:
        print(f"處理錯誤: {url} - {e}")
        return []

def get_images_with_selenium(url, headers):
    """ 使用 Selenium 渲染頁面並爬取圖片 """
    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={headers['User-Agent']}")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "img"))
        )

        images = []
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        for img in soup.find_all("img"):
            process_image(img, url, images)

        for div in soup.find_all(["div", "section", "header", "footer", "a"]):
            style = div.get("style", "")
            if "background-image" in style:
                try:
                    bg_url = style.split("background-image:")[1].split(";")[0]
                    bg_url = bg_url.strip().replace("url(", "").replace(")", "").strip("'\"")
                    full_bg_url = urljoin(url, bg_url)
                    div_id = div.get("id", "")
                    div_class = div.get("class", [])
                    div_class_str = " ".join(div_class) if isinstance(div_class, list) else div_class

                    images.append({
                        "src": full_bg_url,
                        "alt": f"背景圖片 {div_id} {div_class_str}".strip(),
                        "type": "background-image"
                    })
                except Exception as e:
                    print(f"處理背景圖片錯誤: {e}")

            for img in div.find_all("img"):
                process_image(img, url, images, f"in-div-{div.name}")

        print(f"找到 {len(images)} 張圖片")
        return images

    finally:
        driver.quit()

def process_image(img, base_url, images_list, container_type=None):
    """處理單個圖片元素並添加到圖片列表"""
    src = img.get("src")
    srcset = img.get("srcset")
    data_src = img.get("data-src")
    data_original = img.get("data-original")  
    alt = img.get("alt", "無描述")

    img_info = {"alt": alt}
    if container_type:
        img_info["container"] = container_type

    if src:
        full_src = urljoin(base_url, src)
        img_info["src"] = full_src
        images_list.append(img_info.copy())

    if data_src:
        full_src = urljoin(base_url, data_src)
        img_info["src"] = full_src
        img_info["type"] = "lazy-loaded"
        images_list.append(img_info.copy())

    if data_original:
        full_src = urljoin(base_url, data_original)
        img_info["src"] = full_src
        img_info["type"] = "data-original"
        images_list.append(img_info.copy())

    if srcset:
        srcs = srcset.split(',')
        for i, src_item in enumerate(srcs):
            parts = src_item.strip().split(' ')
            if parts:
                src_url = parts[0]
                full_src = urljoin(base_url, src_url)
                new_img_info = img_info.copy()
                new_img_info["src"] = full_src
                new_img_info["type"] = "srcset"
                if len(parts) > 1:
                    new_img_info["size"] = parts[1]
                images_list.append(new_img_info)

def save_images_to_json(images, filename="images.json"):
    """ 將圖片資訊儲存為 JSON 檔案 """
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(images, f, ensure_ascii=False, indent=4)
    print(f"已儲存 {len(images)} 筆圖片資訊至 {filename}")

def download_images(images, save_dir="downloaded_images"):
    """ 下載圖片到指定資料夾 """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    downloaded = 0
    for i, img in enumerate(images):
        try:
            img_url = img["src"]
            file_name = os.path.basename(img_url).split('?')[0]
            if not file_name or len(file_name) < 3:  
                file_name = f"image_{i}.jpg"

            img_type = img.get("type", "standard")
            file_name = f"{img_type}_{file_name}" if img_type != "standard" else file_name

            file_path = os.path.join(save_dir, file_name)

            if os.path.exists(file_path):
                print(f"檔案已存在，跳過: {file_name}")
                downloaded += 1
                continue

            sleep(random.uniform(0.5, 2))

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': base_url  
            }

            response = requests.get(img_url, headers=headers, timeout=10, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                downloaded += 1
                print(f"已下載 [{downloaded}/{len(images)}]: {file_name}")
            else:
                print(f"無法下載 {img_url}, 狀態碼: {response.status_code}")
        except Exception as e:
            print(f"下載圖片時發生錯誤 {img.get('src', '未知URL')}: {e}")

    print(f"總共下載了 {downloaded}/{len(images)} 張圖片")

def crawl_website(base_url, max_pages=5, depth=1, current_depth=1, visited=None):
    """爬取整個網站的圖片，支援到指定深度"""
    if visited is None:
        visited = set()

    if current_depth > depth or base_url in visited or len(visited) >= max_pages:
        return []

    print(f"爬取頁面 ({current_depth}/{depth}): {base_url}")
    visited.add(base_url)

    images = get_images_from_page(base_url, use_selenium=True)
    all_images = images.copy()

    try:
        response = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)

            if base_url.split('//')[1].split('/')[0] in full_url and full_url not in visited:
                if not full_url.endswith(('.pdf', '.jpg', '.png', '.zip')) and '#' not in full_url:
                    sub_images = crawl_website(full_url, max_pages, depth, current_depth + 1, visited)
                    all_images.extend(sub_images)

                    if len(visited) >= max_pages:
                        print(f"已達到最大頁面數限制 ({max_pages})")
                        break
    except Exception as e:
        print(f"爬取子頁面時發生錯誤: {e}")

    return all_images

if __name__ == "__main__":
    base_url = "https://tschool.tp.edu.tw/nss/p/introduce"

    crawl_type = input("選擇爬取方式: 1=單頁面, 2=整個網站: ")

    if crawl_type == "2":
        max_pages = int(input("設定最大爬取頁面數 (建議: 5-10): ") or "5")
        depth = int(input("設定爬取深度 (建議: 1-2): ") or "1")
        print(f"開始爬取網站: {base_url}, 最大頁面數: {max_pages}, 深度: {depth}")
        images = crawl_website(base_url, max_pages, depth)
    else:
        print(f"開始爬取單頁面: {base_url}")
        images = get_images_from_page(base_url, use_selenium=True)

    if images:
        save_images_to_json(images, "images.json")
        print(f"總共找到 {len(images)} 張圖片")

        download_choice = input("是否要下載圖片? (y/n): ").lower()
        if download_choice == 'y':
            download_images(images)

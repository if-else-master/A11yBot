import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import json
from time import sleep
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_links_from_page(url, headers=None, use_selenium=False):
    """ 爬取單頁面所有超連結並回傳列表 """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    if use_selenium:
        return get_links_with_selenium(url, headers)

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 檢查是否成功（非 200）

        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            print(f"Warning: {url} 不是 HTML 內容 ({content_type})")

        soup = BeautifulSoup(response.text, 'html.parser')
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            links.append(full_url)

        print(f"找到 {len(links)} 個超連結")
        return links

    except requests.exceptions.RequestException as e:
        print(f"請求錯誤: {url} - {e}")
        return []
    except Exception as e:
        print(f"處理錯誤: {url} - {e}")
        return []

def get_links_with_selenium(url, headers):
    """ 使用 Selenium 渲染頁面並爬取超連結 """
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
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )

        links = []
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            links.append(full_url)

        print(f"找到 {len(links)} 個超連結")
        return links

    finally:
        driver.quit()

def crawl_website(base_url, max_pages=5, depth=1, current_depth=1, visited=None):
    """爬取整個網站的超連結，支援到指定深度"""
    if visited is None:
        visited = set()

    if current_depth > depth or base_url in visited or len(visited) >= max_pages:
        return []

    print(f"爬取頁面 ({current_depth}/{depth}): {base_url}")
    visited.add(base_url)

    links = get_links_from_page(base_url, use_selenium=True)
    all_links = links.copy()

    try:
        response = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)

            if base_url.split('//')[1].split('/')[0] in full_url and full_url not in visited:
                if not full_url.endswith(('.pdf', '.jpg', '.png', '.zip')) and '#' not in full_url:
                    sub_links = crawl_website(full_url, max_pages, depth, current_depth + 1, visited)
                    all_links.extend(sub_links)

                    if len(visited) >= max_pages:
                        print(f"已達到最大頁面數限制 ({max_pages})")
                        break
    except Exception as e:
        print(f"爬取子頁面時發生錯誤: {e}")

    return all_links

def save_links_to_json(links, filename="links.json"):
    """ 將超連結資訊儲存為 JSON 檔案 """
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=4)
    print(f"已儲存 {len(links)} 筆超連結資訊至 {filename}")

if __name__ == "__main__":
    base_url = "https://tschool.tp.edu.tw/nss/p/index"

    crawl_type = input("選擇爬取方式: 1=單頁面, 2=整個網站: ")

    if crawl_type == "2":
        max_pages = int(input("設定最大爬取頁面數 (建議: 5-10): ") or "5")
        depth = int(input("設定爬取深度 (建議: 1-2): ") or "1")
        print(f"開始爬取網站: {base_url}, 最大頁面數: {max_pages}, 深度: {depth}")
        links = crawl_website(base_url, max_pages, depth)
    else:
        print(f"開始爬取單頁面: {base_url}")
        links = get_links_from_page(base_url, use_selenium=True)

    if links:
        print(f"總共找到 {len(links)} 個超連結")
        print(f"總共爬取了 {len(set(links))} 個唯一頁面")
        save_links_to_json(links, "links.json")

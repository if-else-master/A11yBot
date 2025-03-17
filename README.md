# Web Image Scraper

這是一個強大的網頁圖片爬取工具用於協助我將網站修改成無障礙網站，支援使用 `requests` 和 `Selenium` 來獲取圖片，並能夠遞迴爬取整個網站。

## 主要功能
- 單頁面圖片爬取：使用 `requests` 或 `Selenium` 爬取指定頁面的所有圖片。
- 網站圖片爬取：支援深度爬取整個網站，並提取所有圖片。
- 背景圖片提取：解析 `div`、`section`、`header` 等標籤的 `background-image`。
- 圖片下載：自動下載圖片並儲存至本地資料夾。
- 圖片資訊儲存：將所有圖片的資訊（URL、alt 描述、類型）儲存為 JSON。

## 環境需求
- Python 3.7+
- 必要套件（可使用 `pip install -r requirements.txt` 安裝）：
  ```sh
  requests
  beautifulsoup4
  selenium
  webdriver-manager
  ````

## 安裝與使用
### 1. 安裝相依套件
```sh
pip install -r requirements.txt
```

### 2. 運行爬蟲
執行程式，選擇爬取方式：
```sh
python scraper.py
```
輸入 `1` 可爬取單頁面圖片，或輸入 `2` 可遞迴爬取整個網站。

## 程式運行示例
### 爬取單頁面圖片
```sh
選擇爬取方式: 1
開始爬取單頁面: https://example.com
找到 15 張圖片
已儲存 15 筆圖片資訊至 images.json
```

### 爬取整個網站
```sh
選擇爬取方式: 2
設定最大爬取頁面數 (建議: 5-10): 5
設定爬取深度 (建議: 1-2): 1
開始爬取網站: https://example.com, 最大頁面數: 5, 深度: 1
找到 78 張圖片
已儲存 78 筆圖片資訊至 images.json
```

## 下載圖片
爬取完成後，可選擇是否下載圖片：
```sh
是否要下載圖片? (y/n): y
已下載 78/78 張圖片
```

## 目錄結構
```
├── scraper.py            # 主程式
├── requirements.txt      # 依賴套件列表
├── images.json           # 爬取的圖片資訊（自動生成）
└── downloaded_images/    # 下載的圖片（自動生成）
```

聯絡我：rayc57429@gmail.com


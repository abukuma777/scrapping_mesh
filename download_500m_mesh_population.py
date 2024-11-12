import os
import re
import shutil
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 都道府県番号と都道府県名の対応辞書
prefecture_codes = {
    "北海道": "01",
    "青森県": "02",
    "岩手県": "03",
    "宮城県": "04",
    "秋田県": "05",
    "山形県": "06",
    "福島県": "07",
    "茨城県": "08",
    "栃木県": "09",
    "群馬県": "10",
    "埼玉県": "11",
    "千葉県": "12",
    "東京都": "13",
    "神奈川県": "14",
    "新潟県": "15",
    "富山県": "16",
    "石川県": "17",
    "福井県": "18",
    "山梨県": "19",
    "長野県": "20",
    "岐阜県": "21",
    "静岡県": "22",
    "愛知県": "23",
    "三重県": "24",
    "滋賀県": "25",
    "京都府": "26",
    "大阪府": "27",
    "兵庫県": "28",
    "奈良県": "29",
    "和歌山県": "30",
    "鳥取県": "31",
    "島根県": "32",
    "岡山県": "33",
    "広島県": "34",
    "山口県": "35",
    "徳島県": "36",
    "香川県": "37",
    "愛媛県": "38",
    "高知県": "39",
    "福岡県": "40",
    "佐賀県": "41",
    "長崎県": "42",
    "熊本県": "43",
    "大分県": "44",
    "宮崎県": "45",
    "鹿児島県": "46",
    "沖縄県": "47",
}

# dataフォルダの削除と再作成
data_dir = os.path.join(os.getcwd(), "data")
if os.path.exists(data_dir):
    shutil.rmtree(data_dir)
os.makedirs(data_dir)


# Chromeオプションの設定
def setup_chrome_options(download_dir):
    chrome_options = Options()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options


# 都道府県名の補完処理
def normalize_prefecture_name(prefecture):
    prefecture = prefecture.strip()
    if prefecture in prefecture_codes:
        return prefecture
    # 特別なケース
    if prefecture == "東京":
        return "東京都"
    if prefecture == "北海道":
        return "北海道"
    if prefecture == "大阪":
        return "大阪府"
    if prefecture == "京都":
        return "京都府"
    # 一般的な県の場合
    return prefecture + "県"


# 年度と都道府県ごとのダウンロード先を作成
def create_download_path(year, prefecture):
    normalized_prefecture = normalize_prefecture_name(prefecture)
    prefecture_code = prefecture_codes.get(normalized_prefecture, "00")
    folder_name = f"{prefecture_code}_{normalized_prefecture}"
    path = os.path.join(data_dir, str(year), folder_name)
    os.makedirs(path, exist_ok=True)
    return path


# Seleniumのセットアップ
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=setup_chrome_options(data_dir))

# ターゲットURL
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-mesh500h30.html"
driver.get(url)
time.sleep(2)

# BeautifulSoupでページ内容をパース
soup = BeautifulSoup(driver.page_source, "html.parser")
rows = soup.select("tbody tr")

# データの取得とダウンロード処理
for row in rows[1:]:
    try:
        # 都道府県名を取得
        prefecture_element = row.select_one("td[id^='prefecture']")
        if prefecture_element:
            prefecture = prefecture_element.text.strip()
        else:
            continue  # 都道府県が取得できない場合はスキップ

        # ファイル名を取得
        file_name_element = row.select("td")[4] if len(row.select("td")) > 4 else None
        file_name = file_name_element.text.strip() if file_name_element else "Unknown_File"

        # 年度情報を取得
        year_element = row.select("td")[2] if len(row.select("td")) > 2 else None
        year_text = year_element.text.strip() if year_element else "Unknown_Year"
        match = re.search(r"(\d{4})年", year_text)
        year = match.group(1) if match else "unknown_year"

        # ダウンロード先のフォルダを作成
        download_path = create_download_path(year, prefecture)

        # ダウンロードリンクを取得
        link_element = row.select_one("a")
        if link_element and link_element.has_attr("onclick"):
            onclick_attr = link_element["onclick"]
            download_link = re.search(r"DownLd\('.*?', '.*?', '(.*?)'", onclick_attr)
            if download_link:
                full_url = f"https://nlftp.mlit.go.jp{download_link.group(1)}"

                print(f"Downloading {file_name} for {prefecture} ({year}) to {download_path}...")

                # ダウンロードボタンをクリック
                download_button = driver.find_element(By.XPATH, f"//a[contains(@onclick, '{file_name}')]")
                download_button.click()
                time.sleep(5)  # ダウンロード完了待機

    except Exception as e:
        print(f"Error downloading {file_name} for {prefecture}: {e}")

# ブラウザを閉じる
driver.quit()

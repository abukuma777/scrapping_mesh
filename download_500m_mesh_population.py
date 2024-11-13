import os
import re
import shutil
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

# ログファイルの設定（上書きモード）
log_file = "output.log"
sys.stdout = open(log_file, "w", encoding="utf-8")
sys.stderr = open(log_file, "w", encoding="utf-8")


def setup_data_directory():
    """./data/paquet_500mメッシュ人口推計 フォルダを削除して再作成"""
    base_dir = os.path.join(os.getcwd(), "data", "paquet_500mメッシュ人口推計")

    # 既にフォルダが存在する場合は削除して再作成
    if os.path.exists(base_dir):
        print("Existing './data/paquet_500mメッシュ人口推計' folder found. Deleting...")
        shutil.rmtree(base_dir)

    os.makedirs(base_dir, exist_ok=True)
    print("Created new './data/paquet_500mメッシュ人口推計' folder.")
    return base_dir


def setup_chrome_options(download_dir):
    chrome_options = Options()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.popups": 0,
        "directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options


def handle_download_alert(driver, retries=5):
    """ダウンロード確認ポップアップの処理（リトライ付き）"""
    for attempt in range(retries):
        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            print(f"Download alert detected: {alert.text}")
            alert.accept()
            print("Download confirmed.")
            return True
        except Exception as e:
            print(f"Failed to handle download alert on attempt {attempt + 1}: {e}")
            time.sleep(1)
    return False


def close_survey_popup(driver):
    """アンケートのポップアップを無視して閉じる"""
    try:
        print("Attempting to close survey popup...")
        driver.execute_script("document.querySelector('.modal-close.btn.waves-effect.waves-light').click();")
        WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.CLASS_NAME, "modal-container")))
        print("Survey popup closed successfully.")
        return True
    except Exception as e:
        print(f"Failed to close survey popup: {e}")
        return False


def download_all_files(driver):
    """全ての都道府県のダウンロードボタンをクリック"""
    buttons = driver.find_elements(By.CSS_SELECTOR, "a.btn_padding")
    print(f"Found {len(buttons)} download buttons.")

    for index, button in enumerate(buttons):
        try:
            # ボタンをクリック
            print(f"Attempting to click download button {index + 1}/{len(buttons)}")
            driver.execute_script("arguments[0].click();", button)

            # 最初のクリック時のみアンケートポップアップを処理
            if index == 0:
                close_survey_popup(driver)

            # ダウンロード確認ポップアップを処理
            if handle_download_alert(driver):
                print(f"Download alert handled for button {index + 1}.")

            # ファイル名を動的に取得（ここは必要に応じて修正）
            file_name = f"500m_mesh_suikei_2018_shape_{index + 1:02d}.zip"

            # ダウンロードの完了を待機
            if not download_wait(file_name):
                # 再試行
                print(f"Retrying download for {file_name}")
                driver.execute_script("arguments[0].click();", button)
                handle_download_alert(driver)
                download_wait(file_name)

        except Exception as e:
            print(f"Failed to download file for button {index + 1}: {e}")


def download_wait(file_name):
    """ダウンロードが完了するまで待機し、ファイルの存在を確認"""
    global data_dir  # グローバル変数 data_dir を明示的に参照
    download_complete = False
    retries = 20  # 最大リトライ回数を増やす
    download_folder = data_dir

    file_path = os.path.join(download_folder, file_name)
    prev_size = -1

    for attempt in range(retries):
        # ダウンロード中のファイル（.crdownload）が存在するかチェック
        in_progress_files = [f for f in os.listdir(download_folder) if f.endswith(".crdownload")]
        if in_progress_files:
            print(f"Attempt {attempt + 1}: Waiting for download to complete... {in_progress_files}")
            time.sleep(2)
        else:
            # ダウンロードが完了したか確認
            if os.path.exists(file_path):
                current_size = os.path.getsize(file_path)
                # サイズが変わらない場合、ダウンロード完了と判断
                if current_size > 0 and current_size == prev_size:
                    print(f"Download completed: {file_name}")
                    download_complete = True
                    break
                prev_size = current_size
                print(f"Checking file size: {current_size} bytes")
            else:
                print(f"No completed file found yet for {file_name}. Retrying...")
            time.sleep(1)

    if not download_complete:
        print(f"Download did not complete for {file_name}. Retrying manually...")
        return False
    return True


def move_all_files(base_dir):
    """ダウンロード完了後、ファイルを適切なフォルダに移動"""
    prefecture_map = {
        "01": "北海道",
        "02": "青森",
        "03": "岩手",
        "04": "宮城",
        "05": "秋田",
        "06": "山形",
        "07": "福島",
        "08": "茨城",
        "09": "栃木",
        "10": "群馬",
        "11": "埼玉",
        "12": "千葉",
        "13": "東京",
        "14": "神奈川",
        "15": "新潟",
        "16": "富山",
        "17": "石川",
        "18": "福井",
        "19": "山梨",
        "20": "長野",
        "21": "岐阜",
        "22": "静岡",
        "23": "愛知",
        "24": "三重",
        "25": "滋賀",
        "26": "京都",
        "27": "大阪",
        "28": "兵庫",
        "29": "奈良",
        "30": "和歌山",
        "31": "鳥取",
        "32": "島根",
        "33": "岡山",
        "34": "広島",
        "35": "山口",
        "36": "徳島",
        "37": "香川",
        "38": "愛媛",
        "39": "高知",
        "40": "福岡",
        "41": "佐賀",
        "42": "長崎",
        "43": "熊本",
        "44": "大分",
        "45": "宮崎",
        "46": "鹿児島",
        "47": "沖縄",
    }

    # 正規表現でファイル名から年と都道府県番号を抽出
    pattern = re.compile(r"500m_mesh_suikei_(\d{4})_shape_(\d{2})\.zip")

    for file_name in os.listdir(base_dir):
        if file_name.endswith(".zip"):
            try:
                # 正規表現で年と都道府県番号を抽出
                match = pattern.match(file_name)
                if not match:
                    print(f"Unexpected file format: {file_name}")
                    continue

                year = match.group(1)  # 例: '2018'
                prefecture_number = match.group(2)  # 例: '01'

                # 都道府県名を取得
                prefecture_name = prefecture_map.get(prefecture_number, "不明")

                # 保存先フォルダを構築
                dest_folder = os.path.join(base_dir, f"{year}/{prefecture_number}_{prefecture_name}")

                # ディレクトリが存在しない場合は作成
                os.makedirs(dest_folder, exist_ok=True)

                # ファイルの移動
                src_path = os.path.join(base_dir, file_name)
                dest_path = os.path.join(dest_folder, file_name)

                # 移動処理
                shutil.move(src_path, dest_path)
                print(f"Moved file to: {dest_path}")

            except Exception as e:
                print(f"Failed to move file {file_name}: {e}")


if __name__ == "__main__":
    try:
        # データ保存ディレクトリのセットアップ
        data_dir = setup_data_directory()  # ここで data_dir として統一

        print("Starting download process...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=setup_chrome_options(data_dir)
        )

        url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-mesh500h30.html"
        driver.get(url)
        time.sleep(2)

        # 全都道府県のデータをダウンロード
        download_all_files(driver)

        # ダウンロードしたファイルを適切なフォルダに移動
        move_all_files(data_dir)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.quit()
            print("Driver closed.")
        print("Process completed.")

import os
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
    """data フォルダを削除して再作成"""
    data_dir = os.path.join(os.getcwd(), "data")

    # 既にフォルダが存在する場合は削除
    if os.path.exists(data_dir):
        print("Existing 'data' folder found. Deleting...")
        shutil.rmtree(data_dir)

    # 新しくフォルダを作成
    os.makedirs(data_dir, exist_ok=True)
    print("Created new 'data' folder.")

    return data_dir


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
    download_complete = False
    retries = 10

    for attempt in range(retries):
        # ダウンロード中のファイル（.crdownload）が存在するかチェック
        in_progress_files = [f for f in os.listdir(data_dir) if f.endswith(".crdownload")]
        if in_progress_files:
            print(f"Attempt {attempt + 1}: Waiting for download to complete... {in_progress_files}")
            time.sleep(2)
        else:
            # ファイルが正しくダウンロードされたか確認
            file_path = os.path.join(data_dir, file_name)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                print(f"Download completed: {file_name}")
                download_complete = True
                break
            else:
                print(f"No completed file found yet for {file_name}. Retrying...")
                time.sleep(2)

    if not download_complete:
        print(f"Download did not complete for {file_name}. Retrying manually...")
        return False
    return True


if __name__ == "__main__":
    driver = None  # 初期化しておく
    try:
        # データ保存ディレクトリのセットアップ
        data_dir = setup_data_directory()

        print("Starting download process...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=setup_chrome_options(data_dir)
        )

        url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-mesh500h30.html"
        driver.get(url)
        time.sleep(2)

        # 全都道府県のデータをダウンロード
        download_all_files(driver)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # driver が定義されていれば quit() を呼び出す
        if driver:
            driver.quit()
            print("Driver closed.")
        print("Process completed.")

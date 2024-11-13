import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ログファイルの設定（上書きモード）
log_file = "output.log"
sys.stdout = open(log_file, "w", encoding="utf-8")
sys.stderr = open(log_file, "w", encoding="utf-8")

# データ保存ディレクトリの設定
data_dir = os.path.join(os.getcwd(), "data")
os.makedirs(data_dir, exist_ok=True)


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
            print(f"Attempting to click download button {index + 1}/{len(buttons)}")
            driver.execute_script("arguments[0].click();", button)

            # 最初のクリック時のみアンケートポップアップを処理
            if index == 0:
                close_survey_popup(driver)

            # ダウンロード確認ポップアップを処理
            if handle_download_alert(driver):
                print(f"Download alert handled for button {index + 1}.")

            # ダウンロードの完了を待機
            download_wait()
        except Exception as e:
            print(f"Failed to download file for button {index + 1}: {e}")


def download_wait():
    """ダウンロードが完了するまで待機"""
    download_complete = False
    download_folder = data_dir
    retries = 10

    for attempt in range(retries):
        if any([filename.endswith(".crdownload") for filename in os.listdir(download_folder)]):
            print(f"Attempt {attempt + 1}: Waiting for download to complete...")
            time.sleep(2)
        else:
            print("Checking if file exists...")
            if any([filename.endswith(".zip") for filename in os.listdir(download_folder)]):
                print("Download completed successfully.")
                download_complete = True
                break
            else:
                print("No downloaded file found yet. Retrying...")
                time.sleep(2)

    if not download_complete:
        print("Download did not complete in time.")


if __name__ == "__main__":
    try:
        print("Starting download process...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=setup_chrome_options(data_dir)
        )

        url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-mesh500h30.html"
        driver.get(url)
        time.sleep(2)

        download_all_files(driver)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
        print("Process completed.")

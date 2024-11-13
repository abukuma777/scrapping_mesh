import subprocess


def generate_requirements():
    """現在の環境から `requirements.txt` を生成する"""
    try:
        # `pip freeze` を使用して、現在の環境のパッケージリストを取得
        result = subprocess.run(["pip", "freeze"], stdout=subprocess.PIPE, text=True)

        # `requirements.txt` ファイルに書き込み
        with open("requirements.txt", "w", encoding="utf-8") as file:
            file.write(result.stdout)

        print("`requirements.txt` が生成されました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    generate_requirements()

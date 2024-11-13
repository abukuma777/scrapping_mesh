# 500m メッシュ別将来推計人口データ スクレイピング

## 概要

このリポジトリでは、以下2つのデータをスクレイピングするPythonスクリプトを提供しています。

- [国土数値情報 | 500mメッシュ別将来推計人口データ（H30国政局推計）（shape形式版）](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-mesh500h30.html)
- [世帯主の男女・年齢5歳階級別・家族類型別世帯数 - 『日本の世帯数の将来推計（都道府県別推計）』（2019年推計）](https://www.ipss.go.jp/pp-pjsetai/j/hpjp2019/setai/shosai.asp)

## 動作環境

- Python 3.8 以上
- Google Chrome（最新バージョン）
- ChromeDriver（`webdriver_manager` を使用して自動インストール）

## セットアップ

### 必要なPythonパッケージのインストール

```bash
pip install -r requirements.txt
```

### requirements.txt

以下の内容で requirements.txt ファイルを作成してください。
```
selenium
webdriver_manager
tqdm
```

## 使い方
## スクリプトの実行方法
`download_500m_mesh_population.py` を実行して、500m メッシュ別将来推計人口データをダウンロードします。
```bash
python download_500m_mesh_population.py
```

データは自動的に以下の構造で data/ フォルダに保存されます。
```
data/
└── paquet_500mメッシュ人口推計/
    └── 2018/
        ├── 01_北海道/
        │   └── 500m_mesh_suikei_2018_shape_01.zip
        ├── 02_青森/
        │   └── 500m_mesh_suikei_2018_shape_02.zip
        └── ...
```

### 注意事項
data フォルダは .gitignore で無視されています。
スクリプト実行後に data/ フォルダが自動生成され、必要なデータがダウンロードされます。

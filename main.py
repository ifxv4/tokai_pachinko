import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import csv
import os

# 東海パチンコのトラURL
URL = 'https://p-tora.com/toukai/hall/index.html?no=12709'
# 遷移ページのひな型
MACHINE_URL = 'https://p-tora.com/toukai/hall/dai.php?tno=12709&sis=TVpZADctLDc4&item_name='
# 遷移ページ日付枠（id = 1は前日）
DATE_FRAME = '&offset_date='
# 日付ID（id = 0は当日、値が増える度に前の日になる）
DATE_ID = "0"
# 遷移ページ機種番号
MACHINE_NUM = '&dno='
# 正規表現パターン
PATTERN = r"document\.getElementById\('item_item_name'\)\.value='(.*?)';"
# style(スクレイピング時の検索文字列)
STYLE = "margin: 5px 0"


# 前日の日付を取得
def getSelectDate():
    # 現在の日付を取得
    current_date = datetime.now()
    # 昨日の日付を計算
    select_date = current_date - timedelta(days=int(DATE_ID))
    # 年、月、日をリストに格納して返す
    dateStr = select_date.strftime("%Y-%m-%d")
    return dateStr


# スロットの詳細情報を入手
def getDetailInfo(_link, _name, _number, _date):
    bounas_info = []
    request = requests.get(_link)
    request.encoding = 'Shift-JIS'
    soup = BeautifulSoup(request.text, 'lxml')
    getPicture(soup, _name, _number, _date)
    bounas_info = getBounas(soup)
    if bounas_info:
        outPutInfo(bounas_info, _name, _number, _date)


# 画像を全て入手
def getPicture(_soup, _name, _number, _date):
    # pictureディレクトリ名
    img_dir = "img_data/" + _date + "/" + _date + _name + "/"
    # ディレクトリが存在しない場合は作成する
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    # img要素のsrc属性の値を取得
    try:
        cel = _soup.find('td', id="cel" + DATE_ID)
        style = cel.find('div', style=STYLE)
        element = style.find("img", class_="chartImage")
        path = element.get("image-path")
        image_url = "https://p-tora.com" + path
        response = requests.get(image_url)
        # レスポンスが成功した場合、画像を保存する
        if response.status_code == 200:
            with open(img_dir + "/" + _date + _name + "-" + _number + ".gif", "wb") as f:
                f.write(response.content)
            print("画像をダウンロードしました")
        else:
            print("画像のダウンロードに失敗しました")
    except Exception as e:
        # その他のすべての例外をキャッチする
        print("前日の稼働はありません")



# ボーナス情報を入手
def getBounas(_soup):
    data_array = []
    try:
        cel = _soup.find('td', id="cel" + DATE_ID)
        table = cel.find('table', class_="hist_table")
        # テーブルの全ての行（<tr>）を取得
        rows = table.find_all("tr")
        # 各行のテキストを配列に格納
        for row in rows:
            # 各行のセル（<td>）を取得
            cells = row.find_all("td")
            row_data = []
            for cell in cells:
                # セルのテキストを配列に追加
                row_data.append(cell.text.strip())
            data_array.append(row_data)
    except Exception as e:
        # その他のすべての例外をキャッチする
        print("前日の稼働はありません")
    return data_array


# ボーナス種類をcsvに出力
def outPutInfo(_info, _name, _number, _date):
    # csvファイル名
    csv_name = _date + _name + "-" + _number + ".csv"
    # csvディレクトリ名
    child_dir = "csv_data"
    data_dir = _date
    csv_dir = _date + _name
    # csv上部
    csv_text = '時刻,ボーナス種類,ボーナス回数\n'

    # 現在の作業ディレクトリを取得
    current_dir = os.getcwd()
    # 子ディレクトリのパス
    child_dir_path = os.path.join(current_dir, child_dir)
    # csvディレクトリのパス
    data_dir = os.path.join(child_dir_path, data_dir)
    csv_dir = os.path.join(data_dir, csv_dir)
    csv_path = os.path.join(csv_dir, csv_name)

    # CSVディレクトリが存在しない場合は作成する
    if not os.path.exists(child_dir_path):
        os.mkdir(child_dir_path)
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    if not os.path.exists(csv_dir):
        os.mkdir(csv_dir)

    for array_info in _info:
        for cel_info in array_info:
            csv_text += cel_info + ','
        csv_text += "\n"
    # テキストデータを行ごとに分割してリストに変換
    lines = csv_text.strip().split("\n")

    # CSVファイルに書き込む
    with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # 各行をCSVファイルに書き込む
        for line in lines:
            # カンマで分割してリストに変換
            row = line.split(",")
            # CSVファイルに書き込む
            writer.writerow(row)
    print(f"CSVファイル '{child_dir}\\{csv_name}' にデータを書き込みました。")
        

# スクレイピングして機種名とリンクを配列に収める
def scrape_slot_machines(_url):
    response = requests.get(_url)
    response.encoding = 'Shift-JIS'
    soup = BeautifulSoup(response.text, 'lxml')
    slots_info  = []
    machine_div = soup.find('div', id='pattern5_s')
    # 各<td>要素について処理を行う
    for td_element in machine_div.find_all("td", class_="L"):
      # スロットの名前を取得する
      slot_name = td_element.a.text.strip()
      # onclick属性から値を抽出する
      onclick_value = td_element.input["onclick"]
      # 抽出したものからパターンに一致する部分を取り出す
      match = re.search(PATTERN, onclick_value)
      # 取り出した部分
      extracted_string = match.group(1)
      # スロットの名前とonclick属性の値をリストに追加する
      slots_info.append({"name": slot_name, "link": extracted_string})
    return slots_info


# 機種の番号を格納
def getSlotNumber(_link):
    number_array = []
    request = requests.get(_link)
    request.encoding = 'Shift-JIS'
    soup = BeautifulSoup(request.text, 'lxml')
    slots_info = soup.find_all("td", class_="td1")
    for i, td in enumerate(slots_info):
        if i % 7 == 0:
            number_array.append(td.text.strip())
    print(number_array)
    return number_array


# 全機種ループ処理
def getAllData(_url, _date):
    slot_machines = scrape_slot_machines(_url)
    for machine in slot_machines:
        print(f"機種名: {machine['name']}, リンク: {machine['link']}")
        # リンク先を作成
        link = MACHINE_URL + machine['link'] + DATE_FRAME + DATE_ID
        # 機種の番号を格納
        number_array = [] 
        number_array = getSlotNumber(link)
        # 詳細ページのリンクを作成してアクセス
        for i in number_array:
            link = MACHINE_URL + machine['link'] + MACHINE_NUM + i + DATE_FRAME + DATE_ID
            print("url_debug:", link)
            # 画像とボーナス情報を入手
            getDetailInfo(link, machine['name'], i, _date)


def main():
    dateStr = getSelectDate()
    # デバッグ表示：日付を表示
    print("選択した日付:", dateStr)
    # 全機種ループ処理
    getAllData(URL, dateStr)


if __name__ == "__main__":
    main()
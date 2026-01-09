
import flet as ft
import requests
from datetime import datetime
import sqlite3

DB_NAME = "weather.db"

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"


def format_date(d):
    return datetime.fromisoformat(d).strftime("%m/%d")

def save_weather(code, date, weather, tmin, tmax):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO weather_forecast
        (office_code, date, weather, temp_min, temp_max)
        VALUES (?, ?, ?, ?, ?)
    """, (code, date, weather, tmin, tmax))

    conn.commit()
    conn.close()


def load_weather(code):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT date, weather, temp_min, temp_max
        FROM weather_forecast
        WHERE office_code = ?
        ORDER BY date
    """, (code,))
    rows = cur.fetchall()
    conn.close()
    return rows

def load_weather_by_date(code, date):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT date, weather, temp_min, temp_max
        FROM weather_forecast
        WHERE office_code = ?
        AND date LIKE ?
        ORDER BY date
    """, (code, date + "%"))
    rows = cur.fetchall()
    conn.close()
    return rows


def main(page: ft.Page):
    selected_date = None
    selected_office = None

    page.title = "気象庁 天気予報アプリ"
    page.window_width = 1000
    page.window_height = 650

    # =====================
    # エリア情報取得
    # =====================
    area_json = requests.get(AREA_URL).json()
    centers = area_json["centers"]
    offices = area_json["offices"]

    regions = {}
    for c_code, c in centers.items():
        regions[c_code] = {
            "name": c["name"],
            "offices": []
        }

    for o_code, o in offices.items():
        parent = o.get("parent")
        if parent in regions:
            regions[parent]["offices"].append({
                "code": o_code,
                "name": o["name"]
            })

    # =====================
    # 右側表示エリア
    # =====================
    title_text = ft.Text(size=30, weight="bold")

    weather_list = ft.Column(
        expand=True,
        scroll="auto",
        spacing=8
    )


    # =====================
    # 1行UI
    # =====================
    def weather_row(date, weather, tmin, tmax):
        return ft.Container(
            padding=10,
            content=ft.Row(
                alignment="spaceBetween",
                controls=[
                    ft.Text(date, width=100, weight="bold"),
                    ft.Text(weather, expand=True),
                ]
            )
        )

        # =====================
    # 日付選択 UI
    # =====================
    def on_date_change(e):
        if selected_office is None:
            return

        weather_list.controls.clear()

        rows = load_weather_by_date(
            selected_office,
            e.control.value.isoformat()
        )

        if not rows:
            weather_list.controls.append(
                ft.Text("この日のデータはありません")
            )
        else:
            for d, w, mn, mx in rows:
                weather_list.controls.append(
                    weather_row(
                        format_date(d),
                        w,
                        mn if mn is not None else "-",
                        mx if mx is not None else "-"
                    )
                )
        page.update()

    date_picker = ft.DatePicker(on_change=on_date_change)
    page.overlay.append(date_picker)

    date_button = ft.ElevatedButton(
        "日付を選択",
        on_click=lambda e: date_picker.pick_date()
    )
    weather_view = ft.Column(
        expand=True,
        controls=[
            title_text,
            date_button,
            ft.Divider(),
            weather_list
        ]
    )



    # =====================
    # 天気取得・表示
    # =====================
    def show_weather(office_code):
        nonlocal selected_office
        selected_office = office_code
        weather_list.controls.clear()

        res = requests.get(FORECAST_URL.format(office_code))
        if res.status_code != 200:
            weather_list.controls.append(
                ft.Text("天気データを取得できませんでした")
            )
            page.update()
            return

        try:
            forecast = res.json()[0]
        except Exception:
            weather_list.controls.append(
                ft.Text("対応していない地域です")
            )
            page.update()
            return
        title_text.value = forecast["publishingOffice"]

        ts_weather = forecast["timeSeries"][0]
        ts_temp = forecast["timeSeries"][2] if len(forecast["timeSeries"]) > 2 else None

        area_weather = ts_weather["areas"][0]
        area_temp = ts_temp["areas"][0] if ts_temp else {}

        dates = ts_weather["timeDefines"]
        weathers = area_weather["weathers"]

        tmin_list = area_temp.get("tempsMin", [])
        tmax_list = area_temp.get("tempsMax", [])

        # --- DBに保存 ---
        for i in range(len(dates)):
            tmin = tmin_list[i] if i < len(tmin_list) else None
            tmax = tmax_list[i] if i < len(tmax_list) else None

            save_weather(
                office_code,
                dates[i],
                weathers[i],
                tmin,
                tmax
            )

        # --- DBから表示 ---
        for d, w, mn, mx in load_weather(office_code):
            weather_list.controls.append(
                weather_row(
                    format_date(d),
                    w,
                    mn if mn is not None else "-",
                    mx if mx is not None else "-"
                )
            )

        page.update()



    # =====================
    # 左ナビ
    # =====================
    nav = ft.Column(width=320, scroll="auto")
    nav.controls.append(ft.Text("地域を選択", size=20, weight="bold"))

    for region in regions.values():
        tile = ft.ExpansionTile(
            title=ft.Text(region["name"], weight="bold"),
            controls=[]   # ← これが必須
        )

        for office in region["offices"]:
            tile.controls.append(
                ft.TextButton(
                    content=ft.Text(office["name"]),
                    on_click=lambda e, c=office["code"]: show_weather(c)
                )

            )
        nav.controls.append(tile)

    # =====================
    # 初期表示
    # =====================
    for region in regions.values():
        if region["offices"]:
            show_weather(region["offices"][0]["code"])
            break

    # =====================
    # レイアウト
    # =====================
    page.add(
        ft.Row(
            [
                nav,
                ft.VerticalDivider(width=1),
                weather_view
            ],
            expand=True
        )
    )


ft.app(main)

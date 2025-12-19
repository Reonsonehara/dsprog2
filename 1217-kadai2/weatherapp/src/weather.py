
import flet as ft
import requests
from datetime import datetime

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"


def format_date(d):
    return datetime.fromisoformat(d).strftime("%m/%d")


def main(page: ft.Page):
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

    weather_view = ft.Column(
        expand=True,
        controls=[
            title_text,
            ft.Divider(),
            weather_list
        ]
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
    # 天気取得・表示
    # =====================
    def show_weather(office_code):
        weather_list.controls.clear()

        res = requests.get(FORECAST_URL.format(office_code))
        forecast = res.json()[0]
        title_text.value = forecast["publishingOffice"]

        ts_weather = forecast["timeSeries"][0]
        ts_temp = forecast["timeSeries"][2] if len(forecast["timeSeries"]) > 2 else None

        area_weather = ts_weather["areas"][0]
        area_temp = ts_temp["areas"][0] if ts_temp else {}

        dates = ts_weather["timeDefines"]
        weathers = area_weather["weathers"]

        tmin_list = area_temp.get("tempsMin", [])
        tmax_list = area_temp.get("tempsMax", [])

        for i in range(len(dates)):
            # --- あってもなくても表示 ---
            tmin = (
                tmin_list[i]
                if i < len(tmin_list) and tmin_list[i]
                else "-"
            )
            tmax = (
                tmax_list[i]
                if i < len(tmax_list) and tmax_list[i]
                else "-"
            )

            weather_list.controls.append(
                weather_row(
                    format_date(dates[i]),
                    weathers[i],
                    tmin,
                    tmax
                )
            )

        page.update()


    # =====================
    # 左ナビ
    # =====================
    nav = ft.Column(width=320, scroll="auto")
    nav.controls.append(ft.Text("地域を選択", size=20, weight="bold"))

    for region in regions.values():
        tile = ft.ExpansionTile(title=ft.Text(region["name"], weight="bold"))
        for office in region["offices"]:
            tile.controls.append(
                ft.TextButton(
                    text=office["name"],
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

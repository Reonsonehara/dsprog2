import flet as ft

# メイン関数を定義
def main(page: ft.Page):
    # カウンター表示用のテキストを作成
    counter = ft.Text("0", size=50, data=0)

    #
    hoge = ft.Text("Hello, Flet!", size=30)

    def increment_click(e):
        counter.data += 1
        counter.value = str(counter.data)
        counter.update()
    def decrement_click(e):
        counter.data -= 1
        counter.value = str(counter.data)
        counter.update()
        
    # カウンターを増やすボタンを追加
    page.floating_action_button = ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=increment_click)
    # ページにコンテナを追加
    page.add(
        ft.SafeArea(
            ft.Container(
                content=ft.Column([counter, hoge]),
                alignment=ft.alignment.center,
            ),
            expand=True,
        ),
        ft.FloatingActionButton(icon=ft.Icons.REMOVE, on_click=decrement_click),
    )


ft.app(main)

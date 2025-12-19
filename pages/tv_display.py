import flet as ft
import threading
import time
from datetime import datetime

class TVDisplayPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.is_active = True 
        
        self.current_patient_card = ft.Container()
        self.next_patients_list = ft.Column(spacing=10)
        self.lbl_time = ft.Text(size=20, color="white70")

    def view(self):
        self.page.title = "Klinik Bekleme Ekranı"
        self.page.theme_mode = ft.ThemeMode.DARK 
        
        left_panel = ft.Container(
            content=ft.Column([
                ft.Text("ŞU AN GÖRÜŞÜLEN", size=30, weight="bold", color="teal"),
                ft.Divider(color="teal"),
                self.current_patient_card,
                ft.Container(expand=True),
                ft.Row([
                    # DÜZELTME: ft.icons -> ft.Icons
                    ft.Icon(ft.Icons.ACCESS_TIME, color="white70"),
                    self.lbl_time
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=6,
            bgcolor="#1f2630",
            padding=40,
            border_radius=20,
            margin=10
        )

        right_panel = ft.Container(
            content=ft.Column([
                ft.Text("SIRADAKİ HASTALAR", size=24, weight="bold", color="orange"),
                ft.Divider(color="orange"),
                self.next_patients_list
            ]),
            expand=4,
            bgcolor="#263238",
            padding=30,
            border_radius=20,
            margin=10
        )

        threading.Thread(target=self.update_loop, daemon=True).start()

        return ft.View(
            "/tv",
            [
                ft.Row([left_panel, right_panel], expand=True)
            ],
            bgcolor="black",
            padding=20
        )

    def update_loop(self):
        while self.is_active:
            try:
                now = datetime.now().strftime("%H:%M")
                self.lbl_time.value = now

                appointments = self.db.get_todays_appointments()
                current_p = None
                waiting_list = []

                if appointments:
                    for app in appointments:
                        if app[3] == "Görüşülüyor":
                            current_p = app
                            break
                    if not current_p:
                        for app in appointments:
                            if app[3] == "Bekliyor":
                                current_p = app
                                break
                    for app in appointments:
                        if app[3] == "Bekliyor" and (not current_p or app[0] != current_p[0]):
                            waiting_list.append(app)

                self.update_ui(current_p, waiting_list)
                
                if not self.page.views or self.page.views[-1].route != "/tv":
                    self.is_active = False
                    break

                self.page.update()
                time.sleep(5) 

            except Exception as e:
                print(f"TV Loop Error: {e}")
                time.sleep(5)

    def update_ui(self, current, waiting):
        if current:
            name_display = current[1] 
            self.current_patient_card.content = ft.Column([
                # DÜZELTME: ft.icons -> ft.Icons
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=100, color="white"),
                ft.Text(name_display, size=40, weight="bold", color="white", text_align="center"),
                ft.Container(
                    content=ft.Text("İÇERİ GİRİNİZ", color="white", weight="bold"),
                    bgcolor="green", padding=15, border_radius=10, margin=ft.margin.only(top=20)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            self.current_patient_card.content = ft.Column([
                # DÜZELTME: ft.icons -> ft.Icons
                ft.Icon(ft.Icons.HOTEL_CLASS, size=80, color="grey"),
                ft.Text("Şu an hasta yok", size=20, color="grey")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.next_patients_list.controls.clear()
        if not waiting:
            self.next_patients_list.controls.append(ft.Text("Sırada bekleyen yok.", color="grey"))
        else:
            for p in waiting:
                t_str = p[2].strftime("%H:%M")
                card = ft.Container(
                    content=ft.Row([
                        ft.Text(t_str, size=20, weight="bold", color="orange"),
                        ft.Text(p[1], size=20, color="white")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=15,
                    bgcolor="#37474f",
                    border_radius=10
                )
                self.next_patients_list.controls.append(card)
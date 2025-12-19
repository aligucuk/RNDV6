import flet as ft
from datetime import datetime
import json

class DoctorHomePage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.user_role = page.session.get("user_role")
        self.user_id = page.session.get("user_id")
        self.user_name = page.session.get("user_name")

        # BUG FIX: Tema her girişte yenilenmeli
        self.theme_color = self.db.get_setting("theme_color") or "teal"
        self.is_dark = (self.db.get_setting("theme_mode") == "dark")
        
        self.bg_color = "#1f2630" if self.is_dark else "#f5f7f8"
        self.text_color = "white" if self.is_dark else "#37474f"

    def view(self):
        # 1. Header
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(f"Merhaba, {self.user_name}", size=24, weight="bold", color="white"), 
                    ft.Text(f"Yetki: {self.user_role.capitalize()}", color="white70")
                ]),
                ft.IconButton("logout", icon_color="white", on_click=lambda _: self.page.go("/"))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=30, bgcolor=self.theme_color, border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30)
        )

        # 2. Menü Yetkilendirme (RBAC)
        # Hangi kartın kime görüneceği
        cards_config = [
            # Herkes Görür
            {"id": "card_pat", "t": "Hastalar", "i": ft.Icons.PEOPLE, "c": "blue", "r": "/patient_list", "roles": ["admin", "doktor", "sekreter"]},
            {"id": "card_app", "t": "Randevular", "i": ft.Icons.CALENDAR_TODAY, "c": "teal", "r": "/appointments", "roles": ["admin", "doktor", "sekreter"]},
            {"id": "card_cal", "t": "Ajanda", "i": ft.Icons.CALENDAR_MONTH, "c": "purple", "r": "/calendar", "roles": ["admin", "doktor", "sekreter"]},
            
            # Sadece Doktor ve Admin (Asistan Göremez)
            {"id": "card_fin", "t": "Finans", "i": ft.Icons.ATTACH_MONEY, "c": "green", "r": "/finance", "roles": ["admin", "doktor"]}, # İsteğe göre doktor da gizlenebilir
            {"id": "card_crm", "t": "CRM", "i": ft.Icons.PIE_CHART, "c": "red", "r": "/crm", "roles": ["admin", "sekreter"]}, # Doktor göremez demiştiniz
            {"id": "card_stk", "t": "Stok", "i": ft.Icons.INVENTORY, "c": "orange", "r": "/inventory", "roles": ["admin", "sekreter"]}, # Doktor göremez

            # Sohbet & Ayarlar (Herkes)
            {"id": "card_chat", "t": "Sohbet", "i": ft.Icons.CHAT, "c": "pink", "r": "/chat", "roles": ["admin", "doktor", "sekreter"]},
            {"id": "card_set", "t": "Ayarlar", "i": ft.Icons.SETTINGS, "c": "grey", "r": "/settings", "roles": ["admin", "doktor", "sekreter"]},
        ]

        # Doktor Yetkileri (İstek: Gelir/Gider, Stok, CRM, Ayarlar'daki User Kalksın)
        # Yukarıdaki listede rolleri filtreleyelim:
        
        my_widgets = []
        for c in cards_config:
            if self.user_role in c["roles"]:
                # Doktor Kısıtlaması (CRM, STOK yok)
                if self.user_role == "doktor" and c["id"] in ["card_crm", "card_stk"]:
                    continue
                
                my_widgets.append(self.create_card(c))

        menu_area = ft.Row(my_widgets, wrap=True, spacing=20, alignment=ft.MainAxisAlignment.CENTER)

        return ft.View(
            "/doctor_home",
            [ft.Column([header, ft.Container(height=20), menu_area], scroll=ft.ScrollMode.AUTO)],
            bgcolor=self.bg_color, padding=0
        )

    def create_card(self, data):
        return ft.Container(
            content=ft.Column([
                ft.Icon(data["i"], size=40, color="white"),
                ft.Text(data["t"], weight="bold", color="white")
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=150, height=150, bgcolor=data["c"], border_radius=20,
            on_click=lambda _: self.page.go(data["r"]), ink=True,
            shadow=ft.BoxShadow(blur_radius=10, color="grey")
        )
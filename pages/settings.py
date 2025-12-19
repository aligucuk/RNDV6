import flet as ft

class SettingsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.current_user_id = page.session.get("user_id")

        # 1. Kullanıcı Listesi için ListView
        self.users_list_view = ft.ListView(expand=True, spacing=10, height=300)
        
        # 2. Bildirim Ayarları için Scroll Column
        self.notification_config_ui = ft.Column(scroll=ft.ScrollMode.AUTO)

    def view(self):
        # --- TEMA & RENK AYARLARI ---
        current_mode = self.db.get_setting("theme_mode") or "light"
        current_color = self.db.get_setting("theme_color") or "teal"
        
        is_dark = (current_mode == "dark")
        bg_color = "#1f2630" if is_dark else "white"
        text_color = "white" if is_dark else "teal"
        main_bg = "black" if is_dark else "#f5f7f8"

        # ============================================================
        # SEKME 1: GENEL AYARLAR (GÖRÜNÜM & MODÜLLER)
        # ============================================================
        self.dd_theme_mode = ft.Dropdown(
            label="Tema Modu", width=200, value=current_mode,
            options=[ft.dropdown.Option("light", "Aydınlık"), ft.dropdown.Option("dark", "Karanlık")],
            on_change=self.change_theme_mode, border_radius=10
        )

        colors = [("Teal", "teal"), ("Mavi", "blue"), ("Mor", "purple"), ("Turuncu", "orange"), ("Kırmızı", "red"), ("Yeşil", "green")]
        color_controls = [
            ft.Container(
                content=ft.Column([
                    ft.Container(width=40, height=40, bgcolor=code, border_radius=50, border=ft.border.all(2, "white")),
                    ft.Text(name, size=12, color=text_color)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                on_click=lambda _, c=code: self.change_color_theme(c), padding=5, border_radius=10, ink=True
            ) for name, code in colors
        ]

        tab_general = ft.Container(
            content=ft.Column([
                ft.Text("Görünüm Ayarları", size=20, weight="bold", color=current_color),
                ft.Divider(),
                ft.Row([ft.Icon(ft.Icons.BRIGHTNESS_6), self.dd_theme_mode]),
                ft.Container(height=10),
                ft.Text("Ana Renk Teması:", weight="bold", color=text_color),
                ft.Row(color_controls, wrap=True, spacing=10),
                ft.Divider(),
                ft.ElevatedButton("Fabrika Ayarlarına Dön (Verileri Sil)", bgcolor="red", color="white", on_click=self.reset_data)
            ]),
            padding=20, bgcolor=bg_color, border_radius=10
        )

        # ============================================================
        # SEKME 2: KULLANICI & PERSONEL YÖNETİMİ
        # ============================================================
        # Form Elemanları
        self.txt_u_user = ft.TextField(label="Kullanıcı Adı", expand=1, border_radius=10)
        self.txt_u_pass = ft.TextField(label="Şifre", password=True, can_reveal_password=True, expand=1, border_radius=10)
        row1 = ft.Row([self.txt_u_user, self.txt_u_pass], spacing=10)

        self.txt_u_name = ft.TextField(label="Ad Soyad", expand=2, border_radius=10)
        self.dd_u_role = ft.Dropdown(
            label="Rol", expand=1, border_radius=10,
            options=[ft.dropdown.Option("doktor"), ft.dropdown.Option("sekreter"), ft.dropdown.Option("admin")]
        )
        row2 = ft.Row([self.txt_u_name, self.dd_u_role], spacing=10)

        # Hakediş (Bug düzeltilmiş hali: Number Keyboard + Kod filtresiz)
        self.txt_u_comm = ft.TextField(
            label="Hakediş Oranı (%)", value="0", width=150, border_radius=10, 
            keyboard_type=ft.KeyboardType.NUMBER, hint_text="Sadece sayı"
        )
        btn_save_user = ft.ElevatedButton("Kullanıcıyı Kaydet", icon=ft.Icons.PERSON_ADD, bgcolor="green", color="white", on_click=self.add_new_user, height=50)
        row3 = ft.Row([self.txt_u_comm, btn_save_user], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Kullanıcı Ekleme Formu
        add_user_form = ft.Container(
            content=ft.Column([
                ft.Text("Yeni Personel Ekle", size=16, weight="bold", color=current_color),
                row1, row2, row3,
                ft.Text("* Hakediş oranı sadece doktorlar için geçerlidir.", size=12, color="grey")
            ], spacing=15),
            padding=20, border=ft.border.all(1, "grey"), border_radius=10
        )

        # Listeyi yükle
        self.load_users_list()

        # tab_users değişkeni BURADA tanımlanmalı
        tab_users = ft.Container(
            content=ft.Column([
                add_user_form,
                ft.Divider(),
                ft.Text("Kayıtlı Kullanıcılar", size=16, weight="bold", color=text_color),
                ft.Container(content=self.users_list_view, height=300, border=ft.border.all(1, "#eeeeee"), border_radius=10, padding=10)
            ]),
            padding=20, bgcolor=bg_color, border_radius=10
        )

        # ============================================================
        # SEKME 3: BİLDİRİM MERKEZİ (YENİ ÖZELLİK)
        # ============================================================
        self.load_notification_settings() # Ayarları DB'den çek

        tab_notifications = ft.Container(
            content=self.notification_config_ui,
            padding=20, bgcolor=bg_color, border_radius=10
        )

        # ============================================================
        # ANA SAYFA YAPISI (TABS)
        # ============================================================
        tabs = ft.Tabs(
            selected_index=0, animation_duration=300,
            tabs=[
                ft.Tab(text="Genel Ayarlar", icon=ft.Icons.SETTINGS, content=tab_general),
                ft.Tab(text="Kullanıcı & Personel", icon=ft.Icons.PEOPLE, content=tab_users),
                ft.Tab(text="Bildirim Merkezi", icon=ft.Icons.NOTIFICATIONS, content=tab_notifications),
            ],
            expand=True
        )

        return ft.View(
            "/settings",
            [
                ft.AppBar(title=ft.Text("Sistem Ayarları"), bgcolor=current_color, leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/doctor_home"))),
                ft.Container(content=tabs, padding=10, expand=True)
            ], bgcolor=main_bg
        )

    # ----------------------------------------------------------------
    # FONKSİYONLAR: TEMA
    # ----------------------------------------------------------------
    def change_theme_mode(self, e):
        mode = self.dd_theme_mode.value
        self.db.set_setting("theme_mode", mode)
        self.page.theme_mode = ft.ThemeMode.DARK if mode == "dark" else ft.ThemeMode.LIGHT
        self.page.update(); self.page.go("/settings")

    def change_color_theme(self, color_code):
        self.db.set_setting("theme_color", color_code)
        self.page.theme = ft.Theme(color_scheme_seed=color_code)
        self.page.update(); self.page.go("/settings")

    def reset_data(self, e):
        self.db.factory_reset(); self.page.go("/"); self.page.open(ft.SnackBar(ft.Text("Sistem sıfırlandı."), bgcolor="red"))

    # ----------------------------------------------------------------
    # FONKSİYONLAR: KULLANICI YÖNETİMİ
    # ----------------------------------------------------------------
    def load_users_list(self):
        self.users_list_view.controls.clear()
        users = self.db.get_all_users()
        if not users: self.users_list_view.controls.append(ft.Text("Kullanıcı bulunamadı.", color="red"))
        
        for u in users:
            is_me = (u[0] == self.current_user_id)
            self.users_list_view.controls.append(
                ft.ListTile(
                    leading=ft.CircleAvatar(content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS if u[3]=="admin" else ft.Icons.PERSON), bgcolor="orange" if u[3]=="admin" else "blue"),
                    title=ft.Text(f"{u[2]} ({u[1]})", weight="bold"),
                    subtitle=ft.Text(f"Rol: {u[3].upper()} | Hakediş: %{u[4]}"),
                    trailing=ft.IconButton(ft.Icons.DELETE, icon_color="red", disabled=is_me, tooltip="Kullanıcıyı Sil", on_click=lambda _, uid=u[0]: self.delete_user(uid)),
                    bgcolor="#f0f0f0",
                )
            )
        if self.users_list_view.page: self.users_list_view.update()

    def add_new_user(self, e):
        if not self.txt_u_user.value or not self.txt_u_pass.value or not self.txt_u_name.value or not self.dd_u_role.value:
            self.page.open(ft.SnackBar(ft.Text("Lütfen tüm alanları doldurun."), bgcolor="red")); return
        try: comm = int(self.txt_u_comm.value)
        except ValueError: self.page.open(ft.SnackBar(ft.Text("Hakediş oranı sayı olmalıdır!"), bgcolor="red")); return

        if self.db.add_user(self.txt_u_user.value, self.txt_u_pass.value, self.txt_u_name.value, self.dd_u_role.value, comm):
            self.page.open(ft.SnackBar(ft.Text(f"{self.txt_u_name.value} eklendi."), bgcolor="green"))
            self.txt_u_user.value = ""; self.txt_u_pass.value = ""; self.txt_u_name.value = ""; self.txt_u_comm.value = "0"
            self.page.update(); self.load_users_list()
        else: self.page.open(ft.SnackBar(ft.Text("Kullanıcı adı kullanımda!"), bgcolor="red"))

    def delete_user(self, uid):
        self.db.delete_user(uid)
        self.page.open(ft.SnackBar(ft.Text("Kullanıcı silindi."), bgcolor="orange"))
        self.load_users_list()

    # ----------------------------------------------------------------
    # FONKSİYONLAR: BİLDİRİM MERKEZİ
    # ----------------------------------------------------------------
    def load_notification_settings(self):
        self.notification_config_ui.controls.clear()
        try: settings = self.db.get_notification_settings()
        except: settings = [] 

        if not settings:
            self.notification_config_ui.controls.append(ft.Text("Bildirim veritabanı henüz oluşmadı. Lütfen programı yeniden başlatın.", color="red"))
            return

        for s in settings:
            channel, key, secret, sender, active, template = s
            
            var_row = ft.Row([
                ft.OutlinedButton("{hasta}", on_click=lambda e: self.page.open(ft.SnackBar(ft.Text("Değişken: {hasta}"), bgcolor="blue"))),
                ft.OutlinedButton("{tarih}", on_click=lambda e: self.page.open(ft.SnackBar(ft.Text("Değişken: {tarih}"), bgcolor="blue"))),
                ft.OutlinedButton("{saat}", on_click=lambda e: self.page.open(ft.SnackBar(ft.Text("Değişken: {saat}"), bgcolor="blue"))),
            ], scroll=ft.ScrollMode.HIDDEN)

            # Değerleri saklamak için Textfield referanslarını tutmuyoruz, basitleştirilmiş UI:
            # Not: Gerçek kaydetme işlemi için TextField'ların value'sunu okumak gerekir.
            # Şimdilik UI gösterimi ve simülasyon kayıt butonu:
            
            tf_key = ft.TextField(label="API Key", value=key, password=True, can_reveal_password=True)
            tf_sec = ft.TextField(label="API Secret", value=secret, password=True, can_reveal_password=True)
            tf_snd = ft.TextField(label="Sender ID", value=sender)
            tf_sw = ft.Switch(label="Aktif", value=active)
            tf_tpl = ft.TextField(label="Şablon", value=template, multiline=True)

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SMS if channel=="sms" else (ft.Icons.EMAIL if channel=="email" else ft.Icons.MESSAGE), color="teal"),
                        ft.Text(channel.upper(), weight="bold", size=16),
                        tf_sw
                    ]),
                    ft.Divider(),
                    tf_key, tf_sec, tf_snd,
                    ft.Text("Mesaj Şablonu:", weight="bold", size=12),
                    var_row,
                    tf_tpl,
                    ft.ElevatedButton("Kaydet", bgcolor="teal", color="white", 
                                      on_click=lambda _, c=channel, k=tf_key, sc=tf_sec, sn=tf_snd, a=tf_sw, t=tf_tpl: self.save_notif(c, k.value, sc.value, sn.value, a.value, t.value))
                ]),
                padding=15, border=ft.border.all(1, "grey"), border_radius=10, margin=5, bgcolor="white"
            )
            self.notification_config_ui.controls.append(card)

    def save_notif(self, channel, key, secret, sender, active, template):
        self.db.update_notification_setting(channel, key, secret, sender, active, template)
        self.page.open(ft.SnackBar(ft.Text(f"{channel.upper()} ayarları güncellendi."), bgcolor="green"))
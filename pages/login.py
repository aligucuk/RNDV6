import flet as ft

class LoginPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db

    def view(self):
        # Alanlar
        self.user = ft.TextField(label="Kullanıcı Adı", icon=ft.Icons.PERSON, border_radius=10)
        self.passwd = ft.TextField(label="Şifre", password=True, can_reveal_password=True, icon=ft.Icons.LOCK, border_radius=10)
        
        # TV Modu Butonu
        btn_tv = ft.TextButton("📺 Bekleme Ekranını Aç (TV Modu)", on_click=lambda _: self.page.go("/tv"))

        # --- GÜZEL ARAYÜZ TASARIMI ---
        card_content = ft.Column([
            ft.Icon(ft.Icons.LOCAL_HOSPITAL, size=80, color="teal"),
            ft.Text("RNDV6 Klinik", size=30, weight="bold", color="teal"),
            ft.Text("Giriş Yap", size=20, color="#546e7a"),
            ft.Container(height=20),
            self.user,
            self.passwd,
            ft.Container(height=20),
            ft.ElevatedButton("Giriş", on_click=self.login_click, bgcolor="teal", color="white", width=200, height=50),
            ft.Container(height=10),
            ft.Text("Varsayılan: admin / admin123\ndoktor1 / 1234", size=10, color="grey"),
            ft.Divider(),
            btn_tv
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        login_card = ft.Container(
            content=card_content,
            width=400,
            padding=40,
            bgcolor="white",
            border_radius=20,
            # HATA ÇÖZÜMÜ BURADA: color="grey" (Opacity yerine düz renk veya hex)
            shadow=ft.BoxShadow(blur_radius=20, color="grey")
        )

        return ft.View(
            "/login",
            [
                ft.Container(
                    content=login_card,
                    alignment=ft.alignment.center,
                    expand=True,
                    bgcolor="#e0f2f1" # Arka plan rengi
                )
            ],
            padding=0
        )

    def login_click(self, e):
        if not self.user.value or not self.passwd.value:
            self.page.open(ft.SnackBar(ft.Text("Alanları doldurun"), bgcolor="red"))
            return

        res = self.db.check_login(self.user.value, self.passwd.value)
        if res:
            self.page.session.set("user_id", res[0])
            self.page.session.set("user_name", res[2])
            self.page.session.set("user_role", res[3])
            
            try: self.db.log_action(self.user.value, "Giriş", "Başarılı giriş yapıldı.")
            except: pass
            
            self.page.open(ft.SnackBar(ft.Text(f"Hoşgeldin {res[2]}"), bgcolor="green"))
            self.page.go("/doctor_home")
        else:
            self.page.open(ft.SnackBar(ft.Text("Hatalı Giriş!"), bgcolor="red"))
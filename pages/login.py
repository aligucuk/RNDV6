import flet as ft

class LoginPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db

    def view(self):
        self.user_input = ft.TextField(label="Kullanıcı Adı", width=300, autofocus=True)
        self.pass_input = ft.TextField(label="Şifre", password=True, can_reveal_password=True, width=300)

        return ft.View(
            "/login",
            [
                ft.Container(
                    content=ft.Column([
                        ft.Icon("local_hospital", size=80, color="teal"),
                        ft.Text("RNDV5 Klinik Sistemi", size=30, weight="bold", color="teal"),
                        ft.Text("Güvenli Giriş Ekranı", color="grey"),
                        ft.Container(height=20),
                        self.user_input,
                        self.pass_input,
                        ft.ElevatedButton("GİRİŞ YAP", on_click=self.login_click, width=300, bgcolor="teal", color="white"),
                        ft.Container(height=20),
                        ft.Divider(),
                        ft.TextButton("Bekleme Ekranı (TV) Olarak Başlat", icon="tv", on_click=lambda _: self.page.go("/waiting_room"))
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=50, bgcolor="white", border_radius=20, shadow=ft.BoxShadow(blur_radius=20, color="grey")
                )
            ],
            bgcolor="teal",
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def login_click(self, e):
        user = self.db.check_login(self.user_input.value, self.pass_input.value)
        if user:
            # Session'a kaydet
            self.page.session.set("user_id", user[0])
            self.page.session.set("user_name", user[1])
            self.page.session.set("full_name", user[2])
            self.page.session.set("user_role", user[3])
            
            # Logla
            self.db.log_action(user[1], "Giriş", "Başarılı giriş yapıldı.")
            
            # Yönlendir
            if user[3] == "doktor":
                self.page.go("/doctor_home")
            else:
                self.page.go("/dashboard")
        else:
            self.page.open(ft.SnackBar(ft.Text("Hatalı Kullanıcı Adı veya Şifre!"), bgcolor="red"))
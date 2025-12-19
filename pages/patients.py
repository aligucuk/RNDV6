import flet as ft

class PatientsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.patients_grid = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=10)
        self.date_picker = ft.DatePicker(on_change=self.on_date_change)
        self.page.overlay.append(self.date_picker)

    def view(self):
        # UI Elemanları
        self.tc_input = ft.TextField(label="TC Kimlik No", max_length=11, input_filter=ft.NumbersOnlyInputFilter(), border_radius=10, width=200)
        self.name_input = ft.TextField(label="Ad Soyad", border_radius=10, width=200)
        self.phone_input = ft.TextField(label="Telefon", border_radius=10, width=200, input_filter=ft.NumbersOnlyInputFilter())
        
        # --- YENİ E-MAIL KUTUSU ---
        self.email_input = ft.TextField(label="E-Posta", border_radius=10, width=200, icon=ft.Icons.EMAIL)
        
        self.dd_gender = ft.Dropdown(label="Cinsiyet", width=120, options=[ft.dropdown.Option("Erkek"), ft.dropdown.Option("Kadın")], border_radius=10)
        self.dd_source = ft.Dropdown(label="Referans Kaynağı", width=200, options=[ft.dropdown.Option("Google"), ft.dropdown.Option("Sosyal Medya"), ft.dropdown.Option("Tavsiye"), ft.dropdown.Option("Bilinmiyor")], border_radius=10)
        self.btn_date = ft.ElevatedButton("Doğum Tarihi", icon="calendar_today", on_click=self.open_date_picker)
        self.selected_bdate = None

        form_container = ft.Container(
            content=ft.Column([
                ft.Text("Yeni Hasta Kaydı", size=18, weight="bold", color="teal"),
                ft.Row([self.tc_input, self.name_input, self.phone_input], wrap=True),
                # Email'i buraya ekledik
                ft.Row([self.email_input, self.dd_gender, self.dd_source], wrap=True),
                ft.Row([self.btn_date], wrap=True),
                ft.ElevatedButton("Kaydet", icon="save", bgcolor="teal", color="white", on_click=self.add_patient)
            ], spacing=15),
            padding=20, bgcolor="white", border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color="grey")
        )

        self.txt_search = ft.TextField(label="Hasta Ara...", prefix_icon="search", on_change=self.search_patient)
        self.load_patients()

        return ft.View(
            "/patient_list",
            [
                ft.AppBar(title=ft.Text("Hasta Yönetimi"), bgcolor="teal", leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/doctor_home"))),
                ft.Container(
                    content=ft.Column([form_container, ft.Divider(), self.txt_search, ft.Container(content=self.patients_grid, expand=True)]),
                    padding=20, expand=True
                )
            ], bgcolor="#f5f7f8"
        )

    def open_date_picker(self, e): self.date_picker.open = True; self.date_picker.update()
    def on_date_change(self, e): self.selected_bdate = self.date_picker.value; self.btn_date.text = self.selected_bdate.strftime("%d.%m.%Y"); self.btn_date.update()

    def add_patient(self, e):
        if not self.tc_input.value or len(self.tc_input.value) != 11:
            self.page.open(ft.SnackBar(ft.Text("TC Kimlik 11 hane olmalıdır!"), bgcolor="red")); return
        if not self.name_input.value:
            self.page.open(ft.SnackBar(ft.Text("İsim zorunludur!"), bgcolor="red")); return
        
        bdate = self.selected_bdate if self.selected_bdate else "2000-01-01"
        
        # --- GÜNCELLENMİŞ KAYIT FONKSİYONU ---
        if self.db.add_patient(
            self.tc_input.value, 
            self.name_input.value, 
            self.phone_input.value, 
            self.dd_gender.value, 
            bdate, 
            self.dd_source.value,
            self.email_input.value # E-Mail Eklendi
        ):
            self.page.open(ft.SnackBar(ft.Text("Hasta Eklendi"), bgcolor="green"))
            # Alanları temizle
            self.tc_input.value = ""; self.name_input.value = ""; self.phone_input.value = ""; self.email_input.value = ""
            self.page.update(); self.load_patients()
        else:
            self.page.open(ft.SnackBar(ft.Text("Hata: TC Kimlik kayıtlı."), bgcolor="red"))

    def load_patients(self):
        self.patients_grid.controls.clear()
        patients = self.db.get_all_patients()
        
        for p in patients:
            # p verisi: (id, tc, name, phone, gender, bdate, created, source, status, email)
            # p[0]=id, p[2]=isim, p[1]=tc
            
            # Asistan (Sekreter) Kontrolü
            trailing_button = None
            
            # Eğer kullanıcı 'sekreter' DEĞİLSE (Doktor veya Admin ise) butonu göster
            if self.user_role != "sekreter":
                trailing_button = ft.IconButton(
                    "folder_open", 
                    icon_color="blue", 
                    on_click=lambda _, pid=p[0]: self.page.go(f"/medical/{pid}")
                )
            else:
                # Sekreter ise boş bir ikon koyalım (görünmez) ya da None bırakalım
                trailing_button = ft.Container(width=0)

            card = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.PERSON, color="teal"),
                    ft.Column([
                        ft.Text(p[2], weight="bold"), 
                        ft.Text(f"TC: {p[1]}", size=12, color="grey")
                    ]),
                    trailing_button # Yetkiye göre oluşturduğumuz buton
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=10, bgcolor="white", border_radius=10, border=ft.border.all(1, "#eeeeee")
            )
            self.patients_grid.controls.append(card)
            
        if self.patients_grid.page: self.patients_grid.update()

    def search_patient(self, e):
        term = e.control.value
        if len(term) < 2: return self.load_patients()
        self.patients_grid.controls.clear()
        for p in self.db.search_patients(term):
            card = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.PERSON, color="teal"),
                    ft.Column([ft.Text(p[2], weight="bold"), ft.Text(f"TC: {p[1]}", size=12, color="grey")]),
                    ft.IconButton("folder_open", icon_color="blue", on_click=lambda _, pid=p[0]: self.page.go(f"/medical/{pid}"))
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=10, bgcolor="white", border_radius=10
            )
            self.patients_grid.controls.append(card)
        if self.patients_grid.page: self.patients_grid.update()
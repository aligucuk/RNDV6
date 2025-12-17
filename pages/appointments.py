import flet as ft
import datetime

class AppointmentsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.doctor_id = page.session.get("user_id")
        
        # --- SEÇİCİLER (Pop-up) ---
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change, confirm_text="Seç", cancel_text="İptal"
        )
        self.time_picker = ft.TimePicker(
            on_change=self.on_time_change, confirm_text="Seç", cancel_text="İptal"
        )
        # Overlay'e ekle (Eğer daha önce eklenmediyse)
        if self.date_picker not in page.overlay: page.overlay.append(self.date_picker)
        if self.time_picker not in page.overlay: page.overlay.append(self.time_picker)

        # Değişkenler
        self.selected_patient_id = None
        self.selected_date = datetime.date.today()
        self.selected_time = None

    # --- OLAYLAR (Events) ---
    def on_date_change(self, e):
        self.btn_date.text = self.date_picker.value.strftime("%d.%m.%Y")
        self.btn_date.icon = "check_circle"
        self.btn_date.update()

    def on_time_change(self, e):
        self.selected_time = self.time_picker.value
        self.btn_time.text = self.selected_time.strftime("%H:%M")
        self.btn_time.icon = "check_circle"
        self.btn_time.update()

    def search_patient(self, e):
        term = e.control.value
        self.results_col.controls.clear()
        if len(term) > 1:
            patients = self.db.search_patients(term)
            if patients:
                for p in patients:
                    self.results_col.controls.append(
                        ft.ListTile(
                            leading=ft.Icon("person", color="teal"),
                            title=ft.Text(p[2], weight="bold"),
                            subtitle=ft.Text(f"TC: {p[1]}"),
                            on_click=lambda _, pid=p[0], pname=p[2]: self.select_patient(pid, pname),
                            bgcolor="white", border_radius=8
                        )
                    )
            else:
                self.results_col.controls.append(ft.Text("Bulunamadı.", color="grey"))
        self.results_col.update()

    def select_patient(self, pid, pname):
        self.selected_patient_id = pid
        self.lbl_patient.value = pname
        self.card_patient.bgcolor = "#e0f2f1"
        self.card_patient.border = ft.border.all(2, "teal")
        self.card_patient.update()

    def save_appointment(self, e):
        if not self.selected_patient_id or not self.selected_time:
            self.page.open(ft.SnackBar(ft.Text("Hasta ve Saat seçilmeli!"), bgcolor="red"))
            return
            
        dt_str = f"{self.date_picker.value.strftime('%Y-%m-%d')} {self.selected_time.strftime('%H:%M:00')}"
        
        if self.db.add_appointment(self.selected_patient_id, self.doctor_id, dt_str, "Bekliyor", self.txt_note.value):
            self.page.open(ft.SnackBar(ft.Text("Randevu Oluşturuldu!"), bgcolor="green"))
            # Formu sıfırla ve listeye dön
            self.tabs.selected_index = 0 
            self.refresh_list()
            self.tabs.update()
        else:
            self.page.open(ft.SnackBar(ft.Text("Hata oluştu!"), bgcolor="red"))

    # --- ARAYÜZ OLUŞTURMA ---
    def view(self):
        # 1. SEKME: RANDEVU LİSTESİ
        self.list_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.refresh_list() # Listeyi doldur

        tab_list = ft.Container(
            content=self.list_column,
            padding=20,
            bgcolor="#f5f7f8"
        )

        # 2. SEKME: YENİ RANDEVU (Modern Tasarım)
        # Sol Panel (Arama)
        self.txt_search = ft.TextField(hint_text="Hasta Ara...", prefix_icon="search", bgcolor="white", border_radius=10, on_change=self.search_patient)
        self.results_col = ft.Column(scroll=ft.ScrollMode.AUTO)
        
        panel_search = ft.Container(
            content=ft.Column([
                ft.Text("1. Hasta Seçimi", weight="bold", color="teal"), 
                self.txt_search, 
                ft.Divider(), 
                self.results_col
            ], expand=True),
            expand=4, padding=15, bgcolor="#f5f7f8", border_radius=10
        )

        # Sağ Panel (Form)
        self.lbl_patient = ft.Text("Seçilmedi", weight="bold")
        self.card_patient = ft.Container(content=ft.Row([ft.Icon("person"), self.lbl_patient]), padding=15, bgcolor="white", border_radius=10, border=ft.border.all(1, "grey"))
        
        self.btn_date = ft.ElevatedButton("Tarih", icon="calendar_today", on_click=lambda _: self.date_picker.pick_date(), bgcolor="white", color="teal")
        self.btn_time = ft.ElevatedButton("Saat", icon="schedule", on_click=lambda _: self.time_picker.pick_time(), bgcolor="white", color="teal")
        self.txt_note = ft.TextField(label="Not", multiline=True, bgcolor="white")
        btn_save = ft.ElevatedButton("Randevuyu Kaydet", icon="save", bgcolor="teal", color="white", height=50, on_click=self.save_appointment)

        panel_form = ft.Container(
            content=ft.Column([
                ft.Text("2. Detaylar", weight="bold", color="teal"),
                self.card_patient,
                ft.Row([ft.Expanded(self.btn_date), ft.Expanded(self.btn_time)]),
                self.txt_note,
                ft.Container(expand=True),
                ft.Row([btn_save], alignment=ft.MainAxisAlignment.END)
            ], expand=True),
            expand=6, padding=20, bgcolor="white", border_radius=10
        )

        tab_create = ft.Container(
            content=ft.Row([panel_search, ft.VerticalDivider(), panel_form], expand=True),
            padding=10, bgcolor="white", border_radius=15
        )

        # TABS (Sekmeler)
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Randevu Listesi", icon="list_alt", content=tab_list),
                ft.Tab(text="Yeni Randevu", icon="add_circle", content=tab_create),
            ],
            expand=True
        )

        return ft.View(
            "/appointments",
            [
                ft.AppBar(title=ft.Text("Randevu Yönetimi"), bgcolor="teal", leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/doctor_home"))),
                self.tabs
            ],
            bgcolor="#e0f2f1"
        )

    def refresh_list(self):
        self.list_column.controls.clear()
        # DB'den randevuları çek (Senin DB sınıfına göre uyarla: id, patient_name, date, status)
        apps = self.db.get_appointments_by_doctor(self.doctor_id) 
        
        if not apps:
            self.list_column.controls.append(ft.Text("Görüntülenecek randevu yok.", italic=True, color="grey"))
        else:
            for app in apps:
                # app yapısı: (id, hasta_adi, tarih, durum, not) varsayıyoruz
                # Tarihi datetime objesiyse formatla, string ise parse et
                date_display = str(app[2]) 
                
                card = ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(date_display, size=16, weight="bold", color="teal"),
                                ft.Text(app[1], size=18, weight="bold"), # Hasta Adı
                            ]), expand=True
                        ),
                        ft.Container(
                            content=ft.Text(app[3], color="white", weight="bold"),
                            bgcolor="green" if app[3]=="Onaylandı" else "orange",
                            padding=10, border_radius=5
                        )
                    ]),
                    padding=20, bgcolor="white", border_radius=10,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black"))
                )
                self.list_column.controls.append(card)
        self.list_column.update()
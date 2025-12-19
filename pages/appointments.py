import flet as ft
import datetime

class AppointmentsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.doctor_id = page.session.get("user_id")
        self.selected_patient_id = None
        self.selected_date = None
        self.selected_time = None
        
        # Seçiciler ve Overlay
        self.date_picker = ft.DatePicker(on_change=self.on_date_change)
        self.time_picker = ft.TimePicker(on_change=self.on_time_change)
        self.page.overlay.extend([self.date_picker, self.time_picker])

    def view(self):
        self.txt_search = ft.TextField(label="Hasta Ara (İsim/TC)", on_change=self.search_patient_live)
        self.search_results = ft.ListView(height=150, spacing=5)
        
        # HATA DÜZELTME: Fonksiyonlara yönlendirildi
        self.btn_date = ft.ElevatedButton("Tarih Seç", icon="calendar_month", on_click=self.open_date_picker)
        self.btn_time = ft.ElevatedButton("Saat Seç", icon="access_time", on_click=self.open_time_picker)
        self.txt_note = ft.TextField(label="Randevu Notu", multiline=True)
        
        tab_new = ft.Container(
            content=ft.Column([
                ft.Text("Yeni Randevu Oluştur", size=20, weight="bold"),
                self.txt_search, self.search_results, ft.Divider(),
                ft.Row([self.btn_date, self.btn_time]), self.txt_note,
                ft.ElevatedButton("Randevuyu Kaydet", bgcolor="teal", color="white", on_click=self.save_appointment)
            ]), padding=20
        )

        self.list_col = ft.Column(scroll=ft.ScrollMode.AUTO)
        self.load_appointments()
        
        # Varsayılan sekme 1 (Liste)
        self.tabs = ft.Tabs(
            selected_index=1,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Yeni Randevu", icon="add", content=tab_new),
                ft.Tab(text="Randevularım", icon="list", content=ft.Container(content=self.list_col, padding=20)),
            ], expand=True
        )

        return ft.View(
            "/appointments",
            [
                ft.AppBar(title=ft.Text("Randevu Yönetimi"), bgcolor="teal", leading=ft.IconButton("arrow_back", on_click=self.smart_back)),
                self.tabs
            ]
        )

    # YENİ EKLENEN FONKSİYONLAR (Hata Çözümü İçin)
    def open_date_picker(self, e):
        self.date_picker.open = True
        self.date_picker.update()

    def open_time_picker(self, e):
        self.time_picker.open = True
        self.time_picker.update()

    def smart_back(self, e):
        if self.tabs.selected_index == 0:
            self.tabs.selected_index = 1
            self.tabs.update()
        else:
            self.page.go("/doctor_home")

    def on_date_change(self, e):
        if self.date_picker.value:
            self.selected_date = self.date_picker.value
            self.btn_date.text = self.selected_date.strftime("%d.%m.%Y")
            self.btn_date.icon = "check_circle"
            self.btn_date.update()

    def on_time_change(self, e):
        if self.time_picker.value:
            self.selected_time = self.time_picker.value
            self.btn_time.text = self.selected_time.strftime("%H:%M")
            self.btn_time.icon = "check_circle"
            self.btn_time.update()

    def search_patient_live(self, e):
        term = e.control.value
        self.search_results.controls.clear()
        if len(term) < 2: 
            if self.search_results.page: self.search_results.update()
            return
        
        for p in self.db.search_patients(term):
            self.search_results.controls.append(ft.ListTile(title=ft.Text(p[2]), subtitle=ft.Text(p[1]), leading=ft.Icon("person"), on_click=lambda _, pid=p[0], nm=p[2]: self.select_patient(pid, nm), bgcolor="white"))
        if self.search_results.page: self.search_results.update()

    def select_patient(self, pid, name):
        self.selected_patient_id = pid
        self.txt_search.value = f"Seçilen: {name}"
        self.search_results.controls.clear()
        self.page.update()

    def save_appointment(self, e):
        if not self.selected_patient_id or not self.selected_date or not self.selected_time:
            self.page.open(ft.SnackBar(ft.Text("Lütfen tüm alanları seçin"), bgcolor="red")); return
        
        dt = datetime.datetime.combine(self.selected_date, self.selected_time)
        self.db.add_appointment(self.selected_patient_id, self.doctor_id, dt, self.txt_note.value)
        self.page.open(ft.SnackBar(ft.Text("Randevu oluşturuldu"), bgcolor="green"))
        
        self.txt_note.value = ""
        self.txt_search.value = ""
        self.selected_patient_id = None
        self.page.update()
        self.load_appointments()
        self.tabs.selected_index = 1
        self.tabs.update()

    def load_appointments(self):
        self.list_col.controls.clear()
        apps = self.db.get_appointments_by_doctor(self.doctor_id)
        if not apps: self.list_col.controls.append(ft.Text("Randevu bulunamadı."))
        else:
            for a in apps:
                c = ft.Container(
                    content=ft.Row([
                        ft.Column([ft.Text(a[2].strftime("%d.%m.%Y %H:%M"), weight="bold"), ft.Text(a[1])]),
                        ft.Container(content=ft.Text(a[3], color="white", size=12), bgcolor="green" if a[3]=="Tamamlandı" else "orange", padding=5, border_radius=5)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10, bgcolor="white", border_radius=10, border=ft.border.all(1, "grey")
                )
                self.list_col.controls.append(c)
        if self.list_col.page: self.list_col.update()
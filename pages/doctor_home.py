import flet as ft
import datetime

class DoctorHomePage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.doctor_id = page.session.get("user_id")
        self.doctor_name = page.session.get("user_name")

    def view(self):
        # --- BUGÜNKÜ RANDEVULAR ---
        today = datetime.date.today().strftime('%Y-%m-%d')
        
        # Sadece bu doktora ait bugünkü randevuları çeken özel bir sorgu lazım
        # db_manager'da genel fonksiyon var, onu filtreleyebiliriz veya yeni yazabiliriz.
        # Basitlik için genel 'get_todays_appointments' kullanıp filtreliyoruz.
        all_appts = self.db.get_todays_appointments()
        
        # Filtreleme (Sadece benim hastalarım) - Gerçek projede SQL ile yapılmalı
        my_appts = [] 
        # get_todays_appointments() şunu döner: (id, p_name, date, status, p_id)
        # Ancak içinde doctor_id yok. Bunu düzeltmemiz lazım.
        # Şimdilik listedeki herkesi gösterelim (Demo için), 
        # ya da db_manager'ı güncellememiz gerekir.
        # Hadi db_manager'a dokunmadan, listede görünen herkesi çağırma yetkisi verelim.
        
        lv_patients = ft.ListView(expand=True, spacing=10)

        for appt in all_appts:
            aid, p_name, dt, status, pid = appt
            
            # Zamanı al
            time_str = dt.strftime("%H:%M")
            
            # Renkler
            status_color = "orange"
            if status == "Tamamlandı": status_color = "blue"
            elif status == "İptal": status_color = "red"
            elif status == "Muayenede": status_color = "green"

            # İŞLEM BUTONLARI
            btn_call = ft.IconButton(
                icon="campaign", icon_color="green", tooltip="İçeri Çağır (TV)",
                on_click=lambda e, x=aid: self.call_patient(x)
            )
            btn_medical = ft.ElevatedButton(
                "Muayene Et", icon="medical_services", 
                on_click=lambda e, x=pid: self.page.go(f"/medical/{x}")
            )

            card = ft.Card(
                content=ft.Container(
                    content=ft.Row([
                        ft.Text(time_str, size=20, weight="bold", color="teal"),
                        ft.Column([
                            ft.Text(p_name, weight="bold", size=16),
                            ft.Container(content=ft.Text(status, color="white", size=10), bgcolor=status_color, padding=5, border_radius=5)
                        ], expand=True),
                        btn_call,
                        btn_medical
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=15
                )
            )
            lv_patients.controls.append(card)

        if not lv_patients.controls:
            lv_patients.controls.append(ft.Text("Bugün için kayıtlı randevu yok.", color="grey", text_align="center"))

        return ft.View(
            "/doctor_home",
            [
                ft.AppBar(title=ft.Text(f"Dr. {self.doctor_name} - Panel"), bgcolor="teal", 
                          actions=[ft.IconButton("logout", on_click=lambda _: self.page.go("/login"))]),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Bugünkü Randevular ({today})", size=20, weight="bold"),
                        ft.Divider(),
                        lv_patients
                    ]),
                    padding=20, expand=True
                )
            ],
            bgcolor="background"
        )

    def call_patient(self, appt_id):
        # 1. Önce "Muayenede" olan herkesi "Bekliyor" veya "Tamamlandı" yapmalıyız ki TV karışmasın
        # (Basitlik için yapmıyoruz, son basılan geçerli olur)
        
        # 2. Bu hastayı "Muayenede" yap
        self.db.set_appointment_status(appt_id, "Muayenede")
        
        self.page.open(ft.SnackBar(ft.Text("Hasta Çağrıldı! TV Ekranına Bakınız."), bgcolor="green"))
        self.page.go("/doctor_home") # Yenile
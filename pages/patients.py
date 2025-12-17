import flet as ft
import datetime
from utils.sms_manager import SMSManager

class PatientsPage:
    def __init__(self, page: ft.Page, db, patient_id=None):
        self.page = page
        self.db = db
        self.patient_id = patient_id
        self.sms = SMSManager(db) # SMS Yöneticisi Başlatıldı

        self.txt_tc = ft.TextField(label="TC Kimlik No", max_length=11)
        self.txt_name = ft.TextField(label="Ad Soyad")
        self.txt_phone = ft.TextField(label="Telefon (5XX...)", max_length=10, prefix_text="+90 ")
        self.dd_gender = ft.Dropdown(label="Cinsiyet", options=[ft.dropdown.Option("Kadın"), ft.dropdown.Option("Erkek")])
        self.dd_source = ft.Dropdown(label="Bizi Nereden Duydunuz?", options=[
            ft.dropdown.Option("Google"), ft.dropdown.Option("Instagram"), 
            ft.dropdown.Option("Tavsiye"), ft.dropdown.Option("Tabela"), ft.dropdown.Option("Diğer")
        ])
        self.date_picker = ft.DatePicker(on_change=self.change_date, first_date=datetime.datetime(1920,1,1), last_date=datetime.datetime.now())
        self.btn_date = ft.ElevatedButton("Doğum Tarihi Seç", icon="calendar_month", on_click=lambda _: self.page.open(self.date_picker))
        self.lbl_date = ft.Text("Seçilmedi")
        self.selected_date = None

    def change_date(self, e):
        self.selected_date = e.control.value
        self.lbl_date.value = self.selected_date.strftime("%d.%m.%Y")
        self.page.update()

    def view(self):
        # Düzenleme modu ise verileri doldur
        if self.patient_id:
            p = self.db.get_patient_by_id(self.patient_id)
            if p:
                self.txt_tc.value = p[1]
                self.txt_name.value = p[2]
                self.txt_phone.value = p[3]
                self.dd_gender.value = p[4]
                self.selected_date = p[5]
                self.lbl_date.value = self.selected_date.strftime("%d.%m.%Y") if self.selected_date else "-"
                # Referral (Kaynak) 7. indeks (id, tc, name, phone, gender, birth, created, referral)
                try: self.dd_source.value = p[7]
                except: pass

        return ft.View(
            "/patients",
            [
                ft.AppBar(title=ft.Text("Hasta Kartı"), bgcolor="teal", leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/patient_list"))),
                ft.Container(
                    content=ft.Column([
                        ft.Icon("person_add", size=40, color="teal"),
                        ft.Text("Hasta Bilgileri", size=20, weight="bold"),
                        ft.Divider(),
                        self.txt_tc,
                        self.txt_name,
                        self.txt_phone,
                        self.dd_gender,
                        self.dd_source, # YENİ ALAN
                        ft.Row([self.btn_date, self.lbl_date]),
                        ft.Container(height=20),
                        ft.ElevatedButton("KAYDET", icon="save", bgcolor="green", color="white", on_click=self.save_clicked),
                        ft.ElevatedButton("SİL", icon="delete", bgcolor="red", color="white", visible=bool(self.patient_id), on_click=self.delete_clicked)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=30
                )
            ], bgcolor="background"
        )

    def save_clicked(self, e):
        if not self.txt_tc.value or not self.txt_name.value:
            self.page.open(ft.SnackBar(ft.Text("Eksik Bilgi!"), bgcolor="red"))
            return

        try:
            if self.patient_id:
                self.db.update_patient(self.patient_id, self.txt_tc.value, self.txt_name.value, self.txt_phone.value, self.dd_gender.value, self.selected_date, self.dd_source.value)
                self.page.open(ft.SnackBar(ft.Text("Güncellendi"), bgcolor="green"))
            else:
                if self.db.add_patient(self.txt_tc.value, self.txt_name.value, self.txt_phone.value, self.dd_gender.value, self.selected_date, self.dd_source.value):
                    self.page.open(ft.SnackBar(ft.Text("Kayıt Başarılı"), bgcolor="green"))
                    
                    # --- SMS GÖNDERİMİ ---
                    if self.txt_phone.value:
                        self.sms.send_sms(self.txt_phone.value, f"Sn. {self.txt_name.value}, klinigimize hosgeldiniz. Saglikli gunler dileriz.")
                    
                    self.page.go("/patient_list")
                else:
                    self.page.open(ft.SnackBar(ft.Text("Hata! TC kayıtlı olabilir."), bgcolor="red"))
        except Exception as ex:
            print(ex)

    def delete_clicked(self, e):
        self.db.delete_patient(self.patient_id)
        self.page.go("/patient_list")